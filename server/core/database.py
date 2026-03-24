# -*- coding: utf-8 -*-
"""
Database engine and session factory with multi-environment support.

Configuration
-------------
Uses centralized configuration from server.core.config.

Usage
-----
In FastAPI dependency injection::

    from server.core.database import get_db

    @app.get("/example")
    def example(db: Session = Depends(get_db)):
        ...
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from server.core.config import config

DATABASE_URL: str = config.database.url

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # detect stale connections
    pool_recycle=config.database.pool_recycle,
    pool_size=config.database.pool_size,
    max_overflow=config.database.max_overflow,
    echo=config.database.echo,
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
