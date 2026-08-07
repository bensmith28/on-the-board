# Feature Specification: Foundational Data Layer

**Feature Number**: 001
**Short Name**: foundational-data-layer
**Created**: 2026-08-06
**Phase**: 1.1 — The Core Pipeline
**Status**: Draft

## Clarifications

### Session 2026-08-06

- Q: What PostgreSQL version to target? → A: Latest stable (18.x)

### Session 2026-08-07

- Q: What is the UPSERT conflict key for `ingested_records`? → A: `source_url` + `point_of_origin`

## 1. Overview

This feature establishes the persistent storage layer for the `on-the-board` platform. It implements PostgreSQL with the `pgvector` extension as the "Hybrid Repository," providing both structured metadata management and flexible storage for unstructured, variable-schema content from diverse municipal data sources. This layer is the foundation upon which all adapter ingestion, backend API serving, and future search capabilities are built.

The primary goal is to validate the data lifecycle by defining the schema, data contracts, and verification procedures needed to support the most complex initial data source: Meeting Minutes.

### Source Material

This specification was derived from the following source documents:

- **`docs/specifications/storage.md`** — Core schema (`ingested_records`, `sources_registry`), JSONB payload contract, layer interactions.
- **`docs/specifications/adapter-orchestration.md`** — `sources_registry` usage, `IngestionResult` contract, UPSERT flow, adapter input/output contracts.
- **`docs/specifications/backend-fastapi.md`** — SQLModel entity definitions, `ActivityItem` model.
- **`docs/specifications/adapter-template.md`** — Data contract mapping pattern for adapter-to-storage column and payload mapping.

**Conflicts with source material**: None identified. All schema columns, payload keys, and data contracts in this spec are consistent with the source documents.

## 2. User Scenarios & Testing

### Primary User Scenarios

1. **System Operator verifies data integrity**: After an adapter run, the operator can manually query the database to confirm that ingested records have the correct JSONB payload structure, required evidence fields (source URL, point of origin), and proper metadata.

2. **Developer adds a new adapter**: A developer uses the defined `sources_registry` schema and `IngestionResult` contract to register a new adapter, knowing exactly which columns and payload keys must be populated.

3. **Backend developer consumes stored data**: A developer building the API layer queries `ingested_records` using SQLModel models, retrieving records filtered by source type, locality, and time range.

### Testing Considerations

- Manual SQL queries to verify JSONB payload structure matches the specification
- Validation that all mandatory evidence fields (source URL, point of origin) are present in every record
- Verification that `sources_registry` correctly tracks adapter status and last-run timestamps
- Confirmation that pgvector extension is installed and functional for future semantic search

## 3. Functional Requirements

### 3.1 PostgreSQL Database Setup

- **FR-001**: The system MUST provision a PostgreSQL database instance configured with the `pgvector` extension enabled.
- **FR-002**: The database MUST support JSONB columns for flexible, source-specific payload storage.
- **FR-003**: The database MUST support a VECTOR(1536) column for semantic embedding storage (reserved for Phase 3).
- **FR-004**: Database connection configuration MUST be externalized via environment variables or a configuration file, not hardcoded.

### 3.2 Schema: `ingested_records` Table

- **FR-005**: The `ingested_records` table MUST contain the following columns:
  - `id` (UUID, Primary Key): Unique identifier for each record.
  - `source_type` (VARCHAR(50)): Identifier for the adapter type (e.g., `meeting_minutes`, `press_release`, `town_board_roster`).
  - `locality` (VARCHAR(100)): The municipality/entity the data belongs to (e.g., `Victor, NY`).
  - `timestamp` (TIMESTAMPTZ): The official date/time of the event or publication.
  - `ingestion_timestamp` (TIMESTAMPTZ): When the record was processed and stored.
  - `source_url` (TEXT, Mandatory): The original URL from which the data was extracted.
  - `point_of_origin` (TEXT, Mandatory): Specific page number, section header, or timestamp within the source.
  - `payload` (JSONB): The flexible, source-specific content.
  - `embedding` (VECTOR(1536), NULL, Reserved): Semantic vector column for Phase 3 similarity search.
- **FR-006**: The `ingested_records` table MUST support UPSERT operations keyed on (`source_url`, `point_of_origin`) to handle duplicate ingestion gracefully. On conflict, `payload`, `ingestion_timestamp`, and `timestamp` MUST be updated with the new values; all other columns retain their existing values.
- **FR-007**: Indexes MUST be created on `source_type`, `locality`, `timestamp`, and `source_type + locality` composite for query performance.

### 3.3 Schema: `sources_registry` Table

- **FR-008**: The `sources_registry` table MUST contain the following columns:
  - `id` (UUID, Primary Key): Unique identifier for each registered source.
  - `name` (VARCHAR): Human-readable name (e.g., "Town Board Minutes").
  - `source_type` (VARCHAR(50)): Identifier for the adapter type (e.g., `meeting_minutes`, `press_release`).
  - `locality` (VARCHAR(100)): The municipality/entity the adapter serves (e.g., `Victor, NY`).
  - `config` (JSONB): Adapter-specific configuration parameters (CSS selectors, API endpoints, base URLs, parsing strategy).
  - `last_run` (TIMESTAMPTZ): Timestamp of the last successful execution.
  - `status` (VARCHAR): Current state of the adapter (`active`, `failed`, `maintenance`).
  - `created_at` (TIMESTAMPTZ): Record creation timestamp, defaults to now().
  - `updated_at` (TIMESTAMPTZ): Record last-updated timestamp, defaults to now().
- **FR-009**: The `sources_registry` table MUST serve as the single source of truth for adapter discovery and orchestration.
- **FR-010**: New adapters MUST be registered in `sources_registry` before they can be discovered and executed by the orchestrator.

### 3.4 Data Contract: `IngestionResult`

- **FR-011**: Every adapter MUST produce an `IngestionResult` object containing at least the following payload keys in the JSONB `payload` column:
  - `title` (String): Human-readable title for the record.
  - `content_summary` (String): Brief text excerpt or cleaned version of primary content.
  - `raw_text` (Text): Full, unformatted text extracted from the source.
  - `metadata` (JSONB): Source-specific key-value pairs (e.g., board name, agenda link, channel ID).
  - `related_resources` (Array of Objects): Resource pointers, each with its own `source_url` and `point_of_origin`.
- **FR-012**: The `source_url` and `point_of_origin` fields MUST be validated per VR-001 and VR-002 before any database write. Records failing any validation rule (VR-001 through VR-007) MUST be rejected and logged.
- **FR-013**: The `payload` JSONB structure MUST be validated against the defined contract before ingestion.

### 3.5 SQLModel Entity Definitions

- **FR-014**: SQLModel (or SQLAlchemy) models MUST be defined for both `ingested_records` and `sources_registry` tables.
- **FR-015**: Models MUST enforce type constraints matching the schema definitions in FR-005 and FR-008.
- **FR-016**: The `payload` field MUST be typed as JSONB in the model definition.

### 3.7 Validation Rules

Every `IngestionResult` MUST satisfy the following validation rules before a database write. Rules are enforced by the `validate_ingestion_result()` function in `src/ingestion/validator.py`.

Records failing any rule MUST be rejected with a descriptive error identifying the failed rule.

- **VR-001**: `source_url` MUST be a non-empty, valid URL string.
- **VR-002**: `point_of_origin` MUST be a non-empty string.
- **VR-003**: `payload.title` MUST be a non-empty string.
- **VR-004**: `payload.content_summary` MUST be a non-empty string.
- **VR-005**: `payload.raw_text` MUST be a non-empty string.
- **VR-006**: `payload.metadata` MUST be a non-null object/dict.
- **VR-007**: `payload.related_resources` MUST be a non-null list/array.

### 3.8 Verification Tests

- **FR-017**: A test file `tests/integration/test_verification.py` MUST contain automated checks that verify JSONB payload structure matches the `IngestionResult` specification (all five required keys present).
- **FR-018**: Verification tests MUST confirm that `source_url` and `point_of_origin` are non-empty for every ingested record (via SQL `WHERE source_url IS NULL OR source_url = ''` or equivalent).
- **FR-019**: Verification tests MUST confirm that `sources_registry` entries have valid `status` values (one of: `active`, `failed`, `maintenance`) and non-null `last_run` timestamps for active adapters.

## 4. Success Criteria

### 4.1 Measurable Outcomes

- **SC-001**: PostgreSQL database is provisioned and accessible with `pgvector` extension installed and verified.
- **SC-002**: Both `ingested_records` and `sources_registry` tables are created with all required columns, types, and constraints.
- **SC-003**: A test record inserted into `ingested_records` contains a valid JSONB `payload` with all five required keys (`title`, `content_summary`, `raw_text`, `metadata`, `related_resources`).
- **SC-004**: UPSERT operations on `ingested_records` execute successfully without errors.
- **SC-005**: SQLModel models correctly map to all database columns and enforce type constraints.
- **SC-006**: Manual verification queries confirm that mandatory evidence fields (`source_url`, `point_of_origin`) are present and non-empty for all test records.
- **SC-007**: `sources_registry` correctly tracks at least one adapter entry with valid `status` and `last_run` values.

## 5. Key Entities

### 5.1 `ingested_records`

| Field | Type | Constraints | Description |
|:---|:---|:---|:---|
| `id` | UUID | PK, NOT NULL | Unique record identifier |
| `source_type` | VARCHAR(50) | NOT NULL | Adapter type identifier |
| `locality` | VARCHAR(100) | NOT NULL | Municipality/entity name |
| `timestamp` | TIMESTAMPTZ | NOT NULL | Official event/publication date |
| `ingestion_timestamp` | TIMESTAMPTZ | NOT NULL, defaults to now() | Ingestion time |
| `source_url` | TEXT | NOT NULL | Original source URL |
| `point_of_origin` | TEXT | NOT NULL | Page/section/timestamp within source |
| `payload` | JSONB | NOT NULL | Source-specific content payload |
| `embedding` | VECTOR(n) | NULL (reserved) | Semantic vector (Phase 3) |

### 5.2 `sources_registry`

| Field | Type | Constraints | Description |
|:---|:---|:---|:---|
| `id` | UUID | PK, NOT NULL | Unique registry entry identifier |
| `name` | VARCHAR | NOT NULL | Human-readable adapter name |
| `source_type` | VARCHAR(50) | NOT NULL | Adapter type identifier |
| `locality` | VARCHAR(100) | NOT NULL | Municipality/entity the adapter serves |
| `config` | JSONB | NOT NULL | Adapter configuration parameters |
| `last_run` | TIMESTAMPTZ | NULL | Last successful execution timestamp |
| `status` | VARCHAR | NOT NULL, default `active` | Adapter state (`active`, `failed`, `maintenance`) |
| `created_at` | TIMESTAMPTZ | NOT NULL, default now() | Record creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL, default now() | Record last-updated timestamp |

### 5.3 `IngestionResult` (Data Contract)

| Key | Type | Required | Description |
|:---|:---|:---|:---|
| `title` | String | Yes | Human-readable record title |
| `content_summary` | String | Yes | Brief content excerpt |
| `raw_text` | Text | Yes | Full unformatted extracted text |
| `metadata` | JSONB | Yes | Source-specific key-value pairs |
| `related_resources` | Array[Object] | Yes | Resource pointers with `source_url` and `point_of_origin` |

## 6. Assumptions

- PostgreSQL 18.x (latest stable) is the target database version, compatible with `pgvector` extension.
- The `pgvector` extension will be installed during database provisioning; VECTOR column is reserved but not actively used until Phase 3.
- Victor, NY is the initial locality; the schema design supports multi-locality from the start via the `locality` column.
- Initial adapter registration for the `sources_registry` will be done via SQL migration scripts.
- SQLModel is the chosen ORM layer, consistent with the project's existing specifications.
- Database credentials will be provided via environment variables (`DATABASE_URL` or equivalent).

## 7. Dependencies

- **Phase 1.2 (Meeting Minutes Adapter)**: Requires `ingested_records` table and `IngestionResult` contract to be in place before adapter implementation.
- **Phase 1.3 (Orchestration Engine)**: Requires `sources_registry` table to drive adapter discovery and scheduling.
- **Phase 1.4 (API Layer)**: Requires `ingested_records` schema and SQLModel models to serve data via `/feed` and `/nav/categories` endpoints.
- **External**: PostgreSQL and `pgvector` extension availability.
