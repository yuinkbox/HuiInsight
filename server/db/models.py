# -*- coding: utf-8 -*-
"""
ORM models for the AHDUNYI server.

All tables use:
  - utf8mb4 charset (configured at engine level via DATABASE_URL)
  - UTC timestamps managed automatically by SQLAlchemy
  - Soft-delete via ``is_active`` flag (no hard DELETE in production)
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from server.core.database import Base
from server.constants.roles import UserRole


class User(Base):
    """Application user account.

    Columns
    -------
    id            -- Auto-increment primary key.
    username      -- Login name; unique, indexed.
    real_name     -- Display / audit name (Chinese name supported via utf8mb4).
    hashed_password -- bcrypt hash produced by ``passlib``.
    role          -- One of :class:`~server.constants.roles.UserRole`.
    is_active     -- Soft-delete flag; False = deactivated account.
    created_at    -- Row insertion timestamp (UTC, auto-set).
    updated_at    -- Last update timestamp (UTC, auto-updated).
    """

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_username", "username"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="主键"
    )
    username: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, comment="登录用户名"
    )
    real_name: Mapped[str] = mapped_column(
        String(128), nullable=False, default="", comment="真实姓名"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="bcrypt密码哈希"
    )
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=UserRole.AUDITOR,
        comment="用户角色",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否启用"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间(UTC)",
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
        comment="最后更新时间(UTC)",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} role={self.role.value}>"
