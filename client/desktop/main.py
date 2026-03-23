# -*- coding: utf-8 -*-
"""
AHDUNYI Terminal PRO - unified application entry point.

Startup sequence
----------------
1. Load configuration (config.json or built-in defaults).
2. Initialise logging (UTF-8 safe, GBK-proof).
3. Check runtime dependencies.
4. Launch GUI event loop:
   a. Open MainWindow directly (Vue Web login page is the single login UI).
   b. Start RoomMonitor, wire callbacks to AppBridge.
5. On GUI exit: stop RoomMonitor, flush logs.

Author : AHDUNYI
Version: 9.0.0
"""

import sys
import logging
from pathlib import Path
from typing import Optional

# Monorepo root: client/desktop/ -> client/ -> repo_root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from client.desktop.config.enhanced_config import (
    EnhancedAppSettings,
    get_config,
    get_environment,
    get_server_url,
)
from client.desktop.utils.enhanced_network_client import (
    test_server_connectivity,
    format_connectivity_result,
)
from client.desktop.utils.file_helper import setup_logging

logger = logging.getLogger(__name__)


def _try_import(module: str) -> bool:
    """Return True if module can be imported without error."""
    try:
        __import__(module)
        return True
    except ImportError:
        return False


def _check_dependencies() -> list:
    """Return a list of missing package display-names."""
    required = [
        ("psutil",          ["psutil"]),
        ("uiautomation",    ["uiautomation"]),
        ("PyQt6",           ["PyQt6.QtWidgets"]),
        ("PyQt6-WebEngine", ["PyQt6.QtWebEngineWidgets"]),
    ]
    missing = []
    for display, imports in required:
        if not any(_try_import(m) for m in imports):
            missing.append(display)
    return missing


def _start_room_monitor(settings: EnhancedAppSettings, bridge) -> Optional[object]:
    """Start RoomMonitor and wire its callback to the AppBridge.

    Args:
        settings: Application settings.
        bridge: AppBridge instance to receive room-ID updates.

    Returns:
        Running RoomMonitor, or None on failure.
    """
    try:
        from client.desktop.app.core.room_monitor import create_room_monitor

        def _on_room_change(room_id: Optional[str], user_id: Optional[str] = None) -> None:
            bridge.update_room_info(room_id, user_id)

        monitor = create_room_monitor(
            callback=_on_room_change,
            target_process=settings.room_monitor.target_process,
            heartbeat_interval=settings.room_monitor.heartbeat_interval,
            max_depth=settings.room_monitor.max_search_depth,
            memory_probe_enabled=settings.room_monitor.memory_probe_enabled,
            memory_merge_mode=settings.room_monitor.memory_merge_mode,
            memory_max_region_bytes=settings.room_monitor.memory_max_region_bytes,
            memory_max_total_bytes=settings.room_monitor.memory_max_total_bytes,
        )
        if monitor:
            monitor.start()
            bridge.update_monitor_status(True)
            logger.info("RoomMonitor started.")
        return monitor
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("RoomMonitor startup failed: %s", exc)
        return None


def _check_server_connection(server_url: str) -> bool:
    """
    检查服务器连接性
    
    Args:
        server_url: 服务器URL
        
    Returns:
        是否连接成功
    """
    print("正在检查服务器连接...")
    logger.info("开始服务器连接检查: %s", server_url)
    
    try:
        # 执行详细的连接性检查
        result = test_server_connectivity(server_url, timeout=10)
        
        # 格式化并显示结果
        formatted_result = format_connectivity_result(result)
        print("\n" + "=" * 60)
        print("服务器连接检查结果:")
        print("=" * 60)
        print(formatted_result)
        print("=" * 60 + "\n")
        
        # 记录到日志
        logger.info("服务器连接检查完成: %s", "成功" if result["reachable"] else "失败")
        
        if not result["reachable"]:
            # 显示详细的错误信息
            if result.get("error_message"):
                print(f"[ERROR] 连接失败: {result['error_message']}")
                
            # 提供诊断建议
            print("\n诊断建议:")
            if not result.get("dns_resolved", False):
                print("  • DNS解析失败 - 请检查网络连接或服务器域名")
            elif not result.get("port_open", True):
                print("  • 端口被拒绝 - 请检查服务器是否正在运行，或防火墙设置")
            elif not result.get("http_accessible", False):
                print("  • HTTP访问失败 - 请检查服务器应用是否正常运行")
            else:
                print("  • 未知连接问题 - 请检查网络配置")
                
            return False
            
        print("✅ 服务器连接成功！")
        return True
        
    except Exception as e:
        error_msg = f"连接检查过程中发生错误: {e}"
        print(f"[ERROR] {error_msg}")
        logger.error(error_msg)
        return False


def _run_gui(settings: EnhancedAppSettings) -> int:
    """Create QApplication and run the main event loop.

    Returns:
        Process exit code.
    """
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtGui import QPalette, QColor

    app = QApplication(sys.argv)
    app.setApplicationName("AHDUNYI Terminal PRO")
    app.setOrganizationName("AHDUNYI")

    # Global dark palette
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,          QColor("#0d0f1a"))
    pal.setColor(QPalette.ColorRole.WindowText,      QColor("#e2e8f0"))
    pal.setColor(QPalette.ColorRole.Base,            QColor("#13162b"))
    pal.setColor(QPalette.ColorRole.AlternateBase,   QColor("#1a1f3a"))
    pal.setColor(QPalette.ColorRole.Text,            QColor("#e2e8f0"))
    pal.setColor(QPalette.ColorRole.Button,          QColor("#13162b"))
    pal.setColor(QPalette.ColorRole.ButtonText,      QColor("#e2e8f0"))
    pal.setColor(QPalette.ColorRole.Highlight,       QColor("#4f8ef7"))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(pal)

    try:
        from client.desktop.app.ui.main_window import MainWindow
    except ImportError as exc:
        logger.error("UI import failed: %s", exc)
        QMessageBox.critical(None, "Startup Error", f"Failed to load UI:\n{exc}")
        return 1

    _monitors: list = []

    try:
        # Unified login strategy: always open Vue app directly.
        # Vue LoginPage is now the single source of truth for authentication.
        main_win = MainWindow(settings=settings)

        if settings.features.auto_start_monitor:
            mon = _start_room_monitor(settings, main_win.bridge)
            if mon:
                _monitors.append(mon)

        main_win.show()
        logger.info("MainWindow displayed.")

    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to open MainWindow: %s", exc, exc_info=True)
        QMessageBox.critical(None, "Error", f"Could not open main window:\n{exc}")
        return 1

    exit_code = app.exec()

    for mon in _monitors:
        try:
            mon.stop()
        except Exception:  # pylint: disable=broad-except
            pass
    logger.info("Application exited (code=%d).", exit_code)
    return exit_code


def main() -> int:
    """Application entry point. Returns integer exit code."""
    print("AHDUNYI Terminal PRO  -  starting...")

    # 加载增强配置（dataclass，支持点号访问）
    config: EnhancedAppSettings = get_config()
    server_url = get_server_url()
    environment = get_environment()

    print(f"环境: {environment}")
    print(f"服务器: {server_url}")

    # 设置日志
    setup_logging(
        log_dir=Path(config.paths.logs_directory),
        log_file=config.logging.file,
        level=config.logging.level,
        enable_console=config.debug.enable_console,
    )
    
    logger.info("配置加载完成 - 环境: %s, 服务器: %s", environment, server_url)
    
    # 检查依赖
    missing = _check_dependencies()
    if missing:
        msg = "Missing dependencies: " + ", ".join(missing)
        logger.error(msg)
        print("[ERROR] " + msg)
        print("Run: pip install " + " ".join(missing))
        return 1
    
    # 检查服务器连接
    if not _check_server_connection(server_url):
        logger.error("服务器连接检查失败")
        return 1
    
    return _run_gui(config)


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python -m client.desktop.main [config_file]")
        sys.exit(0)

    try:
        sys.exit(main())
    except Exception as exc:  # pylint: disable=broad-except
        print("[FATAL] " + str(exc))
        import traceback
        traceback.print_exc()
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            _a = QApplication.instance() or QApplication([])
            QMessageBox.critical(
                None, "Fatal Error",
                "AHDUNYI Terminal PRO encountered a fatal error:\n\n"
                + str(exc)
                + "\n\nPlease check the log file."
            )
        except Exception:  # pylint: disable=broad-except
            pass
        try:
            if sys.stdin is not None and getattr(sys.stdin, "isatty", lambda: False)():
                input("Press Enter to exit...")
        except (EOFError, OSError, RuntimeError):
            pass
        sys.exit(1)
