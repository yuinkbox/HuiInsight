# -*- coding: utf-8 -*-
"""
ORM models for the AHDUNYI server.

Table structure is aligned with the OpenClaw-initialised ``users`` table.
All timestamps are UTC.  Soft-delete via ``is_active``.
"""
from datetime import datetime
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

    Aligned with OpenClaw schema:
      username, hashed_password, is_superuser, full_name
    Extended with AHDUNYI fields:
      role, is_active, created_at, updated_at
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
    # OpenClaw compat: full_name (replaces real_name)
    full_name: Mapped[str] = mapped_column(
        String(128), nullable=False, default="", comment="真实姓名"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="bcrypt密码哈希"
    )
    # OpenClaw compat: is_superuser
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否超级管理员"
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
