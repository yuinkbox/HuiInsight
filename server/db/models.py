# -*- coding: utf-8 -*-
"""
ORM models for the AHDUNYI server.

Tables
------
- users       : Application user accounts
- shift_tasks : Audit task assignments per shift
- action_logs : Full audit trail of every auditor action

Author : AHDUNYI
Version: 9.0.0
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from server.constants.roles import UserRole
from server.core.database import Base


class User(Base):
    """Application user account."""

    __tablename__ = "users"
    __table_args__ = (Index("ix_users_username", "username"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=UserRole.AUDITOR,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, default=""
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<User id={self.id} username={self.username!r}"
            f" role={self.role.value}>"
        )


class ShiftTask(Base):
    """Audit task assignment for a single shift."""

    __tablename__ = "shift_tasks"
    __table_args__ = (
        Index("ix_shift_tasks_user_date", "user_id", "shift_date"),
        Index("ix_shift_tasks_date_type", "shift_date", "shift_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    shift_date: Mapped[str] = mapped_column(String(10), nullable=False)
    shift_type: Mapped[str] = mapped_column(String(16), nullable=False)
    task_channel: Mapped[str] = mapped_column(String(16), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reviewed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    violation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    work_duration: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
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
        Index("ix_action_logs_user_ts", "user_id", "timestamp"),
        Index("ix_action_logs_action", "action"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False, default="")
    task_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<ActionLog id={self.id} user={self.username!r}"
            f" action={self.action!r}>"
        )
