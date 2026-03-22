# -*- coding: utf-8 -*-
"""
Application settings loader.

Supports JSON config file + environment-variable overrides.
All path resolution is PyInstaller _MEIPASS-aware.

Author : AHDUNYI
Version: 9.0.0
"""

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def _resource_root() -> Path:
    """Return the directory that contains bundled resources.

    When running inside a PyInstaller one-file EXE, this is the
    temporary extraction directory (_MEIPASS).  Otherwise it is the
    project root (two levels above this file: src/config/ -> root).
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).parent.parent.parent


# ---------------------------------------------------------------------------
# Sub-config dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ServerConfig:
    url: str = "http://106.15.32.246:8000"


@dataclass
class GuiConfig:
    window_width: int = 1280
    window_height: int = 800


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "client.log"


@dataclass
class PathsConfig:
    logs_directory: str = "logs"
    data_directory: str = "data"


@dataclass
class RoomMonitorConfig:
    target_process: str = "small_dimple.exe"
    heartbeat_interval: float = 2.0
    max_search_depth: int = 8
    room_id_pattern: str = r"(?:\u9765\s*|ID[:\uff1a]\s*)?(\d{3,10})"
    # 可选：从目标进程内存扫描「房间类型丨ID:」与「ID:… IP属地」文本（ReadProcessMemory）
    memory_probe_enabled: bool = False
    # override: 内存命中则覆盖 UI 结果；fill: 仅当 UI 未解析出对应字段时用内存补齐
    memory_merge_mode: str = "override"
    memory_max_region_bytes: int = 524288
    memory_max_total_bytes: int = 12582912


@dataclass
class FeaturesConfig:
    auto_start_monitor: bool = True


@dataclass
class DebugConfig:
    enable_console: bool = True


@dataclass
class AppSettings:
    """Top-level application configuration."""

    display_name: str = "AHDUNYI Terminal PRO"
    server: ServerConfig = field(default_factory=ServerConfig)
    gui: GuiConfig = field(default_factory=GuiConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    room_monitor: RoomMonitorConfig = field(default_factory=RoomMonitorConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
    debug: DebugConfig = field(default_factory=DebugConfig)

    @property
    def resource_root(self) -> Path:
        """Absolute path to the resource root directory."""
        return _resource_root()

    @property
    def web_client_dist(self) -> Path:
        """Absolute path to the compiled Vue frontend dist folder.

        PyInstaller packs the dist folder as ``client/web/dist`` inside
        _MEIPASS (matching the datas entry in AHDUNYI.spec).
        In development the path resolves to the actual monorepo location.
        """
        return self.resource_root / "client" / "web" / "dist"


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

class ConfigManager:
    """Load, parse, and validate application settings.

    Args:
        config_path: Optional path to a JSON config file.  If omitted,
            the manager looks for ``config.json`` next to the EXE / in
            the project root.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        self._config_path = config_path

    def load(self) -> AppSettings:
        """Return a fully populated AppSettings instance.

        Resolution order:
        1. Explicit config_path argument
        2. ``config.json`` in the resource root
        3. Built-in defaults
        """
        settings = AppSettings()
        path = self._resolve_path()

        if path and path.exists():
            try:
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
                self._apply(settings, data)
                logger.info("Config loaded from: %s", path)
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Config load error (%s): %s - using defaults", path, exc)
        else:
            logger.info("No config file found - using built-in defaults.")

        self._apply_env(settings)
        return settings

    def _resolve_path(self) -> Optional[Path]:
        if self._config_path:
            return Path(self._config_path)
        candidate = _resource_root() / "config.json"
        return candidate if candidate.exists() else None

    @staticmethod
    def _apply(settings: AppSettings, data: dict) -> None:
        """Overlay a parsed JSON dict onto the settings dataclass tree."""
        if "display_name" in data:
            settings.display_name = str(data["display_name"])

        srv = data.get("server", {})
        if "url" in srv:
            settings.server.url = str(srv["url"])

        gui = data.get("gui", {})
        if "window_width" in gui:
            settings.gui.window_width = int(gui["window_width"])
        if "window_height" in gui:
            settings.gui.window_height = int(gui["window_height"])

        log = data.get("logging", {})
        if "level" in log:
            settings.logging.level = str(log["level"]).upper()
        if "file" in log:
            settings.logging.file = str(log["file"])

        paths = data.get("paths", {})
        if "logs_directory" in paths:
            settings.paths.logs_directory = str(paths["logs_directory"])
        if "data_directory" in paths:
            settings.paths.data_directory = str(paths["data_directory"])

        rm = data.get("room_monitor", {})
        if "target_process" in rm:
            settings.room_monitor.target_process = str(rm["target_process"])
        if "heartbeat_interval" in rm:
            settings.room_monitor.heartbeat_interval = float(rm["heartbeat_interval"])
        if "max_search_depth" in rm:
            settings.room_monitor.max_search_depth = int(rm["max_search_depth"])
        if "memory_probe_enabled" in rm:
            settings.room_monitor.memory_probe_enabled = bool(rm["memory_probe_enabled"])
        if "memory_merge_mode" in rm:
            settings.room_monitor.memory_merge_mode = str(rm["memory_merge_mode"]).lower()
        if "memory_max_region_bytes" in rm:
            settings.room_monitor.memory_max_region_bytes = int(rm["memory_max_region_bytes"])
        if "memory_max_total_bytes" in rm:
            settings.room_monitor.memory_max_total_bytes = int(rm["memory_max_total_bytes"])

        feat = data.get("features", {})
        if "auto_start_monitor" in feat:
            settings.features.auto_start_monitor = bool(feat["auto_start_monitor"])

        dbg = data.get("debug", {})
        if "enable_console" in dbg:
            settings.debug.enable_console = bool(dbg["enable_console"])

    @staticmethod
    def _apply_env(settings: AppSettings) -> None:
        """Override settings from environment variables (for CI / Docker)."""
        if val := os.environ.get("AHDUNYI_SERVER_URL"):
            settings.server.url = val
        if val := os.environ.get("AHDUNYI_LOG_LEVEL"):
            settings.logging.level = val.upper()


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

def get_settings(config_path: Optional[str] = None) -> AppSettings:
    """Module-level convenience wrapper around ConfigManager."""
    return ConfigManager(config_path).load()
