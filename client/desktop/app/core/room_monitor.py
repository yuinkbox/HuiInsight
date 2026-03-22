# -*- coding: utf-8 -*-
"""
RoomMonitor - UI Automation + 可选内存扫描（房间/用户 ID）

Author : AHDUNYI
Version: 10.4.0
"""

import re
import time
import threading
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Tuple

import psutil

try:
    import uiautomation as auto
    WINDOWS_AVAILABLE = True
except ImportError:
    auto = None
    WINDOWS_AVAILABLE = False

import logging

from client.desktop.app.core.memory_room_probe import MemoryRoomProbe

logger = logging.getLogger(__name__)


# ============================================================================
# ID Extraction Strategy
# ============================================================================


class IDExtractor(ABC):
    """Abstract interface for extracting room/user IDs."""

    @abstractmethod
    def extract(self, collected_ids: List[Tuple[int, str]]) -> Tuple[Optional[str], Optional[str]]:
        """Extract (room_id, user_id) from UI 文本（depth, control_name）。"""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset internal state (e.g., sticky room ID) when session ends."""
        pass


class DefaultIDExtractor(IDExtractor):
    """
    基于控件「完整文案」解析：

    - 房间：「女神丨ID:108830」「音乐 | ID:102382」
    - 用户：「ID: … IP属地」或含 IP属地 / 粉丝

    仅「ID:数字」且位数>=8 时优先当用户 UID；房间用 sticky，避免资料卡顶掉房间号。
    """

    ROOM_TYPES = (
        "男神",
        "女神",
        "点唱",
        "拍拍",
        "游戏",
        "个人房",
        "密码房",
        "音乐",
        "情感",
        "脱口秀",
        "靓",  # 靓号
    )
    USER_MARKERS = ("IP\u5c5e\u5730", "\u7c89\u4e1d")
    _SEP = r"[\|\｜丨/]"
    _USER_ID_LEN_HINT = 8

    def __init__(self) -> None:
        self._sticky_room_id: Optional[str] = None
        types_alt = "(?:" + "|".join(re.escape(t) for t in self.ROOM_TYPES) + ")"
        self._strong_room_re = re.compile(
            types_alt + self._SEP + r"\s*ID[:\uFF1a]\s*(\d{3,10})",
            re.IGNORECASE,
        )
        self._strong_user_re = re.compile(
            r"ID[:\uFF1a]\s*(\d{3,10})\s*IP\u5c5e\u5730",
            re.IGNORECASE,
        )
        self._weak_id_re = re.compile(r"ID[:\uFF1a]\s*(\d{3,10})", re.IGNORECASE)

    def reset(self) -> None:
        self._sticky_room_id = None
        logger.debug("DefaultIDExtractor reset")

    def extract(self, collected_ids: List[Tuple[int, str]]) -> Tuple[Optional[str], Optional[str]]:
        # 本轮未扫到任何相关控件时，清空已知房间，避免退出直播间后还显示旧ID
        if not collected_ids:
            self._sticky_room_id = None
            return None, None

        room_id: Optional[str] = None
        user_id: Optional[str] = None

        strong_rooms = []
        strong_users = []
        weak_ids = []
        has_user_profile = False

        # 1. 第一遍扫描：收集所有特征与分类 ID
        for depth, name in collected_ids:
            if any(m in name for m in self.USER_MARKERS):
                has_user_profile = True

            mr = self._strong_room_re.search(name)
            if mr:
                strong_rooms.append((depth, mr.group(1)))
                continue

            mu = self._strong_user_re.search(name)
            if mu:
                strong_users.append((depth, mu.group(1)))
                continue

            mw = self._weak_id_re.search(name)
            if mw:
                weak_ids.append((depth, mw.group(1)))

        # 按深度排序，优先取最上层 UI
        strong_rooms.sort(key=lambda x: x[0])
        strong_users.sort(key=lambda x: x[0])
        weak_ids.sort(key=lambda x: x[0])

        # 2. 强特征解析 (绝对可信)
        if strong_rooms:
            room_id = strong_rooms[0][1]
            self._sticky_room_id = room_id

        if strong_users:
            user_id = strong_users[0][1]

        # 恢复房间上下文
        if room_id is None:
            room_id = self._sticky_room_id

        # 3. 弱特征智能解析 (无上下文前缀的纯 ID)
        weak_id_values = [w[1] for w in weak_ids]

        # 场景 A: 资料卡已展开 -> 弱 ID 绝对是用户，保护房间号
        if has_user_profile and user_id is None:
            for wid in weak_id_values:
                if room_id and wid == room_id:
                    continue
                user_id = wid
                break

        # 场景 B: 资料卡未展开 -> 且没有强匹配的房间号 -> 弱 ID 视为新房间
        if not has_user_profile and not strong_rooms and weak_id_values:
            candidate = weak_id_values[0]
            # 仅在没有房间号，或者 candidate 看起来不像长串 uid 时才更新，防止误杀
            if not room_id or len(candidate) < self._USER_ID_LEN_HINT:
                room_id = candidate
                self._sticky_room_id = room_id

        # 4. 最终兜底 (如果前面都没解析出用户，但存在明显的超长 ID)
        if user_id is None and weak_id_values:
            for wid in weak_id_values:
                if wid != room_id and len(wid) >= self._USER_ID_LEN_HINT:
                    user_id = wid
                    break

        # 安全断言：确保不会将相同的 ID 既当房间又当用户
        if room_id and room_id == user_id:
            user_id = None

        return room_id, user_id

    @property
    def sticky_room_id(self) -> Optional[str]:
        return self._sticky_room_id


# ============================================================================
# UI Scanner (Iterative)
# ============================================================================


class UIScanner:
    """收集含 ID 文案的控件；解析交给 DefaultIDExtractor。"""

    _INTEREST_RE = re.compile(
        r"(?:"
        r"男神|女神|点唱|拍拍|游戏|个人房|密码房|音乐|情感|脱口秀"
        r"|IP\u5c5e\u5730|\u7c89\u4e1d"
        r"|ID\s*[\:\uFF1a]"
        r")",
        re.IGNORECASE,
    )

    def __init__(self, target_process_name: str, max_depth: int):
        self.target_process_name = target_process_name.lower()
        self.max_depth = max_depth

    def scan(self) -> Tuple[Optional[int], List[Tuple[int, str]]]:
        target_pid = self._find_process_pid()
        if target_pid is None:
            return None, []

        if not WINDOWS_AVAILABLE:
            return target_pid, []

        collected: List[Tuple[int, str]] = []
        root = auto.GetRootControl()

        for window in root.GetChildren():
            if window.ProcessId != target_pid:
                continue
            self._collect_ids_from_control(window, collected, depth=0)

        return target_pid, collected

    def _find_process_pid(self) -> Optional[int]:
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.info["name"].lower() == self.target_process_name:
                    return proc.info["pid"]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    def _collect_ids_from_control(
        self, control: auto.Control, collected: List[Tuple[int, str]], depth: int
    ) -> None:
        stack = [(control, depth)]
        while stack:
            curr, curr_depth = stack.pop()
            if curr_depth > self.max_depth:
                continue

            name = curr.Name or ""
            if name and "." not in name and self._INTEREST_RE.search(name):
                collected.append((curr_depth, name))

            try:
                children = curr.GetChildren()
                for child in reversed(children):
                    stack.append((child, curr_depth + 1))
            except Exception:
                pass


# ============================================================================
# RoomMonitor Thread
# ============================================================================


class RoomMonitor(threading.Thread):
    DEFAULT_TARGET_PROCESS = "small_dimple.exe"

    def __init__(
        self,
        callback: Optional[Callable[[Optional[str], Optional[str]], None]] = None,
        heartbeat_interval: float = 2.0,
        max_depth: int = 8,
        target_process: Optional[str] = None,
        extractor: Optional[IDExtractor] = None,
        memory_probe_enabled: bool = False,
        memory_merge_mode: str = "override",
        memory_max_region_bytes: int = 512 * 1024,
        memory_max_total_bytes: int = 12 * 1024 * 1024,
    ) -> None:
        super().__init__(daemon=True)
        self.callback = callback
        self.heartbeat_interval = heartbeat_interval
        self.max_depth = max_depth
        self.target_process_name = (target_process or self.DEFAULT_TARGET_PROCESS).lower()

        self._extractor = extractor or DefaultIDExtractor()
        self._scanner = UIScanner(self.target_process_name, max_depth)
        self._memory_merge_mode = (memory_merge_mode or "override").lower().strip()
        if self._memory_merge_mode not in ("override", "fill"):
            logger.warning(
                "Unknown memory_merge_mode %r, using 'override'",
                memory_merge_mode,
            )
            self._memory_merge_mode = "override"
        self._memory_probe: Optional[MemoryRoomProbe] = None
        if memory_probe_enabled:
            self._memory_probe = MemoryRoomProbe(
                max_region_bytes=memory_max_region_bytes,
                max_total_bytes=memory_max_total_bytes,
            )

        self._running = False
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        self._current_room_id: Optional[str] = None
        self._current_user_id: Optional[str] = None
        self._target_pid: Optional[int] = None

        self.stats = {
            "total_scans": 0,
            "room_changes": 0,
            "user_changes": 0,
            "last_error": None,
        }

        # 房间号需连续 2 次解析一致才提交，减轻控件树/内存噪声导致的来回覆盖
        self._room_debounce_candidate: Optional[str] = None
        self._room_debounce_count: int = 0

        logger.info(
            "RoomMonitor initialised: target=%s, interval=%.1fs, depth=%d, memory=%s (%s)",
            self.target_process_name,
            heartbeat_interval,
            max_depth,
            bool(self._memory_probe),
            self._memory_merge_mode if self._memory_probe else "n/a",
        )

    def run(self) -> None:
        if WINDOWS_AVAILABLE:
            auto.UIAutomationInitializerInThread()

        self._running = True
        logger.info("RoomMonitor thread started (target: %s)", self.target_process_name)

        while not self._stop_event.wait(self.heartbeat_interval):
            try:
                self._monitor_cycle()
            except Exception as exc:
                logger.error("Monitor cycle error: %s", exc, exc_info=True)
                self.stats["last_error"] = str(exc)
                time.sleep(self.heartbeat_interval)

        logger.info("RoomMonitor thread stopped.")

    def stop(self) -> None:
        self._stop_event.set()
        self._running = False

    def _merge_memory_ui(
        self,
        ui_room: Optional[str],
        ui_user: Optional[str],
        mem_room: Optional[str],
        mem_user: Optional[str],
    ) -> Tuple[Optional[str], Optional[str]]:
        """UI 优先，内存仅补齐；fill/override 均不再用内存覆盖已有 UI 结果（防抖动）。"""
        room_id = ui_room or mem_room
        user_id = ui_user or mem_user

        if room_id and user_id and room_id == user_id:
            sticky = getattr(self._extractor, "sticky_room_id", None)
            if sticky and sticky != user_id:
                room_id = sticky

        return room_id, user_id

    def _debounce_room_id(self, candidate: Optional[str]) -> Optional[str]:
        """连续 2 次相同候选才采纳；与当前已展示相同则立即通过。"""
        with self._lock:
            current = self._current_room_id
        if candidate is None:
            return current
        if current is None and candidate:
            self._room_debounce_candidate = candidate
            self._room_debounce_count = 2
            return candidate
        if candidate == current:
            self._room_debounce_candidate = candidate
            self._room_debounce_count = 0
            return candidate
        if candidate == self._room_debounce_candidate:
            self._room_debounce_count += 1
        else:
            self._room_debounce_candidate = candidate
            self._room_debounce_count = 1
        if self._room_debounce_count >= 2:
            return candidate
        return current

    def _monitor_cycle(self) -> None:
        with self._lock:
            self.stats["total_scans"] += 1

        target_pid, collected_ids = self._scanner.scan()

        with self._lock:
            if target_pid is None:
                self._extractor.reset()
                self._room_debounce_candidate = None
                self._room_debounce_count = 0
                self._target_pid = None
                self._handle_info_change(None, None)
                return

            self._target_pid = target_pid

        room_id, user_id = self._extractor.extract(collected_ids)

        if self._memory_probe is not None:
            mem_room, mem_user = self._memory_probe.probe(target_pid)
            room_id, user_id = self._merge_memory_ui(
                room_id, user_id, mem_room, mem_user
            )

        # 本轮无控件样本时：不清空用户栏（资料卡/树闪断）
        if not collected_ids:
            with self._lock:
                if room_id is None:
                    room_id = self._current_room_id or self._extractor.sticky_room_id
                if user_id is None:
                    user_id = self._current_user_id

        if room_id and user_id and room_id == user_id:
            sticky = getattr(self._extractor, "sticky_room_id", None)
            if sticky and sticky != user_id:
                room_id = sticky

        room_id = self._debounce_room_id(room_id)

        with self._lock:
            self._handle_info_change(room_id, user_id)

    def _handle_info_change(self, new_room: Optional[str], new_user: Optional[str]) -> None:
        changed = False

        if new_room != self._current_room_id:
            self._current_room_id = new_room
            self.stats["room_changes"] += 1
            if new_room:
                logger.info("Room captured: %s", new_room)
            else:
                logger.info("Room exited.")
            changed = True

        if new_user != self._current_user_id:
            self._current_user_id = new_user
            self.stats["user_changes"] += 1
            if new_user:
                logger.info("User captured: %s", new_user)
            changed = True

        if changed and self.callback:
            try:
                self.callback(self._current_room_id, self._current_user_id)
            except Exception as exc:
                logger.error("Callback error: %s", exc, exc_info=True)

    def get_current_room_id(self) -> Optional[str]:
        with self._lock:
            return self._current_room_id

    def get_current_user_id(self) -> Optional[str]:
        with self._lock:
            return self._current_user_id

    def get_stats(self) -> dict:
        with self._lock:
            return self.stats.copy()

    def is_running(self) -> bool:
        return self._running

    def is_target_running(self) -> bool:
        with self._lock:
            return self._target_pid is not None


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_room_monitor(
    callback: Optional[Callable[[Optional[str], Optional[str]], None]] = None,
    target_process: Optional[str] = None,
    heartbeat_interval: float = 2.0,
    max_depth: int = 8,
    room_id_pattern: Optional[str] = None,
    memory_probe_enabled: bool = False,
    memory_merge_mode: str = "override",
    memory_max_region_bytes: int = 512 * 1024,
    memory_max_total_bytes: int = 12 * 1024 * 1024,
) -> Optional[RoomMonitor]:
    if not WINDOWS_AVAILABLE:
        logger.warning("Windows UIAutomation unavailable; RoomMonitor disabled.")
        return None

    monitor = RoomMonitor(
        callback=callback,
        heartbeat_interval=heartbeat_interval,
        max_depth=max_depth,
        target_process=target_process,
        memory_probe_enabled=memory_probe_enabled,
        memory_merge_mode=memory_merge_mode,
        memory_max_region_bytes=memory_max_region_bytes,
        memory_max_total_bytes=memory_max_total_bytes,
    )
    logger.info(
        "RoomMonitor created: target=%s, interval=%.1f, depth=%d, memory_probe=%s",
        target_process or monitor.DEFAULT_TARGET_PROCESS,
        heartbeat_interval,
        max_depth,
        memory_probe_enabled,
    )
    return monitor
