# -*- coding: utf-8 -*-
"""
Contextual Audit Engine - multi-dimensional behaviour analysis.

Replaces single-dimension dwell-time judgement with a context-aware
exemption chain.  All heavy I/O (DB queries) are delegated to an
injectable :class:`RiskDataProvider` interface so the engine itself
remains stateless and unit-testable.

Author : AHDUNYI
Version: 9.0.0
"""

import time
import threading
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import logging

try:
    from cachetools import TTLCache  # type: ignore
    _CACHETOOLS_OK: bool = True
except ImportError:
    TTLCache = None  # type: ignore
    _CACHETOOLS_OK = False

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

class AuditStatus(Enum):
    """Possible outcomes of a single behaviour-analysis call."""

    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    SUDDEN_ISSUE = "sudden_issue"
    RISK_TRACKING = "risk_tracking"
    EXEMPTED = "exempted"


class AuditResult:
    """Encapsulates the outcome of one :meth:`ContextualAuditEngine.analyze_behavior` call.

    Args:
        status: Final verdict.
        reason: Human-readable explanation.
        checks: Ordered list of intermediate check results.
    """

    def __init__(
        self,
        status: AuditStatus,
        reason: str,
        checks: List[Dict[str, Any]],
    ) -> None:
        self.status = status
        self.reason = reason
        self.checks = checks

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dictionary (JSON-safe)."""
        return {
            "status": self.status.value,
            "reason": self.reason,
            "checks": self.checks,
        }


# ---------------------------------------------------------------------------
# Risk-data provider interface
# ---------------------------------------------------------------------------

class RiskDataProvider:
    """Abstract interface for external risk data.

    Subclass and override both methods to connect a real data source
    (database, Redis, remote API, etc.).
    """

    def get_risk_user_ids(self) -> List[int]:
        """Return the current list of high-risk user IDs."""
        return []

    def get_report_count(self, room_id: str, window_seconds: int) -> int:
        """Return the number of reports for *room_id* in the last *window_seconds*."""
        return 0


# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------

class MemoryCache:
    """Thread-safe in-memory cache with optional TTL support via *cachetools*.

    Falls back to plain ``dict`` with manual timestamp expiry when
    *cachetools* is not installed.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        if _CACHETOOLS_OK:
            self._risk: Any = TTLCache(maxsize=1000, ttl=300)
            self._reports: Any = TTLCache(maxsize=5000, ttl=60)
        else:
            self._risk: Dict[str, Any] = {}
            self._reports: Dict[str, Any] = {}
            self._ts: Dict[str, float] = {}

    # -- risk list -----------------------------------------------------------

    def get_risk_list(self) -> List[int]:
        """Return the cached high-risk user ID list."""
        with self._lock:
            if _CACHETOOLS_OK:
                return self._risk.get("risk_list", [])
            if time.time() - self._ts.get("risk_list", 0) > 300:
                return []
            return self._risk.get("risk_list", [])

    def set_risk_list(self, risk_list: List[int]) -> None:
        """Update the cached high-risk user ID list."""
        with self._lock:
            self._risk["risk_list"] = risk_list
            if not _CACHETOOLS_OK:
                self._ts["risk_list"] = time.time()

    # -- report counts -------------------------------------------------------

    def get_report_count(self, room_id: str, window: int) -> int:
        """Return the cached report count for *room_id*."""
        key = f"r_{room_id}_{window}"
        with self._lock:
            if _CACHETOOLS_OK:
                return self._reports.get(key, 0)
            if time.time() - self._ts.get(key, 0) > 60:
                return 0

    def set_report_count(self, room_id: str, window: int, count: int) -> None:
        """Update the cached report count for *room_id*."""
        key = f"r_{room_id}_{window}"
        with self._lock:
            self._reports[key] = count
            if not _CACHETOOLS_OK:
                self._ts[key] = time.time()


# ---------------------------------------------------------------------------
# Audit engine
# ---------------------------------------------------------------------------

class ContextualAuditEngine:
    """Multi-dimensional behaviour analysis engine.

    Args:
        provider: External risk-data source.
        cache: Optional shared cache instance.
        risk_refresh_interval: Seconds between risk-list refreshes.
    """

    def __init__(
        self,
        provider: RiskDataProvider,
        cache: Optional[MemoryCache] = None,
        risk_refresh_interval: int = 300,
    ) -> None:
        self._provider = provider
        self._cache = cache or MemoryCache()
        self._risk_refresh_interval = risk_refresh_interval
        self._last_risk_refresh: float = 0.0
        self._lock = threading.RLock()

    def _refresh_risk_list_if_needed(self) -> None:
        """Refresh the risk list from the provider if the TTL has expired."""
        now = time.time()
        with self._lock:
            if now - self._last_risk_refresh < self._risk_refresh_interval:
                return
            try:
                risk_ids = self._provider.get_risk_user_ids()
                self._cache.set_risk_list(risk_ids)
                self._last_risk_refresh = now
                logger.debug("Risk list refreshed: %d entries", len(risk_ids))
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Failed to refresh risk list: %s", exc)

    def _is_risk_user(self, user_id: Optional[int]) -> bool:
        """Return True if *user_id* is on the risk list."""
        if user_id is None:
            return False
        self._refresh_risk_list_if_needed()
        return user_id in self._cache.get_risk_list()

    def analyze_behavior(
        self,
        user_id: Optional[int],
        room_id: str,
        dwell_seconds: float,
        report_window: int = 300,
        suspicious_threshold: int = 3,
        risk_dwell_threshold: float = 1800.0,
        normal_dwell_threshold: float = 600.0,
        exemption_checker: Optional[Callable[[str], bool]] = None,
    ) -> AuditResult:
        """Analyse one user/room observation and return an :class:`AuditResult`."""
        checks: List[Dict[str, Any]] = []

        if exemption_checker is not None:
            try:
                if exemption_checker(room_id):
                    checks.append({"check": "exemption", "result": "exempted"})
                    return AuditResult(AuditStatus.EXEMPTED, "Room is exempted.", checks)
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Exemption checker raised: %s", exc)

        is_risk = self._is_risk_user(user_id)
        checks.append({"check": "risk_user", "result": is_risk})
        if is_risk and dwell_seconds >= risk_dwell_threshold:
            return AuditResult(
                AuditStatus.RISK_TRACKING,
                f"Risk user exceeded dwell threshold ({dwell_seconds:.0f}s).",
                checks,
            )

        try:
            report_count = self._provider.get_report_count(room_id, report_window)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Report count fetch failed: %s", exc)
            report_count = self._cache.get_report_count(room_id, report_window)
        else:
            self._cache.set_report_count(room_id, report_window, report_count)

        checks.append({"check": "report_count", "value": report_count})
        if report_count >= suspicious_threshold:
            return AuditResult(
                AuditStatus.SUSPICIOUS,
                f"Report count {report_count} >= threshold {suspicious_threshold}.",
                checks,
            )

        checks.append({"check": "dwell_seconds", "value": dwell_seconds})
        if dwell_seconds >= normal_dwell_threshold:
            return AuditResult(
                AuditStatus.SUDDEN_ISSUE,
                f"Dwell time {dwell_seconds:.0f}s >= threshold {normal_dwell_threshold:.0f}s.",
                checks,
            )

        return AuditResult(AuditStatus.NORMAL, "No anomaly detected.", checks)
