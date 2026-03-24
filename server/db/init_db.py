# -*- coding: utf-8 -*-
"""
Database initialisation script.

Usage (from repo root)::

    python server/db/init_db.py

Steps
-----
1. Add project root to sys.path.
2. Create all tables (idempotent -- safe to re-run).
3. Seed default accounts for every role if they do not exist.

Author : AHDUNYI
Version: 9.1.0
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from passlib.context import CryptContext
except ImportError:
    print('[ERROR] passlib is not installed.  Run: pip install "passlib[bcrypt]"')
    sys.exit(1)

from sqlalchemy.orm import Session  # noqa: E402

from server.constants.roles import UserRole  # noqa: E402
from server.core.database import Base, SessionLocal, engine  # noqa: E402
from server.db.models import User  # noqa: E402, F401
from server.db.models_extended import DynamicRole  # noqa: E402

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# (username, full_name, password, role_name, is_superuser)
_SEED_USERS = [
    ("superyu", "xuyu", "melody2026", UserRole.MANAGER.value, True),
    ("leader_am", "早班组长", "ahdunyi2026", UserRole.TEAM_LEADER.value, False),
    ("leader_pm", "中班组长", "ahdunyi2026", UserRole.TEAM_LEADER.value, False),
    ("leader_night", "晚班组长", "ahdunyi2026", UserRole.TEAM_LEADER.value, False),
    ("qa_001", "质检专员001", "ahdunyi2026", UserRole.QA_SPECIALIST.value, False),
    ("auditor_001", "审核员001", "ahdunyi2026", UserRole.AUDITOR.value, False),
    ("auditor_002", "审核员002", "ahdunyi2026", UserRole.AUDITOR.value, False),
    ("auditor_003", "审核员003", "ahdunyi2026", UserRole.AUDITOR.value, False),
    ("auditor_004", "审核员004", "ahdunyi2026", UserRole.AUDITOR.value, False),
    ("auditor_005", "审核员005", "ahdunyi2026", UserRole.AUDITOR.value, False),
]


def create_tables() -> None:
    """Create all ORM-mapped tables (idempotent)."""
    Base.metadata.create_all(bind=engine)
    print("[OK] Table structure synchronised.")


def seed_users(db: Session) -> None:
    """Insert seed accounts if they do not already exist."""
    for username, full_name, password, role_name, is_superuser in _SEED_USERS:
        # Look up the dynamic role by name
        dynamic_role = (
            db.query(DynamicRole).filter(DynamicRole.name == role_name).first()
        )
        if dynamic_role is None:
            print(
                f"[WARN] DynamicRole '{role_name}' not found -- skipping '{username}'."
            )
            print("       Run init_dynamic_roles.py first to seed roles.")
            continue

        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"[SKIP] '{username}' already exists.")
            continue

        user = User(
            username=username,
            full_name=full_name,
            hashed_password=_pwd_ctx.hash(password),
            role_id=dynamic_role.id,
            is_superuser=is_superuser,
            is_active=True,
        )
        db.add(user)
        print(f"[ADD]  '{username}'  role={role_name}  role_id={dynamic_role.id}")
    db.commit()
    print("[OK] Seed users committed.")


def main() -> None:
    """Entry point: create tables then seed data."""
    print("=" * 52)
    print(" AHDUNYI Terminal PRO -- DB Init v9.1.0")
    print("=" * 52)

    print("\n[STEP 1] Synchronising table structure...")
    create_tables()

    print("\n[STEP 2] Seeding user accounts...")
    db: Session = SessionLocal()
    try:
        seed_users(db)
    finally:
        db.close()

    print("\n[DONE] Database initialisation complete.")
    print("=" * 52)


if __name__ == "__main__":
    main()
