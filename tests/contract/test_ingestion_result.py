"""Tests for IngestionResult Pydantic model enforcement of VR-001 through VR-007."""

import pytest
from datetime import datetime

from src.adapters.base import IngestionResult


def _valid_kwargs() -> dict:
    return {
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


def test_valid_ingestion_result_constructs():
    """A valid IngestionResult should construct without error."""
    result = IngestionResult(**_valid_kwargs())
    assert result.source_type == "meeting_minutes"
    assert result.payload["title"] == "Test Title"


def test_source_type_empty_raises():
    with pytest.raises(Exception):
        IngestionResult(**{**_valid_kwargs(), "source_type": ""})


def test_source_type_whitespace_raises():
    with pytest.raises(Exception):
        IngestionResult(**{**_valid_kwargs(), "source_type": "   "})


def test_locality_empty_raises():
    with pytest.raises(Exception):
        IngestionResult(**{**_valid_kwargs(), "locality": ""})


def test_source_url_empty_raises():
    with pytest.raises(Exception):
        IngestionResult(**{**_valid_kwargs(), "source_url": ""})


def test_point_of_origin_empty_raises():
    with pytest.raises(Exception):
        IngestionResult(**{**_valid_kwargs(), "point_of_origin": ""})


def test_payload_missing_required_keys_raises():
    kwargs = _valid_kwargs()
    del kwargs["payload"]["title"]
    with pytest.raises(Exception):
        IngestionResult(**kwargs)


def test_payload_title_empty_raises():
    kwargs = _valid_kwargs()
    kwargs["payload"]["title"] = ""
    with pytest.raises(Exception):
        IngestionResult(**kwargs)


def test_payload_content_summary_empty_raises():
    kwargs = _valid_kwargs()
    kwargs["payload"]["content_summary"] = ""
    with pytest.raises(Exception):
        IngestionResult(**kwargs)


def test_payload_raw_text_empty_raises():
    kwargs = _valid_kwargs()
    kwargs["payload"]["raw_text"] = ""
    with pytest.raises(Exception):
        IngestionResult(**kwargs)


def test_payload_metadata_none_raises():
    kwargs = _valid_kwargs()
    kwargs["payload"]["metadata"] = None
    with pytest.raises(Exception):
        IngestionResult(**kwargs)


def test_payload_related_resources_none_raises():
    kwargs = _valid_kwargs()
    kwargs["payload"]["related_resources"] = None
    with pytest.raises(Exception):
        IngestionResult(**kwargs)


def test_payload_metadata_not_dict_raises():
    kwargs = _valid_kwargs()
    kwargs["payload"]["metadata"] = "not a dict"
    with pytest.raises(Exception):
        IngestionResult(**kwargs)


def test_payload_related_resources_not_list_raises():
    kwargs = _valid_kwargs()
    kwargs["payload"]["related_resources"] = "not a list"
    with pytest.raises(Exception):
        IngestionResult(**kwargs)
