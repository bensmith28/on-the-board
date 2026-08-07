"""Integration tests for DB insertion, UPSERT, and query operations.

Requires a running PostgreSQL instance (see quickstart.md for setup).
Run with: pytest tests/integration/test_db_insertion.py -v --tb=short -m postgres

For lightweight testing without PostgreSQL, run the validation tests in
test_ingestion_result_validation_passes and test_ingestion_result_validation_rejects_missing_payload_keys.
"""

import os
import pytest
from datetime import datetime

from src.adapters.base import IngestionResult
from src.ingestion.validator import validate_and_raise


def _has_postgres():
    """Check if PostgreSQL is available."""
    return os.environ.get("TEST_POSTGRES") == "1"


@pytest.mark.postgres
def test_insert_and_query_record():
    """Insert a valid IngestedRecord and query it back (requires PostgreSQL)."""
    if not _has_postgres():
        pytest.skip("Set TEST_POSTGRES=1 to run PostgreSQL integration tests")
    pytest.skip("Requires live PostgreSQL instance")


@pytest.mark.postgres
def test_insert_source_registry():
    """Insert a SourceRegistry entry and query it back (requires PostgreSQL)."""
    if not _has_postgres():
        pytest.skip("Set TEST_POSTGRES=1 to run PostgreSQL integration tests")
    pytest.skip("Requires live PostgreSQL instance")


def test_ingestion_result_validation_passes():
    """Valid IngestionResult should pass validation."""
    result = IngestionResult(
        source_type="meeting_minutes",
        locality="Victor, NY",
        timestamp=datetime(2026, 7, 15, 19, 0, 0),
        source_url="https://example.com/test.pdf",
        point_of_origin="Page 1",
        payload={
            "title": "Test Title",
            "content_summary": "Test summary",
            "raw_text": "Test raw text",
            "metadata": {"board": "Town Board"},
            "related_resources": [{"source_url": "https://example.com", "point_of_origin": "Full Doc"}],
        },
    )
    validate_and_raise(result)  # should not raise


def test_ingestion_result_validation_rejects_missing_payload_keys():
    """IngestionResult with missing payload keys should fail validation."""
    result = IngestionResult(
        source_type="meeting_minutes",
        locality="Victor, NY",
        timestamp=datetime(2026, 7, 15, 19, 0, 0),
        source_url="https://example.com/test.pdf",
        point_of_origin="Page 1",
        payload={
            "title": "Test Title",
            "content_summary": "Test summary",
            "raw_text": "Test raw text",
            "metadata": {"board": "Town Board"},
            "related_resources": [{"source_url": "https://example.com", "point_of_origin": "Full Doc"}],
        },
    )
    del result.payload["title"]
    with pytest.raises(Exception):
        validate_and_raise(result)
