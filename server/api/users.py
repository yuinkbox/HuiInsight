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

import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from server.api.permissions import _get_current_user
from server.constants.permissions import Permission
from server.constants.roles import UserRole
from server.core.database import get_db
from server.db.models import ActionLog, User, UsernameChangeRequest
from server.db.models_extended import DynamicRole
from server.schemas import (
    ActiveUsersResponse,
    OkResponse,
    UserCreate,
    UsernameChangeRequestCreate,
    UsernameChangeRequestListResponse,
    UsernameChangeRequestOut,
    UsernameChangeRequestReview,
    UserOut,
    UserPasswordReset,
    UserRoleUpdate,
    UserUpdate,
)

router = APIRouter(prefix="/api/users", tags=["users"])

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{2,32}$")


def _normalize_username(username: str) -> str:
    return str(username or "").strip().lower()


def _validate_username_or_400(username: str) -> str:
    normalized = _normalize_username(username)
    if not _USERNAME_PATTERN.fullmatch(normalized):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must match [a-zA-Z0-9_]{2,32}.",
        )
    return normalized


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
            role_id=body.role_id,
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
        and body.role_id is not None
        and body.role_id != current_user.role_id
    ):
        raise HTTPException(status_code=400, detail="Cannot change your own role.")
    try:
        if body.full_name is not None:
            target.full_name = body.full_name
        if body.email is not None:
            target.email = body.email
        if body.role_id is not None:
            role_obj = db.query(DynamicRole).filter(DynamicRole.id == body.role_id).first()
            if not role_obj:
                raise HTTPException(status_code=400, detail=f"Invalid role_id: {body.role_id}")
            target.role_id = body.role_id
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
    role_obj = db.query(DynamicRole).filter(DynamicRole.id == body.role_id).first()
    if not role_obj:
        raise HTTPException(status_code=400, detail=f"Invalid role_id '{body.role_id}'.")
    try:
        target.role_id = body.role_id
        db.commit()
        return OkResponse(
            message=f"User {target.username} role updated to '{role_obj.name}'."
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


@router.post(
    "/me/username-change-requests",
    response_model=UsernameChangeRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def create_my_username_change_request(
    body: UsernameChangeRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> UsernameChangeRequestOut:
    """Create a username-change request for the current user."""
    new_username = _validate_username_or_400(body.new_username)
    old_username = _normalize_username(current_user.username)

    if new_username == old_username:
        raise HTTPException(
            status_code=400, detail="New username must differ from current username."
        )

    if (
        db.query(User)
        .filter(User.username == new_username, User.id != current_user.id)
        .first()
    ):
        raise HTTPException(
            status_code=409, detail=f"Username '{new_username}' already exists."
        )

    pending_same_name = (
        db.query(UsernameChangeRequest)
        .filter(
            UsernameChangeRequest.new_username == new_username,
            UsernameChangeRequest.status == "pending",
        )
        .first()
    )
    if pending_same_name:
        raise HTTPException(
            status_code=409, detail=f"Username '{new_username}' is pending approval."
        )

    try:
        # supersede previous pending requests from the same applicant
        db.query(UsernameChangeRequest).filter(
            UsernameChangeRequest.applicant_user_id == current_user.id,
            UsernameChangeRequest.status == "pending",
        ).update({"status": "superseded"}, synchronize_session=False)

        req = UsernameChangeRequest(
            applicant_user_id=current_user.id,
            old_username=old_username,
            new_username=new_username,
            reason=(body.reason or "").strip() or None,
            status="pending",
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return UsernameChangeRequestOut.model_validate(req)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create request: {exc}"
        ) from exc


@router.get(
    "/me/username-change-requests", response_model=UsernameChangeRequestListResponse
)
def list_my_username_change_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> UsernameChangeRequestListResponse:
    """List current user's username-change requests."""
    items = (
        db.query(UsernameChangeRequest)
        .filter(UsernameChangeRequest.applicant_user_id == current_user.id)
        .order_by(UsernameChangeRequest.created_at.desc())
        .all()
    )
    return UsernameChangeRequestListResponse(
        items=[UsernameChangeRequestOut.model_validate(i) for i in items],
        total=len(items),
    )


@router.get(
    "/username-change-requests", response_model=UsernameChangeRequestListResponse
)
def list_username_change_requests(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> UsernameChangeRequestListResponse:
    """Manager view: list all username-change requests."""
    _require_permission(current_user, Permission.ACTION_UPDATE_ROLE, db)
    q = db.query(UsernameChangeRequest)
    if status_filter:
        q = q.filter(UsernameChangeRequest.status == status_filter)
    items = q.order_by(UsernameChangeRequest.created_at.desc()).all()
    return UsernameChangeRequestListResponse(
        items=[UsernameChangeRequestOut.model_validate(i) for i in items],
        total=len(items),
    )


@router.post(
    "/username-change-requests/{request_id}/approve", response_model=OkResponse
)
def approve_username_change_request(
    request_id: int,
    body: UsernameChangeRequestReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> OkResponse:
    """Manager approval: apply username change."""
    _require_permission(current_user, Permission.ACTION_UPDATE_ROLE, db)

    req = (
        db.query(UsernameChangeRequest)
        .filter(UsernameChangeRequest.id == request_id)
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
    if req.status != "pending":
        raise HTTPException(
            status_code=400, detail="Only pending requests can be approved."
        )

    applicant = db.query(User).filter(User.id == req.applicant_user_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant user not found.")

    if (
        db.query(User)
        .filter(User.username == req.new_username, User.id != applicant.id)
        .first()
    ):
        raise HTTPException(
            status_code=409, detail=f"Username '{req.new_username}' already exists."
        )

    try:
        old_username = applicant.username
        applicant.username = req.new_username
        req.status = "approved"
        req.reviewer_user_id = current_user.id
        req.review_comment = (body.comment or "").strip() or None
        req.reviewed_at = datetime.now(timezone.utc)

        db.query(UsernameChangeRequest).filter(
            UsernameChangeRequest.applicant_user_id == applicant.id,
            UsernameChangeRequest.status == "pending",
            UsernameChangeRequest.id != req.id,
        ).update({"status": "superseded"}, synchronize_session=False)

        db.add(
            ActionLog(
                user_id=current_user.id,
                username=current_user.username,
                action="approve_username_change",
                details=f"approved user_id={applicant.id} username {old_username} -> {req.new_username}",
                timestamp=datetime.now(timezone.utc),
            )
        )

        db.commit()
        return OkResponse(
            message=f"Username changed: {old_username} -> {req.new_username}"
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to approve request: {exc}"
        ) from exc


@router.post("/username-change-requests/{request_id}/reject", response_model=OkResponse)
def reject_username_change_request(
    request_id: int,
    body: UsernameChangeRequestReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> OkResponse:
    """Manager reject: close request without applying username."""
    _require_permission(current_user, Permission.ACTION_UPDATE_ROLE, db)

    req = (
        db.query(UsernameChangeRequest)
        .filter(UsernameChangeRequest.id == request_id)
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
    if req.status != "pending":
        raise HTTPException(
            status_code=400, detail="Only pending requests can be rejected."
        )

    try:
        req.status = "rejected"
        req.reviewer_user_id = current_user.id
        req.review_comment = (body.comment or "").strip() or None
        req.reviewed_at = datetime.now(timezone.utc)
        db.add(
            ActionLog(
                user_id=current_user.id,
                username=current_user.username,
                action="reject_username_change",
                details=f"rejected request_id={req.id} applicant={req.applicant_user_id} new={req.new_username}",
                timestamp=datetime.now(timezone.utc),
            )
        )
        db.commit()
        return OkResponse(message="Username change request rejected.")
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to reject request: {exc}"
        ) from exc
