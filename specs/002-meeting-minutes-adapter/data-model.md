# Data Model: Meeting Minutes & Agendas Adapter

## Overview

This document defines the data entities and their relationships for the Meeting Minutes & Agendas Adapter (Feature 002). It covers both the adapter's internal data models and the database tables it interacts with.

---

## Entity 1: DocumentInfo (Adapter Internal)

**Purpose**: Represents a single discovered document (PDF) from the Agenda Center during browser traversal.

| Field | Type | Description |
|:---|:---|:---|
| `document_id` | str | Unique identifier derived from the PDF filename or URL slug |
| `title` | str | Human-readable title extracted from the page (e.g., "Town Board Agenda - July 27, 2026") |
| `board_name` | str | Board this document belongs to (e.g., "Town Board", "Planning Board", "ZBA") |
| `pdf_url` | str | Direct URL to the PDF file |
| `source_url` | str | The exact link where the document link was found in the Agenda Center list |
| `point_of_origin` | str | The PDF filename or date-based identifier |
| `meeting_date` | datetime \| None | Extracted meeting date from PDF text (nullable if extraction fails) |
| `year` | int | Year the document belongs to (derived from page context or URL) |
| `document_type` | str | "agenda" or "minutes" (derived from filename or page context) |
| `already_recorded` | bool | Whether this document's URL already exists in `sources_registry` |

**Validation Rules**:
- `pdf_url` must be a valid URL ending in `.pdf`
- `board_name` must be non-empty
- `source_url` must be non-empty (mandatory evidence mapping)
- `point_of_origin` must be non-empty (mandatory evidence mapping)

---

## Entity 2: IngestionResult (Adapter Output)

**Purpose**: The standardized output contract that every adapter must produce. Populates the `ingested_records` table.

| Field | Type | Required | Description |
|:---|:---|:---|:---|
| `title` | str | Yes | Human-readable title (e.g., "Town Board Agenda - July 27, 2026") |
| `content_summary` | str | Yes | Brief text excerpt from the parsed PDF |
| `raw_text` | str | Yes | Full unformatted text extracted from the PDF |
| `metadata` | dict | Yes | Source-specific key-value pairs: `{"board": "Town Board", "agenda_link": "..."}` |
| `related_resources` | list[dict] | Yes | Resource pointers: `[{"source_url": "...", "point_of_origin": "..."}]` |

**Validation Rules** (per Ingestion Policy VR-001 through VR-007):
- All five keys (`title`, `content_summary`, `raw_text`, `metadata`, `related_resources`) MUST be present
- `title` must be non-empty string
- `content_summary` must be non-empty string
- `raw_text` must be non-empty string
- `metadata` must be a valid JSON object
- `metadata.board` must be non-empty
- `metadata.agenda_link` must be a valid URL
- `related_resources` must be a non-empty list
- Each `related_resources` entry must have non-empty `source_url` and `point_of_origin`

**Rejection**: Records failing any validation rule are rejected and logged with the specific failed rule.

---

## Entity 3: ErrorSignal (Adapter Output)

**Purpose**: Standardized error signaling for the orchestrator.

| Field | Type | Description |
|:---|:---|:---|
| `status` | str | `success`, `transient_failure`, or `permanent_failure` |
| `error_message` | str | Descriptive error string for debugging |
| `error_type` | str | Categorization: `network_error`, `parsing_error`, `schema_inconsistency` |

**State Transitions**:
- `success` — Run completed with at least one record ingested
- `transient_failure` — Network/browser error; retryable (up to 3 attempts)
- `permanent_failure` — Parsing/schema error; not retryable for the same record

---

## Entity 4: ingested_records (Database Table)

**Purpose**: Core table storing all ingested records from all adapters.

| Column | Type | Description |
|:---|:---|:---|
| `id` | UUID (PK) | Unique identifier for the record |
| `source_type` | VARCHAR(50) | Always `meeting_minutes` for this adapter |
| `locality` | VARCHAR(100) | Municipality name (e.g., `Victor, NY`) |
| `timestamp` | TIMESTAMPTZ | Official date/time of the event or publication |
| `ingestion_timestamp` | TIMESTAMPTZ | When the record was processed and stored (defaults to now()) |
| `source_url` | TEXT | Original URL from which data was extracted (mandatory per Ingestion Policy) |
| `point_of_origin` | TEXT | Specific page/section/timestamp within the source (mandatory per Ingestion Policy) |
| `payload` | JSONB | Standardized `IngestionResult` payload (title, content_summary, raw_text, metadata, related_resources) |
| `embedding` | VECTOR(n) | Future/Phase 3: semantic vector for similarity search |

**Indexes**:
- `(source_type, locality, timestamp DESC)` — for feed queries
- `(source_url UNIQUE)` — prevents duplicate ingestion
- `GIN(payload)` — for JSONB content queries

---

## Entity 5: sources_registry (Database Table)

**Purpose**: Tracks configuration and status of active adapters for orchestration.

| Column | Type | Description |
|:---|:---|:---|
| `id` | UUID (PK) | Unique identifier |
| `name` | VARCHAR | Human-readable name (e.g., "Town of Victor Agenda Center") |
| `source_type` | VARCHAR(50) | `meeting_minutes` |
| `locality` | VARCHAR(100) | `Victor, NY` |
| `config` | JSONB | `{"base_url": "https://www.townofvictorny.gov/AgendaCenter", "boards": ["Town Board", "Planning Board", "ZBA"], "selectors": {...}}` |
| `last_run` | TIMESTAMPTZ | Updated after each successful run |
| `status` | VARCHAR | `active`, `failed`, or `maintenance` |
| `created_at` | TIMESTAMPTZ | Defaults to now() |
| `updated_at` | TIMESTAMPTZ | Defaults to now() |

**Initial Data** (pre-populated before adapter first run):
```json
{
  "name": "Town of Victor Agenda Center",
  "source_type": "meeting_minutes",
  "locality": "Victor, NY",
  "config": {
    "base_url": "https://www.townofvictorny.gov/AgendaCenter",
    "boards": ["Town Board", "Planning Board", "ZBA"],
    "max_days_back": 365,
    "consecutive_skip_threshold": 5
  },
  "status": "active"
}
```

---

## Entity 6: Adapter Context (Input)

**Purpose**: The execution context passed to the adapter by the orchestrator.

| Field | Type | Description |
|:---|:---|:---|
| `locality` | str | Municipality/entity name (e.g., `Victor, NY`) |
| `config` | dict | Adapter-specific parameters: `base_url`, `selectors`, `max_days_back`, `consecutive_skip_threshold` |
| `last_run_timestamp` | TIMESTAMPTZ | Timestamp of the previous successful execution for incremental ingestion |

**Relationships**:
- Consumed from `sources_registry` by the orchestrator
- Passed to the adapter as input at runtime

---

## Entity Relationships

```
sources_registry
    │
    ├──(config)──► Adapter Context (input)
    │                   │
    │                   ├──(traverse)──► DocumentInfo (discovered)
    │                   │                   │
    │                   │                   └──(parse)──► IngestionResult (output)
    │                   │                                       │
    │                   │                                       └──(write)──► ingested_records
    │                   │
    │                   └──(update)──► last_run (after successful run)
    │
    └──(status)──► ErrorSignal (on failure)
```

## State Diagram: Adapter Run Lifecycle

```
[START]
   │
   ▼
[Read sources_registry] ──► [last_run_timestamp = null] ──► [Scan all documents]
   │                              │
   │(has value)                   │
   ▼                              ▼
[Scan from last_run_timestamp]  [Scan all documents]
   │
   ▼
[Discover documents (most recent → oldest)]
   │
   ▼
[Filter: skip already-recorded URLs]
   │
   ▼
[Download & parse PDFs]
   │
   ├──[Parse failure]──► [Log permanent_failure, skip record]
   │
   └──[Parse success]──► [Validate IngestionResult contract]
                              │
                              ├──[Validation fail]──► [Log rejection with rule]
                              │
                              └──[Validation pass]──► [UPSERT into ingested_records]
                                   │
                                   ▼
                            [5 consecutive skipped? OR 365 days reached?]
                                   │
                                   ├──[Yes]──► [Update last_run_timestamp]
                                   │              │
                                   │              ▼
                                   │         [Log run summary]
                                   │              │
                                   │              ▼
                                   │         [END: status = success]
                                   │
                                   └──[No]──► [Continue scanning]
```
