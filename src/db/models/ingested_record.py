import uuid
from datetime import datetime
from typing import Any, Optional

from sqlmodel import Field, SQLModel, text
from sqlalchemy.dialects.postgresql import JSONB


class IngestedRecord(SQLModel, table=True):
    """SQLModel mapping to the ingested_records table.

    Columns:
        id (UUID, PK, auto-generated)
        source_type (VARCHAR(50), NOT NULL)
        locality (VARCHAR(100), NOT NULL)
        timestamp (TIMESTAMPTZ, NOT NULL)
        ingestion_timestamp (TIMESTAMPTZ, NOT NULL, default now())
        source_url (TEXT, NOT NULL)
        point_of_origin (TEXT, NOT NULL)
        payload (JSONB, NOT NULL)
        embedding (VECTOR(1536), nullable — reserved for Phase 3)
    """

    __tablename__ = "ingested_records"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    source_type: str = Field(sa_column=text("VARCHAR(50) NOT NULL"))
    locality: str = Field(sa_column=text("VARCHAR(100) NOT NULL"))
    timestamp: datetime = Field(sa_column=text("TIMESTAMPTZ NOT NULL"))
    ingestion_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=text("TIMESTAMPTZ NOT NULL DEFAULT now()"),
    )
    source_url: str = Field(sa_column=text("TEXT NOT NULL"))
    point_of_origin: str = Field(sa_column=text("TEXT NOT NULL"))
    payload: dict[str, Any] = Field(sa_type=JSONB, nullable=False)
    embedding: Optional[bytes] = Field(
        default=None,
        sa_column=text("VECTOR(1536)"),
    )
