# -*- coding: utf-8 -*-
"""增强版配置管理器（dataclass 结构）。"""

import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class Environment:
    """环境枚举。"""

    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


@dataclass
class ServerConfig:
    """服务器配置。"""

    url: str = "http://localhost:8000"
    timeout: int = 10
    health_check_endpoint: str = "/health"

    @classmethod
    def for_environment(cls, env: str) -> "ServerConfig":
        """按环境返回默认服务器配置。"""
        defaults = {
            Environment.DEVELOPMENT: cls(url="http://localhost:8000"),
            Environment.TEST: cls(url="http://122.51.72.36:8002"),
            Environment.PRODUCTION: cls(url="http://106.15.32.246:8000"),
        }
        return defaults.get(env, cls())


@dataclass
class GuiConfig:
    """界面配置。"""

    window_width: int = 1440
    window_height: int = 900


@dataclass
class LoggingConfig:
    """日志配置。"""

    level: str = "INFO"
    file: str = "client.log"


@dataclass
class PathsConfig:
    """路径配置。"""

    logs_directory: str = "logs"
    data_directory: str = "data"


@dataclass
class DebugConfig:
    """调试配置。"""

    enable_console: bool = False


@dataclass
class FeaturesConfig:
    """功能开关。"""

    auto_start_monitor: bool = True


@dataclass
class RoomMonitorConfig:
    """房间监控配置。"""

    target_process: str = "small_dimple.exe"
    heartbeat_interval: float = 2.0
    max_search_depth: int = 8
    memory_probe_enabled: bool = False
    memory_merge_mode: str = "override"
    memory_max_region_bytes: int = 524288
    memory_max_total_bytes: int = 12582912


@dataclass
class EnhancedAppSettings:
    """增强版应用总配置（点号访问）。"""

    environment: str = Environment.DEVELOPMENT
    display_name: str = "AHDUNYI Terminal PRO"
    server: ServerConfig = field(default_factory=ServerConfig)
    gui: GuiConfig = field(default_factory=GuiConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    debug: DebugConfig = field(default_factory=DebugConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
    room_monitor: RoomMonitorConfig = field(default_factory=RoomMonitorConfig)

    @property
    def resource_root(self) -> Path:
        """返回资源根目录（兼容 PyInstaller _MEIPASS）。"""
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)  # type: ignore[attr-defined]
        return Path(__file__).parent.parent.parent

    @property
    def web_client_dist(self) -> Path:
        """返回前端 dist 目录（供 MainWindow 加载）。"""
        return self.resource_root / "client" / "web" / "dist"


class EnhancedConfigManager:
    """增强版配置管理器。"""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self._config_path = config_path
        self._settings: Optional[EnhancedAppSettings] = None

    def load(self) -> EnhancedAppSettings:
        """加载配置（环境变量 > config.json > 默认值）。"""
        env = self._detect_environment()
        settings = EnhancedAppSettings(
            environment=env,
            server=ServerConfig.for_environment(env),
        )

        data = self._load_config_file()
        if data:
            self._apply_config_file(settings, data)

        self._apply_environment_variables(settings)
        self._validate_config(settings)
        self._settings = settings
        return settings

    def _detect_environment(self) -> str:
        """检测运行环境。"""
        env = os.environ.get("ENVIRONMENT", "").lower()
        if env in {Environment.DEVELOPMENT, Environment.TEST, Environment.PRODUCTION}:
            return env

        if hasattr(sys, "_MEIPASS"):
            env_file = Path(sys._MEIPASS) / ".environment"  # type: ignore[attr-defined]
            if env_file.exists():
                try:
                    val = env_file.read_text(encoding="utf-8").strip().lower()
                    if val in {
                        Environment.DEVELOPMENT,
                        Environment.TEST,
                        Environment.PRODUCTION,
                    }:
                        return val
                except Exception:
                    pass

        server_url = os.environ.get("DESKTOP_SERVER_URL", "")
        if "122.51.72.36" in server_url:
            return Environment.TEST
        if "106.15.32.246" in server_url:
            return Environment.PRODUCTION
        return Environment.DEVELOPMENT

    def _resolve_config_path(self) -> Optional[Path]:
        """解析 config.json 路径。"""
        if self._config_path:
            return Path(self._config_path)

        if hasattr(sys, "_MEIPASS"):
            exe_dir = (
                Path(sys.executable).parent
                if hasattr(sys, "executable")
                else Path.cwd()
            )
            candidate = exe_dir / "config.json"
            if candidate.exists():
                return candidate

        from .settings import _resource_root

        candidate = _resource_root() / "config.json"
        return candidate if candidate.exists() else None

    def _load_config_file(self) -> Optional[Dict[str, Any]]:
        """读取配置文件。"""
        path = self._resolve_config_path()
        if not path or not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("加载配置文件失败 %s: %s", path, exc)
            return None

    def _apply_config_file(
        self, settings: EnhancedAppSettings, data: Dict[str, Any]
    ) -> None:
        """将 JSON 数据映射到 dataclass。"""
        if "display_name" in data:
            settings.display_name = str(data["display_name"])

        server = data.get("server")
        if isinstance(server, dict):
            if "url" in server:
                settings.server.url = str(server["url"])
            if "timeout" in server:
                settings.server.timeout = int(server["timeout"])

        gui = data.get("gui")
        if isinstance(gui, dict):
            if "window_width" in gui:
                settings.gui.window_width = int(gui["window_width"])
            if "window_height" in gui:
                settings.gui.window_height = int(gui["window_height"])

        logging_cfg = data.get("logging")
        if isinstance(logging_cfg, dict):
            if "level" in logging_cfg:
                settings.logging.level = str(logging_cfg["level"]).upper()
            if "file" in logging_cfg:
                settings.logging.file = str(logging_cfg["file"])

        paths = data.get("paths")
        if isinstance(paths, dict):
            if "logs_directory" in paths:
                settings.paths.logs_directory = str(paths["logs_directory"])
            if "data_directory" in paths:
                settings.paths.data_directory = str(paths["data_directory"])

        debug = data.get("debug")
        if isinstance(debug, dict) and "enable_console" in debug:
            settings.debug.enable_console = bool(debug["enable_console"])

        features = data.get("features")
        if isinstance(features, dict) and "auto_start_monitor" in features:
            settings.features.auto_start_monitor = bool(features["auto_start_monitor"])

        room = data.get("room_monitor")
        if isinstance(room, dict):
            if "target_process" in room:
                settings.room_monitor.target_process = str(room["target_process"])
            if "heartbeat_interval" in room:
                settings.room_monitor.heartbeat_interval = float(
                    room["heartbeat_interval"]
                )
            if "max_search_depth" in room:
                settings.room_monitor.max_search_depth = int(room["max_search_depth"])
            if "memory_probe_enabled" in room:
                settings.room_monitor.memory_probe_enabled = bool(
                    room["memory_probe_enabled"]
                )
            if "memory_merge_mode" in room:
                settings.room_monitor.memory_merge_mode = str(
                    room["memory_merge_mode"]
                ).lower()
            if "memory_max_region_bytes" in room:
                settings.room_monitor.memory_max_region_bytes = int(
                    room["memory_max_region_bytes"]
                )
            if "memory_max_total_bytes" in room:
                settings.room_monitor.memory_max_total_bytes = int(
                    room["memory_max_total_bytes"]
                )

    def _apply_environment_variables(self, settings: EnhancedAppSettings) -> None:
        """应用环境变量覆盖。"""
        if server_url := os.environ.get("DESKTOP_SERVER_URL"):
            settings.server.url = server_url
        if timeout := os.environ.get("DESKTOP_SERVER_TIMEOUT"):
            try:
                settings.server.timeout = int(timeout)
            except ValueError:
                logger.warning("无效的超时值: %s", timeout)
        if env := os.environ.get("ENVIRONMENT"):
            env = env.lower()
            if env in {
                Environment.DEVELOPMENT,
                Environment.TEST,
                Environment.PRODUCTION,
            }:
                settings.environment = env

    def _validate_config(self, settings: EnhancedAppSettings) -> None:
        """验证关键配置。"""
        if not settings.server.url:
            raise ValueError("服务器URL不能为空")
        if not settings.server.url.startswith(("http://", "https://")):
            logger.warning("服务器URL缺少协议前缀: %s", settings.server.url)

    def save_config_template(self, path: Path) -> None:
        """保存配置模板。"""
        template = {
            "display_name": "AHDUNYI Terminal PRO",
            "environment": "test",
            "server": {"url": "http://122.51.72.36:8002", "timeout": 10},
            "gui": {"window_width": 1440, "window_height": 900},
            "logging": {"level": "INFO", "file": "client.log"},
            "paths": {"logs_directory": "logs", "data_directory": "data"},
            "debug": {"enable_console": False},
            "features": {"auto_start_monitor": True},
            "room_monitor": {
                "target_process": "small_dimple.exe",
                "heartbeat_interval": 2.0,
                "max_search_depth": 8,
                "memory_probe_enabled": False,
                "memory_merge_mode": "override",
                "memory_max_region_bytes": 524288,
                "memory_max_total_bytes": 12582912,
            },
        }
        path.write_text(
            json.dumps(template, indent=2, ensure_ascii=False), encoding="utf-8"
        )


_config_manager = EnhancedConfigManager()
_settings: Optional[EnhancedAppSettings] = None


def get_config() -> EnhancedAppSettings:
    """获取全局配置。"""
    global _settings
    if _settings is None:
        _settings = _config_manager.load()
    return _settings


def reload_config(config_path: Optional[str] = None) -> EnhancedAppSettings:
    """重载全局配置。"""
    global _config_manager, _settings
    _config_manager = EnhancedConfigManager(config_path)
    _settings = _config_manager.load()
    return _settings


def get_server_url() -> str:
    """兼容旧调用：获取服务器地址。"""
    return get_config().server.url


def get_environment() -> str:
    """兼容旧调用：获取环境名。"""
    return get_config().environment
