# -*- coding: utf-8 -*-
"""
Database engine and session factory.

Configuration
-------------
Set ``DATABASE_URL`` in ``server/.env``::

    DATABASE_URL="mysql+pymysql://user:pass@host:3306/ahdunyi_pro_db?charset=utf8mb4"

Usage
-----
In FastAPI dependency injection::

    from server.core.database import get_db

    @app.get("/example")
    def example(db: Session = Depends(get_db)):
        ...
"""
import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Load .env from server/ directory (one level up from this file)
_ENV_FILE = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_FILE, override=False)

DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://ahdunyi_superyu:changeme@127.0.0.1:3306/ahdunyi_pro_db?charset=utf8mb4",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # detect stale connections
    pool_recycle=1800,        # recycle every 30 min (avoid MySQL 8h timeout)
    pool_size=10,
    max_overflow=20,
    echo=False,               # set True for SQL debug output
)

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session.

    Ensures the session is always closed after the request,
    even if an exception occurs.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
