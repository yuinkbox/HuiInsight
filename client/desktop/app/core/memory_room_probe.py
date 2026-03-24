# -*- coding: utf-8 -*-
"""
MemoryRoomProbe - optional memory scanning for room/user ID.

This module provides a fallback stub when ReadProcessMemory-based
scanning is not available or not needed.  The real implementation
would scan the target process memory for room/user ID strings.

Author : AHDUNYI
Version: 9.0.0
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import ctypes
    import ctypes.wintypes
    _WINDOWS = True
except ImportError:
    _WINDOWS = False


class MemoryRoomProbe:
    """Scan target process memory for room/user ID strings.

    On non-Windows platforms or when ctypes is unavailable, all probe
    calls return (None, None) silently.

    Args:
        max_region_bytes: Maximum bytes per memory region to scan.
        max_total_bytes:  Maximum total bytes to scan per probe call.
    """

    def __init__(
        self,
        max_region_bytes: int = 512 * 1024,
        max_total_bytes: int = 12 * 1024 * 1024,
    ) -> None:
        self._max_region_bytes = max_region_bytes
        self._max_total_bytes = max_total_bytes

        if not _WINDOWS:
            logger.warning(
                "MemoryRoomProbe: ctypes unavailable, memory scanning disabled."
            )

    def probe(self, pid: int) -> Tuple[Optional[str], Optional[str]]:
        """Scan process memory for room and user IDs.

        Args:
            pid: Target process PID.

        Returns:
            Tuple of (room_id, user_id), either may be None.
        """
        if not _WINDOWS:
            return None, None

        try:
            return self._scan(pid)
        except Exception as exc:  # pylint: disable=broad-except
            logger.debug("MemoryRoomProbe.probe error (pid=%d): %s", pid, exc)
            return None, None

    def _scan(self, pid: int) -> Tuple[Optional[str], Optional[str]]:
        """Internal memory scan implementation.

        Args:
            pid: Target process PID.

        Returns:
            Tuple of (room_id, user_id).
        """
        import re

        PROCESS_VM_READ = 0x0010
        PROCESS_QUERY_INFORMATION = 0x0400

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]

        handle = kernel32.OpenProcess(
            PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid
        )
        if not handle:
            return None, None

        room_id: Optional[str] = None
        user_id: Optional[str] = None
        total_scanned = 0

        # Patterns matching room/user strings in memory
        room_re = re.compile(
            rb"(?:\xe5\xa5\xb3\xe7\xa5\x9e|\xe7\x94\xb7\xe7\xa5\x9e|\xe9\x9f\xb3\xe4\xb9\x90)"
            rb"[\|\uff5c\u4e¨/]\s*ID[:\uff1a]\s*(\d{3,10})",
            re.IGNORECASE,
        )
        user_re = re.compile(
            rb"ID[:\uff1a]\s*(\d{3,10})\s*IP\xe5\xb1\x9e\xe5\x9c\xb0",
            re.IGNORECASE,
        )

        try:
            class MEMORY_BASIC_INFORMATION(ctypes.Structure):
                _fields_ = [
                    ("BaseAddress", ctypes.c_void_p),
                    ("AllocationBase", ctypes.c_void_p),
                    ("AllocationProtect", ctypes.wintypes.DWORD),
                    ("RegionSize", ctypes.c_size_t),
                    ("State", ctypes.wintypes.DWORD),
                    ("Protect", ctypes.wintypes.DWORD),
                    ("Type", ctypes.wintypes.DWORD),
                ]

            MEM_COMMIT = 0x1000
            PAGE_READABLE = 0x02 | 0x04 | 0x20 | 0x40

            addr = 0
            mbi = MEMORY_BASIC_INFORMATION()
            mbi_size = ctypes.sizeof(mbi)

            while total_scanned < self._max_total_bytes:
                result = kernel32.VirtualQueryEx(
                    handle, ctypes.c_void_p(addr), ctypes.byref(mbi), mbi_size
                )
                if not result:
                    break

                region_size = mbi.RegionSize
                if (
                    mbi.State == MEM_COMMIT
                    and mbi.Protect & PAGE_READABLE
                    and region_size > 0
                    and region_size <= self._max_region_bytes
                ):
                    buf = (ctypes.c_char * region_size)()
                    bytes_read = ctypes.c_size_t(0)
                    if kernel32.ReadProcessMemory(
                        handle,
                        ctypes.c_void_p(addr),
                        buf,
                        region_size,
                        ctypes.byref(bytes_read),
                    ):
                        chunk = bytes(buf[: bytes_read.value])
                        total_scanned += len(chunk)

                        if room_id is None:
                            m = room_re.search(chunk)
                            if m:
                                room_id = m.group(1).decode("utf-8", errors="ignore")

                        if user_id is None:
                            m = user_re.search(chunk)
                            if m:
                                user_id = m.group(1).decode("utf-8", errors="ignore")

                        if room_id and user_id:
                            break

                if mbi.BaseAddress is not None:
                    addr = mbi.BaseAddress + region_size
                else:
                    addr += region_size

                if addr >= 0x7FFFFFFF0000:
                    break
        finally:
            kernel32.CloseHandle(handle)

        return room_id, user_id
