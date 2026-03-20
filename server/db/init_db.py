# -*- coding: utf-8 -*-
"""
Database initialisation script.

Usage (from any working directory)::

    python server/db/init_db.py

Steps
-----
1. Add project root to sys.path for reliable imports.
2. Create all tables defined in server.db.models (idempotent).
3. Seed a default MANAGER account if it does not exist.

Author : AHDUNYI
Version: 9.0.0
"""
import sys
from pathlib import Path

# -- path setup: ensure repo root is on sys.path regardless of cwd ----------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# -- passlib availability check --------------------------------------------
try:
    from passlib.context import CryptContext  # type: ignore
except ImportError:
    print("[ERROR] passlib is not installed.")
    print('        Run: pip install "passlib[bcrypt]"')
    sys.exit(1)

from sqlalchemy.orm import Session

from server.core.database import Base, engine, SessionLocal
from server.constants.roles import UserRole
from server.db.models import User

# --------------------------------------------------------------------------
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Seed data
_SEED_USERNAME      = "superyu"
_SEED_REAL_NAME     = "xuyu"
_SEED_PLAIN_PASSWORD = "melody2026"
_SEED_ROLE          = UserRole.MANAGER


def create_tables() -> None:
    """Create all ORM-mapped tables (idempotent - safe to run repeatedly)."""
    Base.metadata.create_all(bind=engine)
    print("[OK] Table structure synchronised successfully.")


def seed_superuser(db: Session) -> None:
    """Insert the default MANAGER account if it does not already exist.

    Args:
        db: Active SQLAlchemy session.
    """
    existing = db.query(User).filter(User.username == _SEED_USERNAME).first()
    if existing:
        print(f"[OK] Superuser '{_SEED_USERNAME}' already exists - skipping seed.")
        return

    hashed = _pwd_ctx.hash(_SEED_PLAIN_PASSWORD)
    user = User(
        username=_SEED_USERNAME,
        full_name=_SEED_REAL_NAME,
        hashed_password=hashed,
        role=_SEED_ROLE,
        is_superuser=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"[OK] Superuser created: id={user.id} username='{user.username}' role={user.role.value}")


def main() -> None:
    """Entry point: run table creation then seed data."""
    print("=" * 50)
    print(" AHDUNYI Terminal PRO - DB Init")
    print("=" * 50)

    # Step 1: create tables
    print("\n[STEP 1] Synchronising table structure...")
    create_tables()

    # Step 2: seed superuser
    print("\n[STEP 2] Checking superuser account...")
    db: Session = SessionLocal()
    try:
        seed_superuser(db)
    finally:
        db.close()

    print("\n[DONE] Database initialisation complete.")
    print("=" * 50)


if __name__ == "__main__":
    main()
