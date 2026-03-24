# -*- coding: utf-8 -*-
"""
Users API router.

Endpoints
---------
GET    /api/users/active                   -- List active users (optional role filter)
GET    /api/users/all                      -- List ALL users including inactive
POST   /api/users/                         -- Create a new user (manager only)
GET    /api/users/{user_id}                -- Get single user detail
PUT    /api/users/{user_id}                -- Update user profile / role
PUT    /api/users/{user_id}/role           -- Update a user role only
PUT    /api/users/{user_id}/status         -- Toggle active/inactive
POST   /api/users/{user_id}/reset-password -- Reset password
DELETE /api/users/{user_id}               -- Delete user

Author : xvyu
Version: 1.0.0
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from server.api.permissions import _get_current_user
from server.constants.permissions import Permission
from server.constants.roles import UserRole
from server.core.database import get_db
from server.db.models import User
from server.db.models_extended import DynamicRole
from server.schemas import (
    ActiveUsersResponse,
    OkResponse,
    UserCreate,
    UserOut,
    UserPasswordReset,
    UserRoleUpdate,
    UserUpdate,
)

router = APIRouter(prefix="/api/users", tags=["users"])

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _require_permission(current_user: User, perm: str, db: Session) -> None:
    """Raise 403 if current_user does not hold perm."""
    # Get user's role with permissions
    role = db.query(DynamicRole).filter(DynamicRole.id == current_user.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User role not found."
        )

    # Get active permission codes for the role
    permission_codes = {perm.code for perm in role.permissions if perm.is_active}

    if perm not in permission_codes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: '{perm}' required.",
        )


@router.get("/active", response_model=ActiveUsersResponse)
def list_active_users(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> ActiveUsersResponse:
    """Return all active users, optionally filtered by role."""
    try:
        q = db.query(User).filter(User.is_active.is_(True))
        if role:
            q = q.filter(User.role == role)
        users = q.order_by(User.id).all()
        return ActiveUsersResponse(
            users=[UserOut.model_validate(u) for u in users],
            count=len(users),
            filter_role=role or "",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to query users: {exc}"
        ) from exc


@router.get("/all", response_model=ActiveUsersResponse)
def list_all_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> ActiveUsersResponse:
    """Return ALL users including inactive. Manager only."""
    _require_permission(current_user, Permission.ACTION_UPDATE_ROLE, db)
    try:
        q = db.query(User)
        if role:
            q = q.filter(User.role == role)
        if is_active is not None:
            q = q.filter(User.is_active.is_(is_active))
        users = q.order_by(User.id).all()
        return ActiveUsersResponse(
            users=[UserOut.model_validate(u) for u in users],
            count=len(users),
            filter_role=role or "",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to query users: {exc}"
        ) from exc


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> UserOut:
    """Create a new user account. Requires action:update_role."""
    _require_permission(current_user, Permission.ACTION_UPDATE_ROLE, db)
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(
            status_code=409, detail=f"Username '{body.username}' already exists."
        )
    try:
        new_user = User(
            username=body.username,
            full_name=body.full_name,
            email=body.email,
            hashed_password=_pwd_context.hash(body.password),
            role=body.role,
            is_active=body.is_active,
            is_superuser=False,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return UserOut.model_validate(new_user)
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create user: {exc}"
        ) from exc


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> UserOut:
    """Return a single user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserOut.model_validate(user)


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> UserOut:
    """Update user profile fields and/or role. Requires action:update_role."""
    _require_permission(current_user, Permission.ACTION_UPDATE_ROLE, db)
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    if (
        target.id == current_user.id
        and body.role
        and body.role != current_user.role.name
    ):
        raise HTTPException(status_code=400, detail="Cannot change your own role.")
    try:
        if body.full_name is not None:
            target.full_name = body.full_name
        if body.email is not None:
            target.email = body.email
        if body.role is not None:
            target.role = body.role  # type: ignore[assignment]
        if body.is_active is not None:
            target.is_active = body.is_active
        db.commit()
        db.refresh(target)
        return UserOut.model_validate(target)
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update user: {exc}"
        ) from exc


@router.put("/{user_id}/role", response_model=OkResponse)
def update_user_role(
    user_id: int,
    body: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> OkResponse:
    """Update a user role only. Requires action:update_role."""
    _require_permission(current_user, Permission.ACTION_UPDATE_ROLE, db)
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    valid_roles = {r.value for r in UserRole}
    if body.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role '{body.role}'.")
    try:
        target.role = body.role  # type: ignore[assignment]
        db.commit()
        return OkResponse(
            message=f"User {target.username} role updated to '{body.role}'."
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update role: {exc}"
        ) from exc


@router.put("/{user_id}/status", response_model=OkResponse)
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> OkResponse:
    """Toggle a user active/inactive status. Requires action:update_role."""
    _require_permission(current_user, Permission.ACTION_UPDATE_ROLE, db)
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="Cannot change your own active status."
        )
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    try:
        target.is_active = not target.is_active
        db.commit()
        action = "activated" if target.is_active else "deactivated"
        return OkResponse(message=f"User {target.username} {action}.")
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to toggle status: {exc}"
        ) from exc


@router.post("/{user_id}/reset-password", response_model=OkResponse)
def reset_user_password(
    user_id: int,
    body: UserPasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> OkResponse:
    """Reset a user password. Requires action:update_role."""
    _require_permission(current_user, Permission.ACTION_UPDATE_ROLE, db)
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    try:
        target.hashed_password = _pwd_context.hash(body.new_password)
        db.commit()
        return OkResponse(message=f"Password for '{target.username}' has been reset.")
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to reset password: {exc}"
        ) from exc


@router.delete("/{user_id}", response_model=OkResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> OkResponse:
    """Permanently delete a user. Requires action:update_role."""
    _require_permission(current_user, Permission.ACTION_UPDATE_ROLE, db)
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account.")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    try:
        db.delete(target)
        db.commit()
        return OkResponse(message=f"User '{target.username}' permanently deleted.")
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete user: {exc}"
        ) from exc
