# -*- coding: utf-8 -*-
"""
Environment-aware configuration for desktop client.

Supports multi-environment configuration:
1. Development: .env.development
2. Production: .env.production
3. Test: .env.test

Environment variables override config.json settings.

Author : AHDUNYI
Version: 9.1.0
"""
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .settings import AppSettings, ConfigManager


def load_environment() -> str:
    """Load environment from OS environment variable."""
    env = os.environ.get("ENVIRONMENT", "development").lower()
    if env not in ["development", "production", "test"]:
        print(f"⚠ Warning: Unknown environment '{env}', defaulting to 'development'")
        env = "development"
    return env


def load_env_file(environment: str) -> bool:
    """Load environment variables from appropriate .env file.
    
    Returns:
        True if environment file was loaded, False otherwise.
    """
    # Look for .env files in multiple locations
    env_files = [
        Path(__file__).parent.parent.parent.parent / f".env.{environment}",
        Path(__file__).parent.parent.parent.parent / ".env",
        Path(__file__).parent.parent.parent.parent / ".env.example",
    ]
    
    for env_file in env_files:
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=True)
            print(f"📁 Loaded environment file: {env_file.name}")
            return True
    
    print(f"⚠ Warning: No .env file found for environment '{environment}'")
    return False


def apply_environment_overrides(settings: AppSettings) -> AppSettings:
    """Apply environment variable overrides to settings."""
    # Server configuration
    server_url = os.environ.get("DESKTOP_SERVER_URL")
    if server_url:
        settings.server.url = server_url
    
    # GUI configuration
    window_width = os.environ.get("DESKTOP_WINDOW_WIDTH")
    if window_width:
        settings.gui.window_width = int(window_width)
    
    window_height = os.environ.get("DESKTOP_WINDOW_HEIGHT")
    if window_height:
        settings.gui.window_height = int(window_height)
    
    # Logging configuration
    log_level = os.environ.get("DESKTOP_LOG_LEVEL")
    if log_level:
        settings.logging.level = log_level.upper()
    
    log_file = os.environ.get("DESKTOP_LOG_FILE")
    if log_file:
        settings.logging.file = log_file
    
    # Debug configuration
    enable_console = os.environ.get("DESKTOP_ENABLE_CONSOLE")
    if enable_console:
        settings.debug.enable_console = enable_console.lower() == "true"
    
    # Features configuration
    auto_start_monitor = os.environ.get("FEATURE_AUTO_START_MONITOR")
    if auto_start_monitor:
        settings.features.auto_start_monitor = auto_start_monitor.lower() == "true"
    
    # Room monitor configuration
    memory_probe_enabled = os.environ.get("FEATURE_MEMORY_PROBE_ENABLED")
    if memory_probe_enabled:
        settings.room_monitor.memory_probe_enabled = memory_probe_enabled.lower() == "true"
    
    memory_merge_mode = os.environ.get("FEATURE_MEMORY_MERGE_MODE")
    if memory_merge_mode:
        settings.room_monitor.memory_merge_mode = memory_merge_mode
    
    target_process = os.environ.get("MONITOR_TARGET_PROCESS")
    if target_process:
        settings.room_monitor.target_process = target_process
    
    heartbeat_interval = os.environ.get("MONITOR_HEARTBEAT_INTERVAL")
    if heartbeat_interval:
        settings.room_monitor.heartbeat_interval = float(heartbeat_interval)
    
    max_search_depth = os.environ.get("MONITOR_MAX_SEARCH_DEPTH")
    if max_search_depth:
        settings.room_monitor.max_search_depth = int(max_search_depth)
    
    memory_max_region_bytes = os.environ.get("MONITOR_MEMORY_MAX_REGION_BYTES")
    if memory_max_region_bytes:
        settings.room_monitor.memory_max_region_bytes = int(memory_max_region_bytes)
    
    memory_max_total_bytes = os.environ.get("MONITOR_MEMORY_MAX_TOTAL_BYTES")
    if memory_max_total_bytes:
        settings.room_monitor.memory_max_total_bytes = int(memory_max_total_bytes)
    
    return settings


class EnvAwareConfigManager(ConfigManager):
    """Environment-aware configuration manager."""
    
    def __init__(self, config_path: Optional[Path] = None):
        super().__init__(config_path)

        # ConfigManager does not create `self.settings` in __init__.
        # Initialize from defaults / config.json first, then apply env overrides.
        self.settings = self.load()
        
        # Load environment
        self.environment = load_environment()
        
        # Load environment file
        load_env_file(self.environment)
        
        # Apply environment overrides
        self.settings = apply_environment_overrides(self.settings)
        
        # Log configuration
        self._log_config()
    
    def _log_config(self) -> None:
        """Log configuration safely."""
        print("=" * 60)
        print(f"🚀 {self.settings.display_name} - Desktop Client")
        print(f"📊 Environment: {self.environment.upper()}")
        print(f"🌐 Server URL: {self.settings.server.url}")
        print(f"🖥️  Window: {self.settings.gui.window_width}x{self.settings.gui.window_height}")
        print(f"📝 Log Level: {self.settings.logging.level}")
        print(f"🔧 Debug Console: {self.settings.debug.enable_console}")
        print(f"🎯 Target Process: {self.settings.room_monitor.target_process}")
        print("=" * 60)
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.environment == "test"


# Global configuration instance
config_manager = EnvAwareConfigManager()
settings = config_manager.settings