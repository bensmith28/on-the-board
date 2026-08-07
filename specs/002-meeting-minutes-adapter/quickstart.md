# Quickstart Validation Guide: Meeting Minutes & Agendas Adapter

## Prerequisites

- Python 3.11+
- Docker Compose (for PostgreSQL)
- Playwright browsers installed: `playwright install chromium`
- PostgreSQL instance with `ingested_records` and `sources_registry` tables (from Phase 1.1 migration)

## Setup

### 1. Database Setup

Ensure the `ingested_records` and `sources_registry` tables exist. Run the Phase 1.1 migration:

```bash
# From repository root
psql "$DATABASE_URL" -f migrations/001_create_ingested_records.sql
psql "$DATABASE_URL" -f migrations/002_create_sources_registry.sql
```

### 2. Seed sources_registry

Insert the initial configuration for the Town of Victor Agenda Center:

```sql
INSERT INTO sources_registry (name, source_type, locality, config, status)
VALUES (
  'Town of Victor Agenda Center',
  'meeting_minutes',
  'Victor, NY',
  '{"base_url": "https://www.townofvictorny.gov/AgendaCenter", "boards": ["Town Board", "Planning Board", "ZBA"], "selectors": {"year_dropdown": "#year-select", "document_links": ".document-list a", "board_indicator": ".board-name"}, "max_days_back": 365, "consecutive_skip_threshold": 5}',
  'active'
);
```

### 3. Environment Variables

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/on_the_board"
```

---

## Validation Scenarios

### Scenario 1: Manual Adapter Execution (Single PDF)

**Goal**: Verify the adapter downloads and parses at least one PDF and inserts a valid record into `ingested_records`.

**Steps**:

```bash
# Run the adapter manually (first run, no last_run_timestamp)
python -m adapters.meeting_minutes.adapter \
  --locality "Victor, NY" \
  --config '{"base_url": "https://www.townofvictorny.gov/AgendaCenter", "boards": ["Town Board"], "selectors": {"year_dropdown": "#year-select", "document_links": ".document-list a", "board_indicator": ".board-name"}, "max_days_back": 30, "consecutive_skip_threshold": 5}' \
  --last-run-timestamp null
```

**Expected Outcome**:
- Adapter outputs structured JSON logs to stdout (per-document entries + run summary)
- At least one record appears in `ingested_records`
- The record has non-empty `source_url` and `point_of_origin` (verifiable via: `SELECT source_url, point_of_origin FROM ingested_records LIMIT 1;`)
- The record's `payload` contains all five required keys: `title`, `content_summary`, `raw_text`, `metadata`, `related_resources` (see [IngestionResult contract](./contracts/ingestion-result.md))

**Verification**:
```sql
-- Check record count
SELECT COUNT(*) FROM ingested_records WHERE source_type = 'meeting_minutes';

-- Check evidence mapping compliance
SELECT id, source_url, point_of_origin FROM ingested_records WHERE source_type = 'meeting_minutes' LIMIT 1;

-- Check payload structure
SELECT payload->>'title' AS title, 
       jsonb_object_keys(payload) AS payload_keys 
FROM ingested_records WHERE source_type = 'meeting_minutes' LIMIT 1;
```

---

### Scenario 2: Incremental Ingestion (Second Run)

**Goal**: Verify the adapter skips already-recorded documents on a second run.

**Steps**:

```bash
# Get the last_run timestamp from sources_registry
LAST_RUN=$(psql -t -c "SELECT last_run FROM sources_registry WHERE source_type = 'meeting_minutes' LIMIT 1;" | tr -d ' ')

# Run again with the same timestamp
python -m adapters.meeting_minutes.adapter \
  --locality "Victor, NY" \
  --config '{"base_url": "https://www.townofvictorny.gov/AgendaCenter", "boards": ["Town Board"], "selectors": {"year_dropdown": "#year-select", "document_links": ".document-list a", "board_indicator": ".board-name"}, "max_days_back": 30, "consecutive_skip_threshold": 5}' \
  --last-run-timestamp "$LAST_RUN"
```

**Expected Outcome**:
- Adapter logs show 0 documents ingested (all skipped as already recorded)
- `sources_registry.last_run` is updated to the new timestamp
- Record count in `ingested_records` is unchanged from Scenario 1

**Verification**:
```sql
-- Check last_run was updated
SELECT last_run FROM sources_registry WHERE source_type = 'meeting_minutes';

-- Check record count unchanged
SELECT COUNT(*) FROM ingested_records WHERE source_type = 'meeting_minutes';
```

---

### Scenario 3: Evidence Mapping Compliance

**Goal**: Verify every ingested record has non-empty `source_url` and `point_of_origin`.

**Steps**:

```sql
-- Check for any records with empty evidence fields
SELECT id, source_url, point_of_origin 
FROM ingested_records 
WHERE source_type = 'meeting_minutes' 
  AND (source_url IS NULL OR source_url = '' 
       OR point_of_origin IS NULL OR point_of_origin = '');
```

**Expected Outcome**: Zero rows returned (all records have valid evidence mapping).

**Reference**: [Ingestion Policy Mandatory Evidence Mapping](../../docs/ingestion-policy.md) — see [IngestionResult contract](./contracts/ingestion-result.md) for field definitions.

---

### Scenario 4: Error Handling — Transient Failure Retry

**Goal**: Verify transient failures trigger up to 3 retries with exponential backoff.

**Steps**:

```bash
# Simulate transient failure by pointing to a non-existent URL
python -m adapters.meeting_minutes.adapter \
  --locality "Victor, NY" \
  --config '{"base_url": "https://invalid.example.com/AgendaCenter", "boards": ["Town Board"], "selectors": {}, "max_days_back": 30, "consecutive_skip_threshold": 5}' \
  --last-run-timestamp null
```

**Expected Outcome**:
- Adapter logs show retry attempts with increasing delays (1s, 2s, 4s)
- After 3 failed attempts, the run is marked as `transient_failure`
- Structured JSON log entry: `{"status": "transient_failure", "error_type": "network_error", "error_message": "..."}`

**Reference**: [ErrorSignal contract](./contracts/error-signal.md) for retry policy details.

---

### Scenario 5: Error Handling — Permanent Failure (Corrupted PDF)

**Goal**: Verify corrupted/unreadable PDFs are skipped without stopping the pipeline.

**Steps**:

```bash
# Create a test scenario with a corrupted PDF URL
# (This requires a mock server or test fixture with a corrupted PDF)
python -m adapters.meeting_minutes.adapter \
  --locality "Victor, NY" \
  --config '{"base_url": "http://localhost:9999/AgendaCenter", "boards": ["Town Board"], "selectors": {}, "max_days_back": 30, "consecutive_skip_threshold": 5}' \
  --last-run-timestamp null \
  --test-mode corrupted-pdf
```

**Expected Outcome**:
- The corrupted PDF is logged as `permanent_failure` with `error_type: "parsing_error"`
- Other documents in the same run continue to be processed
- The run status is `success` (partial ingestion, not total failure)

**Reference**: [ErrorSignal contract](./contracts/error-signal.md) for permanent_failure behavior.

---

### Scenario 6: Multi-Board Discovery

**Goal**: Verify the adapter discovers documents from at least 3 different boards.

**Steps**:

```bash
python -m adapters.meeting_minutes.adapter \
  --locality "Victor, NY" \
  --config '{"base_url": "https://www.townofvictorny.gov/AgendaCenter", "boards": ["Town Board", "Planning Board", "ZBA"], "selectors": {"year_dropdown": "#year-select", "document_links": ".document-list a", "board_indicator": ".board-name"}, "max_days_back": 30, "consecutive_skip_threshold": 5}' \
  --last-run-timestamp null
```

**Expected Outcome**:
- Records in `ingested_records` have `metadata.board` values for at least 3 different boards
- The run summary log shows documents discovered per board

**Verification**:
```sql
SELECT metadata->>'board' AS board, COUNT(*) 
FROM ingested_records 
WHERE source_type = 'meeting_minutes' 
GROUP BY metadata->>'board';
```

---

### Scenario 7: Performance Constraint

**Goal**: Verify a single adapter run completes within 15 minutes.

**Steps**:

```bash
time python -m adapters.meeting_minutes.adapter \
  --locality "Victor, NY" \
  --config '{"base_url": "https://www.townofvictorny.gov/AgendaCenter", "boards": ["Town Board", "Planning Board", "ZBA"], "selectors": {"year_dropdown": "#year-select", "document_links": ".document-list a", "board_indicator": ".board-name"}, "max_days_back": 365, "consecutive_skip_threshold": 5}' \
  --last-run-timestamp null
```

**Expected Outcome**:
- Total execution time is under 15 minutes (measured by `time` command)
- Run summary log shows total run duration

---

### Scenario 8: Structured JSON Logging

**Goal**: Verify the adapter produces structured JSON logs.

**Steps**:

```bash
python -m adapters.meeting_minutes.adapter \
  --locality "Victor, NY" \
  --config '{"base_url": "https://www.townofvictorny.gov/AgendaCenter", "boards": ["Town Board"], "selectors": {"year_dropdown": "#year-select", "document_links": ".document-list a", "board_indicator": ".board-name"}, "max_days_back": 30, "consecutive_skip_threshold": 5}' \
  --last-run-timestamp null 2>&1 | head -20
```

**Expected Outcome**:
- Each log line is valid JSON
- Per-document entries contain: `title`, `source_url`, `status`, `duration_ms`, and optional `error_details`
- A final run summary entry contains: `documents_discovered`, `documents_ingested`, `documents_skipped`, `documents_failed`, `total_duration_ms`

---

## Troubleshooting

| Issue | Likely Cause | Resolution |
|:---|:---|:---|
| Playwright browser not found | Browsers not installed | Run `playwright install chromium` |
| Connection refused to CivicPlus | Network/firewall issue | Verify outbound HTTPS access to `townofvictorny.gov` |
| CSS selectors return no results | CivicPlus page structure changed | Update selectors in `sources_registry.config` |
| PDF text extraction returns empty | PDF is scanned image (not text-based) | Consider OCR fallback (future enhancement) |
| `last_run` not updating | Adapter failed before completion | Check logs for `transient_failure` or `permanent_failure` entries |
