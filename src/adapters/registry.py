from typing import Optional

from sqlmodel import Session, select

from src.db.config import sync_engine
from src.db.models.source_registry import SourceRegistry


class AdapterNotFoundError(Exception):
    """Raised when a requested adapter is not found in the registry."""

    def __init__(self, source_type: str, locality: Optional[str] = None):
        msg = f"Adapter not found: source_type={source_type}"
        if locality:
            msg += f", locality={locality}"
        super().__init__(msg)
        self.source_type = source_type
        self.locality = locality


def get_active_adapters(session: Session) -> list[SourceRegistry]:
    """Query sources_registry for all active adapters.

    Returns all registry entries where status = 'active'.
    """
    stmt = select(SourceRegistry).where(SourceRegistry.status == "active")
    return session.exec(stmt).all()


def get_adapter_by_type(
    session: Session, source_type: str, locality: Optional[str] = None
) -> SourceRegistry:
    """Look up a single active adapter by source_type (and optionally locality).

    Raises AdapterNotFoundError if no matching active adapter exists.
    """
    stmt = select(SourceRegistry).where(
        SourceRegistry.source_type == source_type,
        SourceRegistry.status == "active",
    )
    if locality:
        stmt = stmt.where(SourceRegistry.locality == locality)

    result = session.exec(stmt).first()
    if result is None:
        raise AdapterNotFoundError(source_type, locality)
    return result


def register_adapter(
    session: Session,
    name: str,
    source_type: str,
    locality: str,
    config: dict,
) -> SourceRegistry:
    """Insert or update an adapter registry entry.

    Uses ON CONFLICT (source_type) to upsert.
    """
    adapter = SourceRegistry(
        name=name,
        source_type=source_type,
        locality=locality,
        config=config,
    )

    existing = session.exec(
        select(SourceRegistry).where(SourceRegistry.source_type == source_type)
    ).first()

    if existing:
        existing.name = name
        existing.locality = locality
        existing.config = config
        session.add(existing)
        session.flush()
        return existing
    else:
        session.add(adapter)
        session.flush()
        return adapter
