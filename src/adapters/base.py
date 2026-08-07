from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


class IngestionResult(BaseModel):
    """Standardized output from all adapters.

    All adapters MUST produce this object after extracting data from a source.
    Validated against VR-001 through VR-007 rules before DB writes.
    """

    source_type: str
    locality: str
    timestamp: datetime
    source_url: str
    point_of_origin: str
    payload: dict[str, Any]

    @field_validator("source_type")
    @classmethod
    def source_type_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source_type must be a non-empty string")
        return v

    @field_validator("locality")
    @classmethod
    def locality_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("locality must be a non-empty string")
        return v

    @field_validator("source_url")
    @classmethod
    def source_url_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source_url must be a non-empty string")
        return v

    @field_validator("point_of_origin")
    @classmethod
    def point_of_origin_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("point_of_origin must be a non-empty string")
        return v

    @field_validator("payload")
    @classmethod
    def payload_must_have_required_keys(cls, v: dict[str, Any]) -> dict[str, Any]:
        required_keys = {"title", "content_summary", "raw_text", "metadata", "related_resources"}
        missing = required_keys - set(v.keys())
        if missing:
            raise ValueError(
                f"payload must contain keys: {', '.join(sorted(missing))}"
            )
        return v

    @field_validator("payload")
    @classmethod
    def payload_title_non_empty(cls, v: dict[str, Any]) -> dict[str, Any]:
        title = v.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("payload.title must be a non-empty string")
        return v

    @field_validator("payload")
    @classmethod
    def payload_content_summary_non_empty(
        cls, v: dict[str, Any]
    ) -> dict[str, Any]:
        cs = v.get("content_summary")
        if not isinstance(cs, str) or not cs.strip():
            raise ValueError("payload.content_summary must be a non-empty string")
        return v

    @field_validator("payload")
    @classmethod
    def payload_raw_text_non_empty(cls, v: dict[str, Any]) -> dict[str, Any]:
        rt = v.get("raw_text")
        if not isinstance(rt, str) or not rt.strip():
            raise ValueError("payload.raw_text must be a non-empty string")
        return v

    @field_validator("payload")
    @classmethod
    def payload_metadata_non_null(cls, v: dict[str, Any]) -> dict[str, Any]:
        md = v.get("metadata")
        if md is None:
            raise ValueError("payload.metadata must be non-null")
        if not isinstance(md, dict):
            raise ValueError("payload.metadata must be a dict")
        return v

    @field_validator("payload")
    @classmethod
    def payload_related_resources_non_null(
        cls, v: dict[str, Any]
    ) -> dict[str, Any]:
        rr = v.get("related_resources")
        if rr is None:
            raise ValueError("payload.related_resources must be non-null")
        if not isinstance(rr, list):
            raise ValueError("payload.related_resources must be a list")
        return v


class BaseAdapter:
    """Base adapter class with ingest() method signature.

    All concrete adapters inherit from this and implement ingest().
    """

    def ingest(self) -> IngestionResult:
        """Extract data and return an IngestionResult.

        Subclasses MUST implement this method.
        """
        raise NotImplementedError
