"""Validation module for IngestionResult payloads.

Provides validate_ingestion_result() and custom exception types for
validation failures (VR-001 through VR-007).
"""

from dataclasses import dataclass
from typing import Any

from src.adapters.base import IngestionResult


@dataclass
class ValidationError:
    """Describes a single validation failure."""

    rule: str
    field: str
    message: str


class IngestionValidationError(Exception):
    """Raised when an IngestionResult fails validation.

    Collects all ValidationError instances for the failing result.
    """

    def __init__(self, errors: list[ValidationError]):
        self.errors = errors
        messages = [f"[{e.rule}] {e.field}: {e.message}" for e in errors]
        super().__init__("\n".join(messages))


def validate_ingestion_result(result: IngestionResult) -> list[ValidationError]:
    """Validate an IngestionResult against VR-001 through VR-007 rules.

    Returns a list of ValidationError instances (empty if valid).
    Callers should raise IngestionValidationError when the list is non-empty.
    """
    errors: list[ValidationError] = []

    # VR-001: source_url non-empty valid URL
    if not result.source_url or not result.source_url.strip():
        errors.append(ValidationError("VR-001", "source_url", "Must be a non-empty string"))

    # VR-002: point_of_origin non-empty
    if not result.point_of_origin or not result.point_of_origin.strip():
        errors.append(ValidationError("VR-002", "point_of_origin", "Must be a non-empty string"))

    payload = result.payload

    # VR-003: payload.title non-empty
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append(ValidationError("VR-003", "payload.title", "Must be a non-empty string"))

    # VR-004: payload.content_summary non-empty
    cs = payload.get("content_summary")
    if not isinstance(cs, str) or not cs.strip():
        errors.append(ValidationError("VR-004", "payload.content_summary", "Must be a non-empty string"))

    # VR-005: payload.raw_text non-empty
    rt = payload.get("raw_text")
    if not isinstance(rt, str) or not rt.strip():
        errors.append(ValidationError("VR-005", "payload.raw_text", "Must be a non-empty string"))

    # VR-006: payload.metadata non-null
    md = payload.get("metadata")
    if md is None:
        errors.append(ValidationError("VR-006", "payload.metadata", "Must be non-null"))
    elif not isinstance(md, dict):
        errors.append(ValidationError("VR-006", "payload.metadata", "Must be a dict/object"))

    # VR-007: payload.related_resources non-null
    rr = payload.get("related_resources")
    if rr is None:
        errors.append(ValidationError("VR-007", "payload.related_resources", "Must be non-null"))
    elif not isinstance(rr, list):
        errors.append(ValidationError("VR-007", "payload.related_resources", "Must be a list/array"))

    return errors


def validate_and_raise(result: IngestionResult) -> None:
    """Validate an IngestionResult and raise IngestionValidationError on failure.

    Returns None if valid. Raises if any validation rule is violated.
    """
    errors = validate_ingestion_result(result)
    if errors:
        raise IngestionValidationError(errors)
