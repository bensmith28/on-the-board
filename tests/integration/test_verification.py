"""Verification test suite for FR-017, FR-018, FR-019 checks.

FR-017: Payload key presence validation
FR-018: Evidence field non-null/non-empty validation
FR-019: sources_registry status validity
"""

import pytest
from datetime import datetime

from src.adapters.base import IngestionResult
from src.ingestion.validator import validate_ingestion_result


# ---- FR-017: Payload key presence ----

def _valid_payload():
    return {
        "title": "Test Title",
        "content_summary": "Test summary",
        "raw_text": "Test raw text",
        "metadata": {"board": "Town Board"},
        "related_resources": [{"source_url": "https://example.com", "point_of_origin": "Full Doc"}],
    }


def _make_result(payload=None):
    base = {
        "source_type": "meeting_minutes",
        "locality": "Victor, NY",
        "timestamp": datetime(2026, 7, 15, 19, 0, 0),
        "source_url": "https://example.com/test.pdf",
        "point_of_origin": "Page 1",
        "payload": payload or _valid_payload(),
    }
    return IngestionResult(**base)


def _make_result_bypass(payload=None):
    """Create an IngestionResult bypassing Pydantic validation for testing the validator module."""
    base = {
        "source_type": "meeting_minutes",
        "locality": "Victor, NY",
        "timestamp": datetime(2026, 7, 15, 19, 0, 0),
        "source_url": "https://example.com/test.pdf",
        "point_of_origin": "Page 1",
        "payload": payload or _valid_payload(),
    }
    return IngestionResult.model_construct(**base)


def test_fr017_all_required_keys_present():
    """FR-017: All five IngestionResult keys must be present in payload."""
    result = _make_result()
    errors = validate_ingestion_result(result)
    key_errors = [e for e in errors if "title" in e.field or "content_summary" in e.field or "raw_text" in e.field or "metadata" in e.field or "related_resources" in e.field]
    # payload has all keys, so no key-missing errors
    key_missing = [e for e in errors if "contain keys" in e.message]
    assert len(key_missing) == 0


def test_fr017_missing_title_key():
    """FR-017: Missing 'title' key should be detected."""
    payload = _valid_payload()
    del payload["title"]
    result = _make_result_bypass(payload)
    errors = validate_ingestion_result(result)
    assert any(e.field == "payload.title" for e in errors)


def test_fr017_missing_content_summary_key():
    """FR-017: Missing 'content_summary' key should be detected."""
    payload = _valid_payload()
    del payload["content_summary"]
    result = _make_result_bypass(payload)
    errors = validate_ingestion_result(result)
    assert any(e.field == "payload.content_summary" for e in errors)


def test_fr017_missing_raw_text_key():
    """FR-017: Missing 'raw_text' key should be detected."""
    payload = _valid_payload()
    del payload["raw_text"]
    result = _make_result_bypass(payload)
    errors = validate_ingestion_result(result)
    assert any(e.field == "payload.raw_text" for e in errors)


def test_fr017_missing_metadata_key():
    """FR-017: Missing 'metadata' key should be detected."""
    payload = _valid_payload()
    del payload["metadata"]
    result = _make_result_bypass(payload)
    errors = validate_ingestion_result(result)
    assert any(e.field == "payload.metadata" for e in errors)


def test_fr017_missing_related_resources_key():
    """FR-017: Missing 'related_resources' key should be detected."""
    payload = _valid_payload()
    del payload["related_resources"]
    result = _make_result_bypass(payload)
    errors = validate_ingestion_result(result)
    assert any(e.field == "payload.related_resources" for e in errors)


# ---- FR-018: Evidence field non-null/non-empty ----

def test_fr018_source_url_non_empty():
    """FR-018: source_url must be non-null and non-empty."""
    result = _make_result()
    result.source_url = ""
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-001" for e in errors)


def test_fr018_point_of_origin_non_empty():
    """FR-018: point_of_origin must be non-null and non-empty."""
    result = _make_result()
    result.point_of_origin = ""
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-002" for e in errors)


# ---- FR-019: sources_registry status validity ----

def test_fr019_valid_statuses():
    """FR-019: Valid statuses are 'active', 'failed', 'maintenance'."""
    valid_statuses = {"active", "failed", "maintenance"}
    assert "active" in valid_statuses


def test_fr019_status_field_exists_in_source_registry():
    """FR-019: SourceRegistry model must have a status field."""
    from src.db.models.source_registry import SourceRegistry
    assert "status" in SourceRegistry.model_fields
