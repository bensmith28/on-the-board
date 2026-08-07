# Contract: IngestionResult (Adapter Output)

## Purpose

Defines the standardized output contract that all adapters must produce. This contract populates the `ingested_records` table's `payload` column.

## Schema

### IngestionResult

```json
{
  "title": "<non-empty string>",
  "content_summary": "<non-empty string>",
  "raw_text": "<non-empty string>",
  "metadata": {
    "board": "<non-empty string>",
    "agenda_link": "<valid URL>"
  },
   "related_resources": [
     {
       "source_url": "<non-empty valid URL>",
       "point_of_origin": "<non-empty string>"
     }
   ],
   "extraction_timestamp": "<ISO 8601 UTC timestamp>"
}
```

## Field Definitions

| Field | Type | Required | Constraints |
|:---|:---|:---|:---|
| `title` | String | Yes | Non-empty; human-readable; e.g., "Town Board Agenda - July 27, 2026" |
| `content_summary` | String | Yes | Non-empty; brief text excerpt from the parsed PDF |
| `raw_text` | String | Yes | Non-empty; full unformatted text extracted from the PDF |
| `metadata` | Object | Yes | Must contain `board` (non-empty string) and `agenda_link` (valid URL) |
| `related_resources` | Array | Yes | Non-empty; each element must contain `source_url` (non-empty valid URL) and `point_of_origin` (non-empty string) |
| `extraction_timestamp` | String | Yes | ISO 8601 UTC timestamp of when data was extracted from the source PDF |

## Validation Rules (VR-001 through VR-007)

1. **VR-001**: `title` is present and non-empty
2. **VR-002**: `content_summary` is present and non-empty
3. **VR-003**: `raw_text` is present and non-empty
4. **VR-004**: `metadata` is a valid JSON object
5. **VR-005**: `metadata.board` is present and non-empty
6. **VR-006**: `metadata.agenda_link` is a valid URL
7. **VR-007**: `related_resources` is a non-empty array; each element has non-empty `source_url` and `point_of_origin`
8. **VR-008**: `extraction_timestamp` is present and is a valid ISO 8601 UTC timestamp

## Mandatory Evidence Mapping

Per the Ingestion Policy, every record MUST satisfy:
- **`source_url`**: The exact link where the document link was found in the Agenda Center list (from `related_resources[0].source_url`)
- **`point_of_origin`**: The PDF filename or date-based identifier (from `related_resources[0].point_of_origin`)

## Rejection Behavior

Records failing any validation rule MUST be:
1. Rejected (not written to `ingested_records`)
2. Logged with the specific failed rule (e.g., `{"level": "error", "rule": "VR-001", "error": "title is empty"}`)
