import uuid
from datetime import datetime
from typing import Any, Optional

from sqlmodel import Field, SQLModel, text
from sqlalchemy.dialects.postgresql import JSONB


class SourceRegistry(SQLModel, table=True):
    """SQLModel mapping to the sources_registry table.

    Columns:
        id (UUID, PK, auto-generated)
        name (VARCHAR, NOT NULL)
        source_type (VARCHAR(50), NOT NULL, UNIQUE)
        locality (VARCHAR(100), NOT NULL)
        config (JSONB, NOT NULL)
        last_run (TIMESTAMPTZ, nullable)
        status (VARCHAR, NOT NULL, default 'active')
        created_at (TIMESTAMPTZ, NOT NULL, default now())
        updated_at (TIMESTAMPTZ, NOT NULL, default now())
    """

    __tablename__ = "sources_registry"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(sa_column=text("VARCHAR NOT NULL"))
    source_type: str = Field(sa_column=text("VARCHAR(50) NOT NULL"))
    locality: str = Field(sa_column=text("VARCHAR(100) NOT NULL"))
    config: dict[str, Any] = Field(sa_type=JSONB, nullable=False)
    last_run: Optional[datetime] = Field(
        default=None,
        sa_column=text("TIMESTAMPTZ"),
    )
    status: str = Field(
        default="active",
        sa_column=text("VARCHAR NOT NULL DEFAULT 'active'"),
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=text("TIMESTAMPTZ NOT NULL DEFAULT now()"),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=text("TIMESTAMPTZ NOT NULL DEFAULT now()"),
    )
