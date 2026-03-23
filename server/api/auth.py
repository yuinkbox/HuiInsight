# -*- coding: utf-8 -*-
"""
Authentication API router.

Endpoints
---------
POST /api/auth/login           -- Username/password login, returns JWT.
POST /api/auth/change-password -- Change current user's password.

Author : AHDUNYI
Version: 9.0.0
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import bcrypt as _bcrypt_lib
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from server.constants.permissions import (get_permissions_for_role,
                                          get_role_meta)
from server.core.config import config
from server.core.database import get_db
from server.db.models import User
from server.schemas import UserOut

_SECRET_KEY: str = config.auth.jwt_secret_key
_ALGORITHM: str = config.auth.jwt_algorithm
_ACCESS_TOKEN_EXPIRE_MINUTES: int = config.auth.access_token_expire_minutes

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/api/auth", tags=["auth"])


# --------------------------------------------------------------------------
# Pydantic schemas
# --------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str


class AuthUserOut(BaseModel):
    """精简版用户信息，仅用于登录响应 Token 中。完整版请使用 schemas.UserOut。"""

    username: str
    full_name: str
    role: str
    is_superuser: bool

    model_config = {"from_attributes": True}


class RoleMeta(BaseModel):
    """UI display metadata for a role."""

    label: str
    color: str
    dashboard_view: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: AuthUserOut
    permissions: List[str]
    role_meta: RoleMeta


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _create_access_token(
    data: Dict[str, Any],
    expires_minutes: int = _ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    """Create a signed JWT with an expiry claim."""
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload["exp"] = expire
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


def _verify_password(plain: str, hashed: str) -> bool:
    """Verify plain password against bcrypt hash.

    Uses passlib first; falls back to raw bcrypt on compatibility errors
    (passlib 1.7.4 + bcrypt 4.x known issue).

    Args:
        plain:  The plaintext password supplied by the user.
        hashed: The bcrypt hash stored in the database.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        return _pwd_ctx.verify(plain, hashed)
    except Exception:
        pass
    # Fallback: call bcrypt directly, bypassing passlib wrapper
    try:
        plain_bytes = plain.encode("utf-8")
        hash_bytes = hashed.encode("utf-8") if isinstance(hashed, str) else hashed
        return _bcrypt_lib.checkpw(plain_bytes, hash_bytes)
    except Exception:
        return False


def _get_user_or_401(db: Session, username: str) -> User:
    """Fetch user by username or raise HTTP 401."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated.",
        )
    return user


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user and return a 24-hour JWT access token.

    Args:
        body: JSON payload with ``username`` and ``password``.
        db:   Injected database session.

    Returns:
        :class:`TokenResponse` with token, user, permissions, role_meta.

    Raises:
        HTTPException 401: Wrong credentials or inactive account.
    """
    user = _get_user_or_401(db, body.username)

    if not _verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )

    role_value: str = user.role.value

    token = _create_access_token(
        {
            "sub": user.username,
            "role": role_value,
            "is_superuser": user.is_superuser,
        }
    )

    meta = get_role_meta(role_value)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserOut.model_validate(user),
        permissions=get_permissions_for_role(role_value),
        role_meta=RoleMeta(
            label=meta["label"],
            color=meta["color"],
            dashboard_view=meta["dashboard_view"],
        ),
    )


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Change the password for an existing account.

    Args:
        body: JSON payload with ``username``, ``old_password``, ``new_password``.
        db:   Injected database session.

    Returns:
        ``{"message": "Password updated successfully."}``

    Raises:
        HTTPException 401: Wrong old password or inactive account.
        HTTPException 400: New password too short (min 8 chars).
    """
    if len(body.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters.",
        )

    user = _get_user_or_401(db, body.username)

    if not _verify_password(body.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Old password is incorrect.",
        )

    user.hashed_password = _pwd_ctx.hash(body.new_password)
    db.commit()

    return {"message": "Password updated successfully."}
