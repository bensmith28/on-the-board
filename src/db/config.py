import os

from sqlmodel import create_engine, SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def get_database_url() -> str:
    """Parse DATABASE_URL from environment variables.

    Supports both a full DATABASE_URL and individual connection params.
    Falls back to a local development default.
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    user = os.environ.get("POSTGRES_USER", "otb")
    password = os.environ.get("POSTGRES_PASSWORD", "otb_dev")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "on_the_board")

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


def get_sync_database_url() -> str:
    """Return a synchronous database URL by converting asyncpg to psycopg2."""
    async_url = get_database_url()
    return async_url.replace("postgresql+asyncpg://", "postgresql://")


# Async engine for use with SQLModel async sessions (lazy)
_db_url = None
_async_engine = None
_sync_db_url = None
_sync_engine = None


def get_db_url() -> str:
    global _db_url
    if _db_url is None:
        _db_url = get_database_url()
    return _db_url


def get_async_engine():
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(get_db_url(), echo=False)
    return _async_engine


def get_sync_db_url() -> str:
    global _sync_db_url
    if _sync_db_url is None:
        _sync_db_url = get_sync_database_url()
    return _sync_db_url


def get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(get_sync_db_url(), echo=False)
    return _sync_engine


# Backwards-compatible aliases
db_url = None
async_engine = None
sync_db_url = None
sync_engine = None


def create_db_tables() -> None:
    """Create all SQLModel tables in the database (sync)."""
    SQLModel.metadata.create_all(sync_engine)
