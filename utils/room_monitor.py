"""
RoomMonitor 统帅钦定版 (基于 V8.6 靓号增强版实验代码)
核心：保留最原始、最精准的递归搜索算法，深度融入后端架构
"""

import re
import time
import threading
import psutil
from typing import Optional, Callable, Dict, Any
import logging

try:
    import uiautomation as auto
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    auto = None

logger = logging.getLogger(__name__)

class RoomMonitor(threading.Thread):
    TARGET_PROCESS_NAME = "small_dimple.exe"
    
    # 🎯 完全采用实验版的升级靓号正则
    ID_PATTERN = re.compile(r'(?:靓\s*|ID[:：]\s*)?(\d{3,10})')

    def __init__(self, callback=None, heartbeat_interval=2.0, max_depth=8):
        super().__init__(daemon=True)
        self.callback = callback
        self.heartbeat_interval = heartbeat_interval
        self.max_depth = max_depth 
        
        self._running = False
        self._current_room_id = None
        self._target_pid = None
        self.stats = {"total_scans": 0, "room_changes": 0, "last_error": None}
        
        logger.info(f"🎯 RoomMonitor初始化: interval={heartbeat_interval}s, depth={max_depth}")

    def run(self):
        # 解决 COM 线程初始化问题
        if WINDOWS_AVAILABLE:
            _initializer = auto.UIAutomationInitializerInThread()
            
        self._running = True
        logger.info("🚀 AHDUNYI 影子探针 V8.6 [靓号识别增强版] 线程已挂载启动...")
        logger.info("💎 正在监控... 3-10位常规号及带『靓』字短号均已纳入监测范围。")
        
        while self._running:
            try:
                self._monitor_cycle()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                self.stats["last_error"] = str(e)
                time.sleep(self.heartbeat_interval * 2)

    def stop(self):
        """提供给 main.py 关闭线程的接口"""
        self._running = False

    def _monitor_cycle(self):
        self.stats["total_scans"] += 1
        
        # 1. 查找 PID (复刻实验版逻辑)
        target_pid = None
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == self.TARGET_PROCESS_NAME.lower():
                    target_pid = proc.info['pid']
                    break
            except:
                continue
                
        if not target_pid:
            self._target_pid = None
            self._handle_room_id_change(None)
            return

        self._target_pid = target_pid
        
        if not WINDOWS_AVAILABLE:
            return
            
        root = auto.GetRootControl()
        current_found_id = None

        # 2. 🎯 核心搜索：完全复刻实验版的 quick_find 逻辑
        for window in root.GetChildren():
            try:
                if window.ProcessId == target_pid:
                    
                    def quick_find(control, depth=0):
                        nonlocal current_found_id
                        if depth > self.max_depth or current_found_id: return
                        
                        try:
                            for element in control.GetChildren():
                                name = element.Name
                                if name and "." not in name:
                                    match = self.ID_PATTERN.search(name)
                                    if match:
                                        potential_id = match.group(1)
                                        # 过滤短号或特判“靓”字
                                        if "靓" in name or len(potential_id) >= 4:
                                            current_found_id = potential_id
                                            return
                                quick_find(element, depth + 1)
                        except: pass
                    
                    quick_find(window)
                    if current_found_id: break
            except: continue

        # 3. 触发状态变更
        self._handle_room_id_change(current_found_id)

    def _handle_room_id_change(self, new_id: Optional[str]):
        if new_id != self._current_room_id:
            self._current_room_id = new_id
            
            if new_id:
                self.stats["room_changes"] += 1
                # 沿用实验版的炫酷输出
                is_pretty = " [至尊靓号]" if len(new_id) < 6 else ""
                logger.info(f"🔥 【精准捕获】房间号: {new_id}{is_pretty}")
            else:
                logger.info("📴 【实时状态】退出房间")
                
            if self.callback:
                try:
                    self.callback(new_id)
                except Exception as e:
                    logger.error(f"回调执行失败: {e}")

    # 提供给后端的标准化接口
    def get_current_room_id(self): return self._current_room_id
    def get_stats(self): return self.stats.copy()
    def is_running(self): return self._running
    def is_target_running(self): return self._target_pid is not None

def create_room_monitor(callback=None, target_process=None, heartbeat_interval=2.0, max_depth=8, room_id_pattern=None):
    """
    创建RoomMonitor实例
    参数:
        callback: 回调函数
        target_process: 目标进程名 (兼容参数，实际使用 RoomMonitor.TARGET_PROCESS_NAME)
        heartbeat_interval: 心跳间隔
        max_depth: 最大搜索深度
        room_id_pattern: 房间ID正则模式 (兼容参数，实际使用 RoomMonitor.ID_PATTERN)
    """
    if not WINDOWS_AVAILABLE:
        logger.warning("⚠️ Windows环境不可用，RoomMonitor无法启动")
        return None
    
    # 创建RoomMonitor实例
    monitor = RoomMonitor(
        callback=callback,
        heartbeat_interval=heartbeat_interval,
        max_depth=max_depth
    )
    
    logger.info(f"✅ RoomMonitor已创建: target={target_process or monitor.TARGET_PROCESS_NAME}, "
                f"interval={heartbeat_interval}, depth={max_depth}")
    
    return monitor