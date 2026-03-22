# -*- coding: utf-8 -*-
"""
Main application window - PyQt6 WebEngine container.

Loads the compiled Vue frontend from client/web/dist/index.html.
Vue handles all authentication via its LoginPage component.
No token injection from Python — Vue manages login/logout entirely.

Author : AHDUNYI
Version: 9.0.0
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from client.desktop.app.bridge.web_channel import AppBridge
from client.desktop.config.settings import AppSettings

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Primary application window hosting the Vue WebEngine frontend.
    
    Vue handles all authentication and routing. Python just provides:
    - WebEngine container
    - QWebChannel bridge for room monitoring
    """

    def __init__(
        self,
        settings: AppSettings,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._bridge = AppBridge(parent=self)

        self._is_mini = False
        self._normal_geometry = None
        self._violation_dialog: Optional[QDialog] = None

        self._setup_window()
        self._setup_webengine()

        logger.info("MainWindow ready (Vue handles auth)")

    @property
    def bridge(self) -> AppBridge:
        """Return the AppBridge instance."""
        return self._bridge

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        self.setWindowTitle("AHDUNYI Terminal PRO")
        self.resize(self._settings.gui.window_width, self._settings.gui.window_height)
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

    def _setup_webengine(self) -> None:
        self._view = QWebEngineView(self)
        self.setCentralWidget(self._view)

        # Register bridge with QWebChannel for room monitoring
        channel = QWebChannel(self._view.page())
        channel.registerObject("bridge", self._bridge)
        self._view.page().setWebChannel(channel)

        # WebEngine settings
        ws = self._view.page().settings()
        ws.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        ws.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        ws.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True
        )
        ws.setAttribute(
            QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True
        )

        # 开启开发者工具（debug 模式）
        if self._settings.debug.enable_console:
            self._devtools = QWebEngineView()
            self._devtools.setWindowTitle("DevTools - AHDUNYI Terminal")
            self._devtools.resize(1200, 700)
            self._view.page().setDevToolsPage(self._devtools.page())
            self._devtools.show()
            logger.info("DevTools opened")

        # Load frontend
        index_html = self._settings.web_client_dist / "index.html"
        if index_html.exists():
            self._view.load(QUrl.fromLocalFile(str(index_html)))
            logger.info("WebEngine loading: %s", index_html)
        else:
            self._show_build_error(self._settings.web_client_dist)

    def _show_build_error(self, dist_path: Path) -> None:
        logger.error("Frontend dist not found: %s", dist_path)
        self._view.setHtml(
            '<!DOCTYPE html><html lang="en">'
            '<head><meta charset="utf-8">'
            "<style>"
            "body{margin:0;background:#0d0f1a;color:#e2e8f0;"
            "font-family:Consolas,monospace;"
            "display:flex;align-items:center;justify-content:center;"
            "height:100vh;flex-direction:column;gap:16px}"
            "h2{color:#f87171}"
            "code{background:#1e2440;padding:4px 10px;border-radius:6px;color:#4f8ef7}"
            "</style></head>"
            "<body>"
            "<h2>Frontend not built</h2>"
            "<p>Build the Vue frontend first:</p>"
            "<code>cd client/web &amp;&amp; npm install &amp;&amp; npm run build</code>"
            "</body></html>"
        )

    # ------------------------------------------------------------------
    # Window control (called from AppBridge slots)
    # ------------------------------------------------------------------

    def set_always_on_top(self, enabled: bool) -> None:
        """Toggle the WindowStaysOnTopHint flag."""
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        self.show()
        logger.info("Always-on-top: %s", enabled)

    def set_mini_mode(self, enabled: bool) -> None:
        """Switch between compact mini-float and normal window size."""
        screen = QApplication.primaryScreen().geometry()

        if enabled and not self._is_mini:
            self._normal_geometry = self.geometry()
            mini_w, mini_h = 360, 480
            x = screen.width() - mini_w - 24
            y = 24
            self.setGeometry(x, y, mini_w, mini_h)
            self._is_mini = True
            logger.info("Entered mini mode (%dx%d)", mini_w, mini_h)

        elif not enabled and self._is_mini:
            if self._normal_geometry:
                self.setGeometry(self._normal_geometry)
            else:
                w = self._settings.gui.window_width
                h = self._settings.gui.window_height
                self.resize(w, h)
                self.move(
                    (screen.width() - w) // 2,
                    (screen.height() - h) // 2,
                )
            self._is_mini = False
            logger.info("Exited mini mode")

    def open_violation_popup(self) -> None:
        """Second top-level WebEngine window sharing profile (same login storage)."""
        if self._violation_dialog is not None and self._violation_dialog.isVisible():
            self._violation_dialog.raise_()
            self._violation_dialog.activateWindow()
            return

        index_html = self._settings.web_client_dist / "index.html"
        if not index_html.exists():
            logger.error("Cannot open violation popup: dist missing at %s", index_html)
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("违规处置上报")
        dlg.setModal(False)
        dlg.resize(560, 640)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)

        popup_view = QWebEngineView(dlg)
        profile = QWebEngineProfile.defaultProfile()
        page = QWebEnginePage(profile, popup_view)
        popup_view.setPage(page)

        channel = QWebChannel(page)
        channel.registerObject("bridge", self._bridge)
        page.setWebChannel(channel)

        url = QUrl.fromLocalFile(str(index_html.resolve()))
        url.setFragment("/desktop/violation-popup")
        popup_view.load(url)

        layout.addWidget(popup_view)
        self._violation_dialog = dlg

        def _clear_ref(_result: int = 0) -> None:
            self._violation_dialog = None

        dlg.finished.connect(_clear_ref)
        dlg.show()

    def close_violation_popup(self) -> None:
        if self._violation_dialog is not None:
            self._violation_dialog.close()
            self._violation_dialog = None

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Close AHDUNYI Terminal PRO?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            logger.info("MainWindow closing.")
            event.accept()
        else:
            event.ignore()
