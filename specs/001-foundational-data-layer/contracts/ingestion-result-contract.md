# Contract: IngestionResult

## Overview

This contract defines the standardized `IngestionResult` object that all adapters MUST produce. It is the interface between the Adapter layer and the Storage layer.

## Interface

### IngestionResult

All adapters return this object after extracting data from a source.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_type` | `str` | Yes | Adapter type identifier (e.g., `meeting_minutes`) |
| `locality` | `str` | Yes | Municipality/entity name (e.g., `Victor, NY`) |
| `timestamp` | `datetime` | Yes | Official date/time of the event or publication |
| `source_url` | `str` | Yes | Direct link to the original source |
| `point_of_origin` | `str` | Yes | Page number, section header, or timestamp within source |
| `payload` | `dict` | Yes | Source-specific content (see Payload Schema below) |

### Payload Schema

The `payload` field is a JSONB-compatible dict. Every payload MUST contain these keys:

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `title` | `str` | Yes | Human-readable title for the record |
| `content_summary` | `str` | Yes | Brief text excerpt or cleaned version of primary content |
| `raw_text` | `str` | Yes | Full, unformatted text extracted from the source |
| `metadata` | `dict` | Yes | Source-specific key-value pairs |
| `related_resources` | `list[dict]` | Yes | Resource pointers |

### related_resources Structure

Each object in `related_resources` MUST include:

| Key | Type | Description |
|-----|------|-------------|
| `source_url` | `str` | URL to the resource |
| `point_of_origin` | `str` | Page/section/timestamp within the resource |
| `title` | `str \| None` | Human-readable title |
| `resource_type` | `str \| None` | e.g., `pdf`, `video`, `html` |

## Validation

Adapters MUST validate the `IngestionResult` before writing to the database. Invalid results are rejected and logged.

| Rule | Field | Constraint |
|------|-------|------------|
| VR-001 | `source_url` | Non-empty, valid URL |
| VR-002 | `point_of_origin` | Non-empty string |
| VR-003 | `payload.title` | Non-empty string |
| VR-004 | `payload.content_summary` | Non-empty string |
| VR-005 | `payload.raw_text` | Non-empty string |
| VR-006 | `payload.metadata` | Non-null dict |
| VR-007 | `payload.related_resources` | Non-null list |

## Example

```python
result = IngestionResult(
    source_type="meeting_minutes",
    locality="Victor, NY",
    timestamp=datetime(2026, 7, 15, 19, 0, 0),
    source_url="https://townofvictorny.gov/agendas/town-board-2026-07-15.pdf",
    point_of_origin="Page 3",
    payload={
        "title": "Town Board Meeting Minutes — July 15, 2026",
        "content_summary": "Discussion of Q3 budget allocation and zoning amendments...",
        "raw_text": "...full extracted text...",
        "metadata": {
            "board": "Town Board",
            "agenda_link": "https://townofvictorny.gov/agendas/2026-07-15",
            "meeting_type": "Regular"
        },
        "related_resources": [
            {
                "source_url": "https://townofvictorny.gov/agendas/2026-07-15.pdf",
                "point_of_origin": "Full Document",
                "title": "Original PDF",
                "resource_type": "pdf"
            }
        ]
    }
)
```
