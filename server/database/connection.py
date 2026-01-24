"""
Database connection management for SQLite
"""

import asyncio
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.orm import DeclarativeBase

from ..config import get_db_path, settings


class Base(DeclarativeBase):
    """Base class for all ORM models"""

    pass


# Global engine and session maker
_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or create the database engine"""
    global _engine

    if _engine is None:
        db_path = get_db_path()
        # Ensure data directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create async engine for SQLite
        db_url = f"sqlite+aiosqlite:///{db_path}"
        _engine = create_async_engine(
            db_url,
            echo=False,  # Set to True for SQL query logging
            connect_args={"check_same_thread": False},
        )

        # Enable WAL mode for better concurrency
        def on_connect(dbapi_conn, connection_record):
            dbapi_conn.execute("PRAGMA journal_mode=WAL")
            dbapi_conn.execute("PRAGMA foreign_keys=ON")
            dbapi_conn.execute("PRAGMA synchronous=NORMAL")
            dbapi_conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout for locks

        from sqlalchemy import event

        event.listen(_engine.sync_engine, "connect", on_connect)

    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get or create the session maker"""
    global _session_maker

    if _session_maker is None:
        engine = get_engine()
        _session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session (for dependency injection)"""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    engine = get_engine()
    async with engine.begin() as conn:
        # Import all models so they're registered with Base
        from server.database import models  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    global _engine, _session_maker

    if _engine:
        await _engine.dispose()
        _engine = None
        _session_maker = None


# Convenience function for raw SQL queries
async def execute_raw_sql(query: str, params: tuple = ()) -> aiosqlite.Cursor:
    """Execute raw SQL query (for complex queries)"""
    db_path = get_db_path()
    conn = await aiosqlite.connect(db_path)
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")
    await conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout

    try:
        cursor = await conn.execute(query, params)
        await conn.commit()
        return cursor
    finally:
        await conn.close()


async def fetch_all_sql(query: str, params: tuple = ()) -> list:
    """Fetch all results from raw SQL query"""
    db_path = get_db_path()
    conn = await aiosqlite.connect(db_path)
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")
    await conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout

    try:
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    finally:
        await conn.close()


async def fetch_one_sql(query: str, params: tuple = ()) -> dict | None:
    """Fetch one result from raw SQL query"""
    db_path = get_db_path()
    conn = await aiosqlite.connect(db_path)
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")
    await conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout

    try:
        cursor = await conn.execute(query, params)
        row = await cursor.fetchone()
        if row is None:
            return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    finally:
        await conn.close()
