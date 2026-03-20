# -*- coding: utf-8 -*-
"""
Permissions API router.

Endpoints
---------
GET /api/auth/permissions  -- Return current user's permission list + role meta.

This endpoint is called by the frontend after a token refresh or page reload
to re-hydrate the Pinia permission store without requiring a full re-login.

Author : AHDUNYI
Version: 9.0.0
"""
import os
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from server.core.database import get_db
from server.db.models import User
from server.constants.permissions import (
    get_permissions_for_role,
    get_role_meta,
    ROLE_META,
)

_SECRET_KEY: str = os.environ.get(
    "JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION_USE_LONG_RANDOM_STRING"
)
_ALGORITHM: str = "HS256"

router = APIRouter(prefix="/api/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)


# --------------------------------------------------------------------------
# Pydantic schemas
# --------------------------------------------------------------------------
class RoleMeta(BaseModel):
    label: str
    color: str
    dashboard_view: str


class PermissionsResponse(BaseModel):
    role: str
    permissions: List[str]
    role_meta: RoleMeta


class AllRolesResponse(BaseModel):
    """Full role catalogue — used by admin UIs to build dynamic dropdowns."""

    roles: List[Dict[str, Any]]


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT, raising 401 on any error."""
    try:
        return jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
        ) from exc


def _get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: resolve Bearer token -> User ORM object."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )
    payload = _decode_token(credentials.credentials)
    username: str = payload.get("sub", "")
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )
    return user


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------
@router.get("/permissions", response_model=PermissionsResponse)
def get_my_permissions(
    current_user: User = Depends(_get_current_user),
) -> PermissionsResponse:
    """Return the permission list for the authenticated user.

    The frontend calls this on every page reload to re-hydrate the Pinia
    permission store, so there is no stale permission data after a role change.

    Args:
        current_user: Resolved from the Bearer JWT by dependency injection.

    Returns:
        :class:`PermissionsResponse` with role, permissions, role_meta.
    """
    role_value = current_user.role.value
    meta = get_role_meta(role_value)
    return PermissionsResponse(
        role=role_value,
        permissions=get_permissions_for_role(role_value),
        role_meta=RoleMeta(
            label=meta["label"],
            color=meta["color"],
            dashboard_view=meta["dashboard_view"],
        ),
    )


@router.get("/roles", response_model=AllRolesResponse)
def get_all_roles() -> AllRolesResponse:
    """Return the full role catalogue with UI metadata.

    Used by admin interfaces to build dynamic role-selection dropdowns
    without any hardcoded role lists in the frontend.

    Returns:
        :class:`AllRolesResponse` with a list of role descriptors.
    """
    roles = [
        {
            "value": role_value,
            "label": meta["label"],
            "color": meta["color"],
            "dashboard_view": meta["dashboard_view"],
        }
        for role_value, meta in ROLE_META.items()
    ]
    return AllRolesResponse(roles=roles)
