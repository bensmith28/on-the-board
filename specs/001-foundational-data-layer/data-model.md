# Data Model: Foundational Data Layer

## Overview

This document defines the database schema, SQLModel entity definitions, and data relationships for the Foundational Data Layer. All entities map directly to the functional requirements in `spec.md` and the data contract in `docs/specifications/storage.md`.

## Entity: `ingested_records`

The primary table storing all incoming data from adapters. Uses a hybrid relational + wide JSONB approach.

### Schema

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | UUID | PK, NOT NULL | `gen_random_uuid()` | Unique record identifier |
| `source_type` | VARCHAR(50) | NOT NULL | — | Adapter type identifier (e.g., `meeting_minutes`, `press_release`) |
| `locality` | VARCHAR(100) | NOT NULL | — | Municipality/entity name (e.g., `Victor, NY`) |
| `timestamp` | TIMESTAMPTZ | NOT NULL | — | Official date/time of the event or publication |
| `ingestion_timestamp` | TIMESTAMPTZ | NOT NULL | `now()` | When the record was processed and stored |
| `source_url` | TEXT | NOT NULL | — | Original URL from which data was extracted |
| `point_of_origin` | TEXT | NOT NULL | — | Page number, section header, or timestamp within source |
| `payload` | JSONB | NOT NULL | — | Flexible, source-specific content |
| `embedding` | VECTOR(1536) | NULL | — | Semantic vector (reserved for Phase 3) |

### Indexes

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `idx_ingested_source_type` | `source_type` | B-tree | Filter records by adapter type |
| `idx_ingested_locality` | `locality` | B-tree | Filter records by municipality |
| `idx_ingested_timestamp` | `timestamp` | B-tree | Time-range queries, sorting |
| `idx_ingested_source_type_locality` | `source_type`, `locality` | B-tree composite | Combined filter (primary query pattern) |
| `idx_ingested_upsert_key` | `source_url`, `point_of_origin` | B-tree unique | UPSERT conflict key (FR-006) |

### Payload JSONB Schema

Every `payload` entry MUST contain these keys (per `IngestionResult` contract):

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `title` | String | Yes | Human-readable title for the record |
| `content_summary` | String | Yes | Brief text excerpt or cleaned version of primary content |
| `raw_text` | Text | Yes | Full, unformatted text extracted from the source |
| `metadata` | Object | Yes | Source-specific key-value pairs |
| `related_resources` | Array[Object] | Yes | Resource pointers with `source_url` and `point_of_origin` |

#### `metadata` (per source_type examples)

**Meeting Minutes**:
```json
{
  "board": "Town Board",
  "agenda_link": "https://...",
  "meeting_type": "Regular"
}
```

**Press Release**:
```json
{
  "author": "Town Clerk",
  "department": "Communications"
}
```

#### `related_resources` (structure)

Each object in the array MUST include:
| Key | Type | Description |
|-----|------|-------------|
| `source_url` | String | URL to the resource |
| `point_of_origin` | String | Page/section/timestamp within the resource |
| `title` | String (optional) | Human-readable title |
| `resource_type` | String (optional) | e.g., `pdf`, `video`, `html` |

## Entity: `sources_registry`

Tracks the configuration and status of active adapters.

### Schema

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | UUID | PK, NOT NULL | `gen_random_uuid()` | Unique registry entry identifier |
| `name` | VARCHAR | NOT NULL | — | Human-readable adapter name (e.g., "Town Board Minutes") |
| `source_type` | VARCHAR(50) | NOT NULL, UNIQUE | — | Adapter type identifier (maps to `ingested_records.source_type`) |
| `locality` | VARCHAR(100) | NOT NULL | — | Municipality/entity this adapter serves |
| `config` | JSONB | NOT NULL | — | Adapter-specific configuration (base URL, selectors, strategy) |
| `last_run` | TIMESTAMPTZ | NULL | — | Timestamp of the last successful execution |
| `status` | VARCHAR | NOT NULL | `'active'` | Adapter state (`active`, `failed`, `maintenance`) |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | When the registry entry was created |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | When the registry entry was last updated |

### Indexes

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `idx_sources_type` | `source_type` | B-tree unique | Fast lookup by adapter type |
| `idx_sources_locality` | `locality` | B-tree | Filter adapters by municipality |
| `idx_sources_status` | `status` | B-tree | Discovery of active adapters |

## Entity: `IngestionResult` (Data Contract)

Not a database table — a standardized Python object that all adapters produce.

### Structure

```python
class IngestionResult(BaseModel):
    source_type: str
    locality: str
    timestamp: datetime
    source_url: str
    point_of_origin: str
    payload: dict  # JSONB content (title, content_summary, raw_text, metadata, related_resources)
```

### Validation Rules

| Rule | Field | Constraint |
|------|-------|------------|
| VR-001 | `source_url` | Non-empty string, valid URL format |
| VR-002 | `point_of_origin` | Non-empty string |
| VR-003 | `payload.title` | Non-empty string |
| VR-004 | `payload.content_summary` | Non-empty string |
| VR-005 | `payload.raw_text` | Non-empty string |
| VR-006 | `payload.metadata` | Non-null object |
| VR-007 | `payload.related_resources` | Non-null array |

## Relationships

```
sources_registry (source_type) ──────► (source_type) ingested_records
sources_registry (locality)  ──────► (locality)  ingested_records

ingested_records.payload.metadata ──► (nested JSONB, no FK)
ingested_records.payload.related_resources[].source_url ──► (external URL reference)
```

| Relationship | Type | Description |
|-------------|------|-------------|
| `sources_registry` → `ingested_records` | One-to-Many | One adapter can produce many records |
| `ingested_records.payload` | JSONB embedded | Flexible, no FK constraints on nested keys |

## Migration Plan

### Migration 001: Initial Schema

Creates both tables with all columns, indexes, and constraints.

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ingested_records table
CREATE TABLE ingested_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL,
    locality VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    ingestion_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_url TEXT NOT NULL,
    point_of_origin TEXT NOT NULL,
    payload JSONB NOT NULL,
    embedding VECTOR(1536),
    CONSTRAINT chk_payload_keys CHECK (
        payload ? 'title' AND
        payload ? 'content_summary' AND
        payload ? 'raw_text' AND
        payload ? 'metadata' AND
        payload ? 'related_resources'
    )
);

-- sources_registry table
CREATE TABLE sources_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    locality VARCHAR(100) NOT NULL,
    config JSONB NOT NULL,
    last_run TIMESTAMPTZ,
    status VARCHAR NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE UNIQUE INDEX idx_ingested_upsert_key ON ingested_records (source_url, point_of_origin);
CREATE INDEX idx_ingested_source_type ON ingested_records (source_type);
CREATE INDEX idx_ingested_locality ON ingested_records (locality);
CREATE INDEX idx_ingested_timestamp ON ingested_records (timestamp);
CREATE INDEX idx_ingested_source_type_locality ON ingested_records (source_type, locality);
CREATE UNIQUE INDEX idx_sources_type ON sources_registry (source_type);
CREATE INDEX idx_sources_locality ON sources_registry (locality);
CREATE INDEX idx_sources_status ON sources_registry (status);

-- UPSERT helper function (enforces FR-006 UPSERT behavior)
CREATE OR REPLACE FUNCTION upsert_ingested_record(
    p_source_type VARCHAR, p_locality VARCHAR, p_timestamp TIMESTAMPTZ,
    p_source_url TEXT, p_point_of_origin TEXT, p_payload JSONB
) RETURNS VOID AS $$
BEGIN
    INSERT INTO ingested_records (source_type, locality, timestamp, source_url, point_of_origin, payload, ingestion_timestamp)
    VALUES (p_source_type, p_locality, p_timestamp, p_source_url, p_point_of_origin, p_payload, now())
    ON CONFLICT (source_url, point_of_origin) DO UPDATE SET
        payload = EXCLUDED.payload,
        ingestion_timestamp = EXCLUDED.ingestion_timestamp,
        timestamp = EXCLUDED.timestamp,
        updated_at = now();
END;
$$ LANGUAGE plpgsql;
```
