# -*- coding: utf-8 -*-
"""
OTA Update Checker for AHDUNYI Terminal PRO.

Runs in a background thread after app startup.
Checks server for newer client version, downloads installer,
and notifies the Vue frontend via AppBridge signals.

Author : xvyu
Version: 1.0.0
"""

import hashlib
import logging
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import requests
from packaging.version import Version

logger = logging.getLogger(__name__)


class UpdateChecker(threading.Thread):
    """Background thread that checks for client updates.

    Args:
        current_version: Current installed version string (e.g. '1.0.0').
        version_url: URL to GET version info from server.
        on_update_available: Callback(version, changelog, download_url, force).
        on_progress: Callback(percent: int) during download.
        on_ready: Callback(installer_path: str) when download complete.
        delay_seconds: Seconds to wait after start before checking.
    """

    def __init__(
        self,
        current_version: str,
        version_url: str,
        on_update_available: Callable[[str, str, str, bool], None],
        on_progress: Optional[Callable[[int], None]] = None,
        on_ready: Optional[Callable[[str], None]] = None,
        delay_seconds: float = 8.0,
    ) -> None:
        super().__init__(daemon=True, name="UpdateChecker")
        self.current_version = current_version
        self.version_url = version_url
        self.on_update_available = on_update_available
        self.on_progress = on_progress
        self.on_ready = on_ready
        self.delay_seconds = delay_seconds
        self._download_thread: Optional[threading.Thread] = None
        self._installer_path: Optional[str] = None

    def run(self) -> None:
        """Wait, then check for updates."""
        time.sleep(self.delay_seconds)
        try:
            self._check()
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("UpdateChecker failed silently: %s", exc)

    def _check(self) -> None:
        """Fetch version info and compare with current version."""
        logger.info("UpdateChecker: checking %s", self.version_url)
        resp = requests.get(self.version_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        latest = data.get("latest_version", "")
        min_required = data.get("min_required_version", "")
        download_url = data.get("download_url", "")
        changelog = data.get("changelog", "")
        force_update = data.get("force_update", False)

        current = Version(self.current_version)
        latest_v = Version(latest)
        min_v = Version(min_required) if min_required else None

        # Force update if below minimum required version
        if min_v and current < min_v:
            force_update = True

        if latest_v > current:
            logger.info(
                "UpdateChecker: new version %s available (current=%s, force=%s)",
                latest,
                self.current_version,
                force_update,
            )
            self.on_update_available(latest, changelog, download_url, force_update)
        else:
            logger.info("UpdateChecker: already up to date (%s)", self.current_version)

    def start_download(self, download_url: str) -> None:
        """Start downloading the installer in background.

        Args:
            download_url: Direct URL to the installer .exe file.
        """
        if self._download_thread and self._download_thread.is_alive():
            logger.warning("Download already in progress.")
            return
        self._download_thread = threading.Thread(
            target=self._download,
            args=(download_url,),
            daemon=True,
            name="UpdateDownloader",
        )
        self._download_thread.start()

    def _download(self, url: str) -> None:
        """Download installer to temp directory with progress reporting.

        Args:
            url: Direct download URL.
        """
        try:
            tmp_dir = Path(tempfile.gettempdir()) / "ahdunyi_update"
            tmp_dir.mkdir(exist_ok=True)
            installer_path = tmp_dir / "AHDUNYI_Terminal_PRO_Setup.exe"

            logger.info("UpdateDownloader: downloading from %s", url)
            resp = requests.get(url, stream=True, timeout=60)
            resp.raise_for_status()

            total = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(installer_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total and self.on_progress:
                            pct = min(int(downloaded / total * 100), 99)
                            self.on_progress(pct)

            if self.on_progress:
                self.on_progress(100)

            self._installer_path = str(installer_path)
            logger.info("UpdateDownloader: download complete -> %s", installer_path)

            if self.on_ready:
                self.on_ready(self._installer_path)

        except Exception as exc:  # pylint: disable=broad-except
            logger.error("UpdateDownloader failed: %s", exc)

    def install_and_restart(self) -> None:
        """Launch the downloaded installer silently and exit the app.

        The Inno Setup installer runs with /VERYSILENT /NORESTART,
        so it overwrites files while the old EXE has already exited.
        """
        import subprocess
        import sys
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer

        if not self._installer_path or not Path(self._installer_path).exists():
            logger.error("install_and_restart: installer not found")
            return

        logger.info("Launching installer: %s", self._installer_path)
        subprocess.Popen(
            [self._installer_path, "/SILENT", "/NORESTART", "/CLOSEAPPLICATIONS"],
        )
        # Delay slightly to let installer start, then quit
        QTimer.singleShot(1500, QApplication.quit)
