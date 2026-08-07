"""Tests verifying SQLModel models match database schema columns from data-model.md."""

import uuid
from datetime import datetime

from src.db.models.ingested_record import IngestedRecord
from src.db.models.source_registry import SourceRegistry


# ---- IngestedRecord ----

def test_ingested_record_has_required_fields():
    """IngestedRecord should have all fields from data-model.md."""
    required_fields = {
        "id", "source_type", "locality", "timestamp",
        "ingestion_timestamp", "source_url", "point_of_origin",
        "payload", "embedding",
    }
    model_fields = set(IngestedRecord.model_fields.keys())
    assert required_fields.issubset(model_fields)


def test_ingested_record_default_id_is_uuid():
    """id should default to a UUID."""
    record = IngestedRecord(
        source_type="meeting_minutes",
        locality="Victor, NY",
        timestamp=datetime(2026, 7, 15, 19, 0, 0),
        source_url="https://example.com/test.pdf",
        point_of_origin="Page 1",
        payload={"title": "T", "content_summary": "T", "raw_text": "T", "metadata": {}, "related_resources": []},
    )
    assert isinstance(record.id, uuid.UUID)


def test_ingested_record_embedding_nullable():
    """embedding should default to None."""
    record = IngestedRecord(
        source_type="meeting_minutes",
        locality="Victor, NY",
        timestamp=datetime(2026, 7, 15, 19, 0, 0),
        source_url="https://example.com/test.pdf",
        point_of_origin="Page 1",
        payload={"title": "T", "content_summary": "T", "raw_text": "T", "metadata": {}, "related_resources": []},
    )
    assert record.embedding is None


def test_ingested_record_table_name():
    """IngestedRecord should map to 'ingested_records' table."""
    assert IngestedRecord.__tablename__ == "ingested_records"


# ---- SourceRegistry ----

def test_source_registry_has_required_fields():
    """SourceRegistry should have all fields from data-model.md."""
    required_fields = {
        "id", "name", "source_type", "locality",
        "config", "last_run", "status", "created_at", "updated_at",
    }
    model_fields = set(SourceRegistry.model_fields.keys())
    assert required_fields.issubset(model_fields)


def test_source_registry_default_status():
    """status should default to 'active'."""
    registry = SourceRegistry(
        name="Test Adapter",
        source_type="meeting_minutes",
        locality="Victor, NY",
        config={"base_url": "https://example.com"},
    )
    assert registry.status == "active"


def test_source_registry_default_ids_are_uuid():
    """id should default to a UUID."""
    registry = SourceRegistry(
        name="Test Adapter",
        source_type="meeting_minutes",
        locality="Victor, NY",
        config={"base_url": "https://example.com"},
    )
    assert isinstance(registry.id, uuid.UUID)


def test_source_registry_table_name():
    """SourceRegistry should map to 'sources_registry' table."""
    assert SourceRegistry.__tablename__ == "sources_registry"


def test_source_registry_last_run_nullable():
    """last_run should default to None."""
    registry = SourceRegistry(
        name="Test Adapter",
        source_type="meeting_minutes",
        locality="Victor, NY",
        config={"base_url": "https://example.com"},
    )
    assert registry.last_run is None
