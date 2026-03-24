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

from client.desktop.config.env_config import config_manager, settings
from client.desktop.config.settings import AppSettings
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


def _start_room_monitor(settings: AppSettings, bridge) -> Optional[object]:
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
        )
        if monitor:
            monitor.start()
            bridge.update_monitor_status(True)
            logger.info("RoomMonitor started.")
        return monitor
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("RoomMonitor startup failed: %s", exc)
        return None



def _start_update_checker(settings: AppSettings, bridge, main_win) -> None:
    """Start OTA UpdateChecker in background thread.

    Args:
        settings: Application settings (contains server.url and version).
        bridge: AppBridge instance to emit signals to Vue frontend.
        main_win: MainWindow instance to store checker reference.
    """
    try:
        from client.desktop.app.core.updater import UpdateChecker
        version_url = settings.server.url.rstrip("/") + "/api/client/version"
        current_version = getattr(settings, "version", "1.0.0")

        def _on_available(version: str, changelog: str, dl_url: str, force: bool) -> None:
            bridge.notify_update_available(version, changelog, dl_url, force)

        def _on_progress(pct: int) -> None:
            bridge.notify_update_progress(pct)

        def _on_ready(path: str) -> None:
            bridge.notify_update_ready(path)

        checker = UpdateChecker(
            current_version=current_version,
            version_url=version_url,
            on_update_available=_on_available,
            on_progress=_on_progress,
            on_ready=_on_ready,
            delay_seconds=8.0,
        )
        main_win._update_checker = checker
        checker.start()
        logger.info("UpdateChecker started (current=%s, url=%s)", current_version, version_url)
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("UpdateChecker startup failed: %s", exc)

def _start_update_checker(settings, bridge, main_win) -> None:
    """Start OTA UpdateChecker in background thread."""
    try:
        from client.desktop.app.core.updater import UpdateChecker
        version_url = settings.server.url.rstrip('/') + '/api/client/version'
        current_version = getattr(settings, 'version', '1.0.0')

        def _on_available(version, changelog, dl_url, force):
            bridge.notify_update_available(version, changelog, dl_url, force)

        def _on_progress(pct):
            bridge.notify_update_progress(pct)

        def _on_ready(path):
            bridge.notify_update_ready(path)

        checker = UpdateChecker(
            current_version=current_version,
            version_url=version_url,
            on_update_available=_on_available,
            on_progress=_on_progress,
            on_ready=_on_ready,
            delay_seconds=8.0,
        )
        main_win._update_checker = checker
        checker.start()
        import logging as _log
        _log.getLogger(__name__).info(
            'UpdateChecker started (current=%s, url=%s)', current_version, version_url
        )
    except Exception as exc:
        import logging as _log
        _log.getLogger(__name__).warning('UpdateChecker startup failed: %s', exc)


def _run_gui(settings: AppSettings) -> int:
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
                # Store reference so restart_room_monitor/stop_room_monitor can manage it
                main_win._active_monitor = mon

        main_win.show()
        logger.info("MainWindow displayed.")

        # Start OTA update checker in background (non-blocking)
        _start_update_checker(settings, main_win.bridge, main_win)

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

    # Configuration already loaded by config_manager
    app_settings = settings

    setup_logging(
        log_dir=Path(app_settings.paths.logs_directory),
        log_file=app_settings.logging.file,
        level=app_settings.logging.level,
        enable_console=app_settings.debug.enable_console,
    )
    logger.info("Settings loaded: server=%s", app_settings.server.url)

    missing = _check_dependencies()
    if missing:
        msg = "Missing dependencies: " + ", ".join(missing)
        logger.error(msg)
        print("[ERROR] " + msg)
        print("Run: pip install " + " ".join(missing))
        return 1

    return _run_gui(app_settings)


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
