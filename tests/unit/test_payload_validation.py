"""Unit tests for validate_ingestion_result().

Tests valid payload (passes) and invalid payloads missing each required field (fails).
"""

import pytest
from datetime import datetime

from src.ingestion.validator import (
    IngestionValidationError,
    validate_ingestion_result,
    validate_and_raise,
)
from src.adapters.base import IngestionResult


def _make_valid_result(**overrides) -> IngestionResult:
    """Return a valid IngestionResult with optional field overrides."""
    base = {
        "source_type": "meeting_minutes",
        "locality": "Victor, NY",
        "timestamp": datetime(2026, 7, 15, 19, 0, 0),
        "source_url": "https://example.com/test.pdf",
        "point_of_origin": "Page 1",
        "payload": {
            "title": "Test Title",
            "content_summary": "Test summary",
            "raw_text": "Test raw text",
            "metadata": {"board": "Town Board"},
            "related_resources": [{"source_url": "https://example.com", "point_of_origin": "Full Doc"}],
        },
    }
    base.update(overrides)
    return IngestionResult(**base)


def _make_invalid_result(**overrides) -> IngestionResult:
    """Return an IngestionResult with bypassed Pydantic validation for testing the validator module."""
    data = {
        "source_type": "meeting_minutes",
        "locality": "Victor, NY",
        "timestamp": datetime(2026, 7, 15, 19, 0, 0),
        "source_url": "https://example.com/test.pdf",
        "point_of_origin": "Page 1",
        "payload": {
            "title": "Test Title",
            "content_summary": "Test summary",
            "raw_text": "Test raw text",
            "metadata": {"board": "Town Board"},
            "related_resources": [{"source_url": "https://example.com", "point_of_origin": "Full Doc"}],
        },
    }
    data.update(overrides)
    return IngestionResult.model_construct(**data)


# ---- Valid payload ----

def test_valid_payload_passes():
    """A fully valid IngestionResult should produce no validation errors."""
    result = _make_valid_result()
    errors = validate_ingestion_result(result)
    assert errors == []


def test_valid_payload_validate_and_raise_no_exception():
    """validate_and_raise should not raise for a valid result."""
    result = _make_valid_result()
    validate_and_raise(result)  # should not raise


# ---- VR-001: source_url ----

def test_empty_source_url_fails():
    result = _make_invalid_result(source_url="")
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-001" for e in errors)


def test_whitespace_source_url_fails():
    result = _make_invalid_result(source_url="   ")
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-001" for e in errors)


# ---- VR-002: point_of_origin ----

def test_empty_point_of_origin_fails():
    result = _make_invalid_result(point_of_origin="")
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-002" for e in errors)


# ---- VR-003: payload.title ----

def test_empty_payload_title_fails():
    result = _make_valid_result()
    result.payload["title"] = ""
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-003" for e in errors)


# ---- VR-004: payload.content_summary ----

def test_empty_payload_content_summary_fails():
    result = _make_valid_result()
    result.payload["content_summary"] = ""
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-004" for e in errors)


# ---- VR-005: payload.raw_text ----

def test_empty_payload_raw_text_fails():
    result = _make_valid_result()
    result.payload["raw_text"] = ""
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-005" for e in errors)


# ---- VR-006: payload.metadata ----

def test_null_payload_metadata_fails():
    result = _make_valid_result()
    result.payload["metadata"] = None
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-006" for e in errors)


def test_non_dict_metadata_fails():
    result = _make_valid_result()
    result.payload["metadata"] = "not a dict"
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-006" for e in errors)


# ---- VR-007: payload.related_resources ----

def test_null_related_resources_fails():
    result = _make_valid_result()
    result.payload["related_resources"] = None
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-007" for e in errors)


def test_non_list_related_resources_fails():
    result = _make_valid_result()
    result.payload["related_resources"] = "not a list"
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-007" for e in errors)


# ---- validate_and_raise raises ----

def test_validate_and_raise_raises_on_invalid():
    result = _make_invalid_result(source_url="")
    with pytest.raises(IngestionValidationError) as exc_info:
        validate_and_raise(result)
    assert len(exc_info.value.errors) > 0


# ---- Missing required keys ----

def test_missing_title_key_fails():
    result = _make_valid_result()
    del result.payload["title"]
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-003" for e in errors)


def test_missing_content_summary_key_fails():
    result = _make_valid_result()
    del result.payload["content_summary"]
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-004" for e in errors)


def test_missing_raw_text_key_fails():
    result = _make_valid_result()
    del result.payload["raw_text"]
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-005" for e in errors)


def test_missing_metadata_key_fails():
    result = _make_valid_result()
    del result.payload["metadata"]
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-006" for e in errors)


def test_missing_related_resources_key_fails():
    result = _make_valid_result()
    del result.payload["related_resources"]
    errors = validate_ingestion_result(result)
    assert any(e.rule == "VR-007" for e in errors)
