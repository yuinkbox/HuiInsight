# -*- coding: utf-8 -*-
"""
Client version management API.

Endpoints
---------
GET  /api/client/version        -- Get latest client version info (public, no auth).
POST /api/client/version        -- Update version info (admin only).

Author : xvyu
Version: 1.0.0
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from server.api.permissions import _get_current_user
from server.core.database import get_db
from server.db.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/client", tags=["client"])


# ---------------------------------------------------------------------------
# In-memory version store
# In production: persist to DB or a config file on the server.
# ---------------------------------------------------------------------------

_VERSION_STORE: dict = {
    "latest_version": "1.0.0",
    "min_required_version": "1.0.0",
    "download_url": "http://106.15.32.246:8000/downloads/HuiInsight_Setup_1.0.0.exe",
    "changelog": "\u521d\u59cb\u7248\u672c",
    "force_update": False,
    "release_date": "2026-03-24",
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class VersionInfo(BaseModel):
    """Client version information response."""

    latest_version: str
    min_required_version: str
    download_url: str
    changelog: str
    force_update: bool
    release_date: str


class VersionUpdateRequest(BaseModel):
    """Admin request to update version info."""

    latest_version: str
    min_required_version: Optional[str] = None
    download_url: Optional[str] = None
    changelog: Optional[str] = None
    force_update: Optional[bool] = None
    release_date: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/version", response_model=VersionInfo)
def get_latest_version() -> VersionInfo:
    """Return latest client version info.

    Public endpoint - no authentication required.
    Called by the desktop client on startup to check for updates.

    Returns:
        VersionInfo: Latest version metadata.
    """
    return VersionInfo(**_VERSION_STORE)


@router.post("/version", response_model=VersionInfo)
def update_version_info(
    body: VersionUpdateRequest,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
) -> VersionInfo:
    """Update client version metadata. Admin role required.

    Args:
        body: Fields to update.
        current_user: Resolved from Bearer JWT.
        db: Database session (unused here, reserved for future DB persistence).

    Returns:
        VersionInfo: Updated version metadata.

    Raises:
        HTTPException: 403 if current user is not admin.
    """
    if current_user.role not in ("admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="\u53ea\u6709\u7ba1\u7406\u5458\u53ef\u4ee5\u66f4\u65b0\u7248\u672c\u4fe1\u606f",
        )

    _VERSION_STORE["latest_version"] = body.latest_version
    if body.min_required_version is not None:
        _VERSION_STORE["min_required_version"] = body.min_required_version
    if body.download_url is not None:
        _VERSION_STORE["download_url"] = body.download_url
    if body.changelog is not None:
        _VERSION_STORE["changelog"] = body.changelog
    if body.force_update is not None:
        _VERSION_STORE["force_update"] = body.force_update
    if body.release_date is not None:
        _VERSION_STORE["release_date"] = body.release_date

    logger.info(
        "Version info updated by %s: latest=%s, min_required=%s, force=%s",
        current_user.username,
        _VERSION_STORE["latest_version"],
        _VERSION_STORE["min_required_version"],
        _VERSION_STORE["force_update"],
    )
    return VersionInfo(**_VERSION_STORE)
