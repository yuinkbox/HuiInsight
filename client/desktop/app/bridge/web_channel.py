# -*- coding: utf-8 -*-
"""
QWebChannel bridge - exposes Python state to the Vue frontend.

Protocol
--------
* JS calls bridge.getRoomId()        -> Python returns current room ID.
* JS calls bridge.getSystemStatus()  -> Python returns a JSON string.
* Python emits roomIdChanged(str)    -> JS listener updates UI.
* Python emits systemStatusChanged(str) -> JS listener updates UI.

Author : xvyu
Version: 1.0.0
"""

import json
from typing import Optional, Any
import logging

import requests
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)


class AppBridge(QObject):
    """Qt object exposed to JavaScript via QWebChannel.

    All public pyqtSlot methods are callable from Vue components.
    All pyqtSignal signals can be subscribed to from JavaScript.

    Args:
        parent: Optional QObject parent.
    """

    # Signals emitted to JavaScript
    roomIdChanged = pyqtSignal(str, name="roomIdChanged")
    roomInfoChanged = pyqtSignal(str, name="roomInfoChanged")
    systemStatusChanged = pyqtSignal(str, name="systemStatusChanged")
    tokenInfoChanged = pyqtSignal(str, name="tokenInfoChanged")
    violationSubmitted = pyqtSignal(str, name="violationSubmitted")
    # OTA update signals
    updateAvailable = pyqtSignal(str, name="updateAvailable")
    updateProgress = pyqtSignal(int, name="updateProgress")
    updateReady = pyqtSignal(str, name="updateReady")

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._room_id: Optional[str] = None
        self._user_id: Optional[str] = None
        self._token_info: dict = {}
        self._monitor_running: bool = False

    # ------------------------------------------------------------------
    # Slots callable from JavaScript
    # ------------------------------------------------------------------

    @pyqtSlot(result=str)
    def getRoomId(self) -> str:
        """Return the currently monitored room ID, or empty string."""
        return self._room_id or ""

    @pyqtSlot(result=str)
    def getRoomInfo(self) -> str:
        """Return JSON with both room_id and user_id."""
        return json.dumps(
            {
                "room_id": self._room_id or "",
                "user_id": self._user_id or "",
            },
            ensure_ascii=False,
        )

    @pyqtSlot(result=str)
    def getSystemStatus(self) -> str:
        """Return a JSON-encoded system status snapshot."""
        status = {
            "room_id": self._room_id,
            "monitor_running": self._monitor_running,
            "token_info": self._token_info,
        }
        return json.dumps(status, ensure_ascii=False)

    @pyqtSlot(result=str)
    def getTokenInfo(self) -> str:
        """Return the current login token payload as a JSON string."""
        return json.dumps(self._token_info, ensure_ascii=False)

    @pyqtSlot(str, str, result=str)
    def desktopLogin(self, username: str, password: str) -> str:
        """Perform desktop-side login request and return JSON result."""
        try:
            win = self.parent()
            server_url = None
            if win and hasattr(win, "_settings"):
                server_url = getattr(getattr(win, "_settings"), "server", None)
                server_url = getattr(server_url, "url", None)

            if not server_url:
                from client.desktop.config.enhanced_config import get_server_url

                server_url = get_server_url()

            login_url = f"{str(server_url).rstrip('/')}/api/auth/login"
            response = requests.post(
                login_url,
                json={"username": username, "password": password},
                timeout=10,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )

            try:
                data: Any = response.json()
            except Exception:
                data = {"detail": response.text or "Unknown response"}

            if 200 <= response.status_code < 300:
                return json.dumps(
                    {"ok": True, "status": response.status_code, "data": data},
                    ensure_ascii=False,
                )

            detail = data.get("detail") if isinstance(data, dict) else str(data)
            return json.dumps(
                {
                    "ok": False,
                    "status": response.status_code,
                    "detail": detail or "Login failed",
                    "message": "Server returned non-success status",
                },
                ensure_ascii=False,
            )

        except Exception as exc:
            logger.error("Bridge desktopLogin failed: %s", exc)
            return json.dumps(
                {
                    "ok": False,
                    "status": 0,
                    "detail": str(exc),
                    "message": "Desktop login request failed",
                },
                ensure_ascii=False,
            )

    @pyqtSlot(str)
    def logFromJS(self, message: str) -> None:
        """Receive a log message forwarded from the Vue console."""
        logger.info("[JS] %s", message)

    @pyqtSlot(bool)
    def setAlwaysOnTop(self, enabled: bool) -> None:
        """Toggle window-stays-on-top flag from JavaScript."""
        win = self.parent()
        if win and hasattr(win, "set_always_on_top"):
            win.set_always_on_top(enabled)
            logger.info("Bridge: alwaysOnTop -> %s", enabled)

    @pyqtSlot(bool)
    def setMiniMode(self, enabled: bool) -> None:
        """Switch between mini-float and normal window size from JavaScript."""
        win = self.parent()
        if win and hasattr(win, "set_mini_mode"):
            win.set_mini_mode(enabled)
            logger.info("Bridge: miniMode -> %s", enabled)

    @pyqtSlot()
    def openViolationPopup(self) -> None:
        """Open a separate OS window for the violation form (mini mode)."""
        win = self.parent()
        if win and hasattr(win, "open_violation_popup"):
            win.open_violation_popup()
            logger.info("Bridge: openViolationPopup")

    @pyqtSlot()
    def closeViolationPopup(self) -> None:
        """Close the auxiliary violation form window."""
        win = self.parent()
        if win and hasattr(win, "close_violation_popup"):
            win.close_violation_popup()
            logger.info("Bridge: closeViolationPopup")

    @pyqtSlot()
    def startMonitor(self) -> None:
        """Start (or restart) the RoomMonitor from JavaScript (workflow start)."""
        win = self.parent()
        if win and hasattr(win, "restart_room_monitor"):
            win.restart_room_monitor()
            logger.info("Bridge: startMonitor requested")

    @pyqtSlot()
    def stopMonitor(self) -> None:
        """Stop the RoomMonitor from JavaScript (workflow end)."""
        win = self.parent()
        if win and hasattr(win, "stop_room_monitor"):
            win.stop_room_monitor()
            logger.info("Bridge: stopMonitor requested")

    @pyqtSlot(str)
    def notifyViolationSubmitted(self, payload_json: str) -> None:
        """Forward violation submit from the popup WebView to the main window."""
        self.violationSubmitted.emit(payload_json)

    # ------------------------------------------------------------------
    # Python-side setters (called by main application logic)
    # ------------------------------------------------------------------

    def update_room_id(self, room_id: Optional[str]) -> None:
        """Backward-compat: update room_id only."""
        self._room_id = room_id
        self.roomIdChanged.emit(room_id or "")
        logger.debug("Bridge: roomIdChanged -> %s", room_id)

    def update_room_info(self, room_id: Optional[str], user_id: Optional[str]) -> None:
        """Update both room_id and user_id, notify JavaScript."""
        self._room_id = room_id
        self._user_id = user_id
        self.roomIdChanged.emit(room_id or "")
        info = json.dumps(
            {
                "room_id": room_id or "",
                "user_id": user_id or "",
            },
            ensure_ascii=False,
        )
        self.roomInfoChanged.emit(info)
        logger.debug("Bridge: roomInfoChanged -> room=%s user=%s", room_id, user_id)

    def update_token_info(self, token_info: dict) -> None:
        """Store login token payload and notify JavaScript.

        Args:
            token_info: Decoded JWT payload dict from the login response.
        """
        self._token_info = token_info
        self.tokenInfoChanged.emit(json.dumps(token_info, ensure_ascii=False))
        logger.debug(
            "Bridge: tokenInfoChanged -> user=%s role=%s",
            token_info.get("username"),
            token_info.get("role"),
        )

    def update_monitor_status(self, running: bool) -> None:
        """Update the RoomMonitor running state and push to JavaScript.

        Args:
            running: True if the monitor thread is active.
        """
        self._monitor_running = running
        self.systemStatusChanged.emit(self.getSystemStatus())
        logger.debug("Bridge: monitorRunning -> %s", running)

    # ------------------------------------------------------------------
    # OTA update notifiers (called by UpdateChecker)
    # ------------------------------------------------------------------

    def notify_update_available(
        self, version: str, changelog: str, download_url: str, force: bool
    ) -> None:
        import json as _json

        payload = _json.dumps(
            {
                "version": version,
                "changelog": changelog,
                "download_url": download_url,
                "force": force,
            }
        )
        self.updateAvailable.emit(payload)

    def notify_update_progress(self, percent: int) -> None:
        self.updateProgress.emit(percent)

    def notify_update_ready(self, installer_path: str) -> None:
        self.updateReady.emit(installer_path)

    @pyqtSlot(str)
    def startInstallUpdate(self, installer_path: str) -> None:
        win = self.parent()
        if win is not None:
            setattr(win, "_closing_for_update", True)

        if win and hasattr(win, "_update_checker") and win._update_checker:
            win._update_checker.install_and_restart()
        else:
            import subprocess
            from PyQt6.QtCore import QTimer
            from PyQt6.QtWidgets import QApplication

            subprocess.Popen(
                [installer_path, "/SILENT", "/NORESTART", "/CLOSEAPPLICATIONS"]
            )
            QTimer.singleShot(1500, QApplication.quit)

    @pyqtSlot(str)
    def startDownload(self, download_url: str) -> None:
        """Start OTA installer download from JavaScript.

        Args:
            download_url: Direct URL to the installer file.
        """
        win = self.parent()
        checker = getattr(win, "_update_checker", None) if win else None
        if checker:
            checker.start_download(download_url)
            logger.info("Bridge: startDownload -> %s", download_url)
        else:
            logger.warning("Bridge: startDownload called but no UpdateChecker available")

