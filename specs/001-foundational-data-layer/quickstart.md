# Quickstart: Foundational Data Layer Validation

## Overview

This guide provides runnable validation scenarios to prove the Foundational Data Layer works end-to-end. Each scenario is independently verifiable.

## Prerequisites

- Docker and Docker Compose installed
- PostgreSQL 18.x Docker image available (`postgres:18`)
- `pgvector` extension available for PostgreSQL 18
- Python 3.12+ with dependencies installed (`SQLModel`, `asyncpg`, `pydantic`)
- `DATABASE_URL` environment variable set to the PostgreSQL connection string

## Setup

### 1. Start PostgreSQL with pgvector

```bash
docker run -d \
  --name on-the-board-db \
  -e POSTGRES_USER=otb \
  -e POSTGRES_PASSWORD=otb_dev \
  -e POSTGRES_DB=on_the_board \
  -p 5432:5432 \
  -v pg_data:/var/lib/postgresql/data \
  postgres:18
```

### 2. Install pgvector extension

```bash
docker exec -it on-the-board-db psql -U otb -d on_the_board -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3. Run schema migrations

```bash
# Execute migrations/001_initial_schema.sql
psql -U otb -d on_the_board -f src/db/migrations/001_initial_schema.sql
```

## Validation Scenarios

### V-001: Verify Tables Exist with Correct Schema

**Purpose**: Confirm both `ingested_records` and `sources_registry` tables are created with all required columns.

**Steps**:
```bash
# Check ingested_records columns
docker exec on-the-board-db psql -U otb -d on_the_board -c "\d ingested_records"

# Check sources_registry columns
docker exec on-the-board-db psql -U otb -d on_the_board -c "\d sources_registry"
```

**Expected**: Both tables display with all columns from `data-model.md` matching types and constraints. `vector` extension is enabled.

### V-002: Insert a Test Record with Valid Payload

**Purpose**: Verify `ingested_records` accepts a record with a valid `IngestionResult` payload (per `contracts/ingestion-result-contract.md`).

**Steps**:
```bash
docker exec on-the-board-db psql -U otb -d on_the_board -c "
INSERT INTO ingested_records (
    source_type, locality, timestamp, source_url, point_of_origin, payload
) VALUES (
    'meeting_minutes',
    'Victor, NY',
    '2026-07-15 19:00:00+00',
    'https://townofvictorny.gov/agendas/town-board-2026-07-15.pdf',
    'Page 3',
    '{
        \"title\": \"Town Board Meeting Minutes — July 15, 2026\",
        \"content_summary\": \"Discussion of Q3 budget allocation.\",
        \"raw_text\": \"Full extracted text...\",
        \"metadata\": {\"board\": \"Town Board\", \"meeting_type\": \"Regular\"},
        \"related_resources\": [{
            \"source_url\": \"https://townofvictorny.gov/agendas/town-board-2026-07-15.pdf\",
            \"point_of_origin\": \"Full Document\"
        }]
    }'::jsonb
);"
```

**Expected**: Insert succeeds without errors.

**Verify**:
```bash
docker exec on-the-board-db psql -U otb -d on_the_board -c "
SELECT id, source_type, locality, timestamp,
       payload->>'title' as title,
       payload->'metadata' as metadata
FROM ingested_records
WHERE source_type = 'meeting_minutes';"
```

**Expected**: One row returned with correct `title`, `metadata`, and all fields populated.

### V-003: Verify UPSERT on Duplicate (`source_url` + `point_of_origin`)

**Purpose**: Confirm UPSERT correctly updates existing records keyed on (`source_url`, `point_of_origin`) per FR-006.

**Steps**:
```bash
# Insert duplicate record (same source_url + point_of_origin, different payload)
docker exec on-the-board-db psql -U otb -d on_the_board -c "
INSERT INTO ingested_records (
    source_type, locality, timestamp, source_url, point_of_origin, payload
) VALUES (
    'meeting_minutes',
    'Victor, NY',
    '2026-07-15 19:00:00+00',
    'https://townofvictorny.gov/agendas/town-board-2026-07-15.pdf',
    'Page 3',
    '{
        \"title\": \"UPDATED Title\",
        \"content_summary\": \"Updated summary.\",
        \"raw_text\": \"Updated text.\",
        \"metadata\": {\"board\": \"Town Board\"},
        \"related_resources\": []
    }'::jsonb
) ON CONFLICT (source_url, point_of_origin) DO UPDATE SET
    payload = EXCLUDED.payload,
    ingestion_timestamp = now();"
```

**Expected**: No error. Record is updated (not duplicated).

**Verify**:
```bash
docker exec on-the-board-db psql -U otb -d on_the_board -c "
SELECT COUNT(*) FROM ingested_records
WHERE source_url = 'https://townofvictorny.gov/agendas/town-board-2026-07-15.pdf';"
```

**Expected**: `1` (not 2). The `payload->>'title'` should show `UPDATED Title`.

### V-004: Verify Mandatory Evidence Validation (source_url + point_of_origin)

**Purpose**: Confirm that records missing mandatory evidence fields are rejected.

**Steps**:
```bash
# Try inserting without point_of_origin
docker exec on-the-board-db psql -U otb -d on_the_board -c "
INSERT INTO ingested_records (
    source_type, locality, timestamp, source_url, payload
) VALUES (
    'meeting_minutes',
    'Victor, NY',
    '2026-08-01 19:00:00+00',
    'https://example.com/missing.pdf',
    '{\"title\":\"Test\",\"content_summary\":\"Test\",\"raw_text\":\"Test\",\"metadata\":{},\"related_resources\":[]}'::jsonb
);"
```

**Expected**: Error — `point_of_origin` is NOT NULL constraint violation.

### V-005: Verify sources_registry Tracks Adapter Status

**Purpose**: Confirm `sources_registry` correctly stores and reflects adapter configuration.

**Steps**:
```bash
# Insert a test adapter entry
docker exec on-the-board-db psql -U otb -d on_the_board -c "
INSERT INTO sources_registry (name, source_type, locality, config, status)
VALUES (
    'Town Board Minutes',
    'meeting_minutes',
    'Victor, NY',
    '{\"base_url\": \"https://townofvictorny.gov/agendas\", \"strategy\": \"playwright\"}',
    'active'
)
ON CONFLICT (source_type) DO UPDATE SET
    updated_at = now(),
    status = EXCLUDED.status;"
```

**Verify**:
```bash
docker exec on-the-board-db psql -U otb -d on_the_board -c "
SELECT name, source_type, status, config FROM sources_registry
WHERE source_type = 'meeting_minutes';"
```

**Expected**: One row with `status = 'active'` and correct `config` JSON.

### V-006: Verify Query Performance on Indexed Columns

**Purpose**: Confirm indexes support efficient queries on `source_type`, `locality`, and composite filters.

**Steps**:
```bash
docker exec on-the-board-db psql -U otb -d on_the_board -c "
EXPLAIN ANALYZE SELECT * FROM ingested_records
WHERE source_type = 'meeting_minutes' AND locality = 'Victor, NY'
ORDER BY timestamp DESC LIMIT 20;"
```

**Expected**: Query plan uses `idx_ingested_source_type_locality` composite index (Index Scan or Bitmap Index Scan), not a sequential scan.

### V-007: Verify SQLModel Models Map Correctly

**Purpose**: Confirm Python SQLModel models correctly map to database schema.

**Steps**:
```python
# Run from Python REPL or test
from src.db.models import IngestedRecord, SourceRegistry
from sqlmodel import Session, select

# Test model creation
record = IngestedRecord(
    source_type="meeting_minutes",
    locality="Victor, NY",
    timestamp="2026-07-15T19:00:00+00:00",
    source_url="https://example.com/test.pdf",
    point_of_origin="Page 1",
    payload={"title": "Test", "content_summary": "Test", "raw_text": "Test", "metadata": {}, "related_resources": []}
)

# Verify model fields match DB columns
assert record.__fields__.keys() >= {"source_type", "locality", "timestamp", "source_url", "point_of_origin", "payload"}
```

**Expected**: All assertions pass. Model fields match database columns from `data-model.md`.

## Cleanup

```bash
docker stop on-the-board-db && docker rm on-the-board-db
docker volume rm pg_data
```
