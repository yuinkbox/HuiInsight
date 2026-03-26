# -*- coding: utf-8 -*-
"""
ORM models for the AHDUNYI server.

Tables
------
- users       : Application user accounts
- shift_tasks : Audit task assignments per shift
- action_logs : Full audit trail of every auditor action

Author : xvyu
Version: 1.0.0
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.core.database import Base
from server.db.models_extended import DynamicRole


class User(Base):
    """Application user account."""

    __tablename__ = "users"
    __table_args__ = (
        # unique=True 已内联，此处只保留普通索引避免重复索引
        Index("ix_users_username", "username", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # unique 交由上方 Index 管理，避免 MySQL 产生重复索引
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    full_name: Mapped[str] = mapped_column(
        String(128), nullable=False, server_default=""
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="0"
    )
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dynamic_roles.id"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    email: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False), nullable=True, onupdate=func.now()
    )

    # Relationships
    role: Mapped["DynamicRole"] = relationship("DynamicRole", lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<User id={self.id} username={self.username!r}" f" role_id={self.role_id}>"
        )

    @property
    def role_name(self) -> str:
        """Return the role name string from the related DynamicRole."""
        return self.role.name if self.role else ""

    @property
    def role_display_name(self) -> str:
        """Return the role display name from the related DynamicRole."""
        return self.role.display_name if self.role else ""


class ShiftTask(Base):
    """Audit task assignment for a single shift."""

    __tablename__ = "shift_tasks"
    __table_args__ = (
        Index("ix_shift_tasks_user_date", "user_id", "shift_date"),
        Index("ix_shift_tasks_user_id", "user_id"),
        Index("ix_shift_tasks_date_type", "shift_date", "shift_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    shift_date: Mapped[str] = mapped_column(String(10), nullable=False)
    shift_type: Mapped[str] = mapped_column(String(16), nullable=False)
    task_channel: Mapped[str] = mapped_column(String(16), nullable=False)
    is_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="0"
    )
    reviewed_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    violation_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    work_duration: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False), nullable=True, onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<ShiftTask id={self.id} user_id={self.user_id}"
            f" date={self.shift_date} channel={self.task_channel}>"
        )


class ActionLog(Base):
    """Full audit trail -- one row per user action."""

    __tablename__ = "action_logs"
    __table_args__ = (
        Index("ix_action_logs_timestamp", "timestamp"),
        Index("ix_action_logs_user_ts", "user_id", "timestamp"),
        Index("ix_action_logs_action", "action"),
        Index("ix_action_logs_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[str] = mapped_column(String(64), nullable=False, server_default="")
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    task_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<ActionLog id={self.id} user={self.username!r}"
            f" action={self.action!r}>"
        )


class UsernameChangeRequest(Base):
    """Workflow record for username change requests."""

    __tablename__ = "username_change_requests"
    __table_args__ = (
        Index("ix_ucr_applicant_status", "applicant_user_id", "status"),
        Index("ix_ucr_status_created", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    applicant_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    old_username: Mapped[str] = mapped_column(String(64), nullable=False)
    new_username: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default="pending"
    )
    reviewer_user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    review_comment: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False), nullable=True, onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<UsernameChangeRequest id={self.id} applicant={self.applicant_user_id}"
            f" status={self.status!r} old={self.old_username!r} new={self.new_username!r}>"
        )
