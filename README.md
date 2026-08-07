# on-the-board — Foundational Data Layer

## Overview

This repository implements the foundational data layer for **on-the-board**: a system for ingesting, storing, and querying municipal data from diverse sources.

## Quick Start

### 1. Environment Setup

```bash
cp .env.example .env
# Edit .env with your database credentials if needed
```

### 2. Start PostgreSQL with pgvector

```bash
docker compose up -d
```

### 3. Apply Schema Migrations

```bash
psql -U otb -d on_the_board -f src/db/migrations/001_initial_schema.sql
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run Tests

```bash
# Unit tests (no database required)
pytest tests/unit/ -v

# Contract tests (Pydantic model validation)
pytest tests/contract/ -v

# Verification tests (FR-017/FR-018/FR-019)
pytest tests/integration/test_verification.py -v

# Integration tests (requires Docker PostgreSQL running)
pytest tests/integration/test_db_insertion.py -v
```

## Project Structure

```
src/
├── db/
│   ├── config.py              # Database connection configuration (env-based)
│   ├── models/
│   │   ├── ingested_record.py # SQLModel model for ingested_records table
│   │   ├── source_registry.py # SQLModel model for sources_registry table
│   │   └── __init__.py
│   └── migrations/
│       └── 001_initial_schema.sql
├── adapters/
│   ├── base.py                # IngestionResult model + BaseAdapter class
│   ├── registry.py            # Adapter registration guard
│   └── __init__.py
└── ingestion/
    ├── validator.py           # IngestionResult validation (VR-001 to VR-007)
    └── __init__.py

tests/
├── unit/
│   ├── test_payload_validation.py
│   ├── test_sqlmodel_models.py
│   └── test_adapter_registry.py
├── integration/
│   ├── test_db_insertion.py
│   └── test_verification.py
└── contract/
    └── test_ingestion_result.py
```

## Key Concepts

### IngestionResult Contract

All adapters produce an `IngestionResult` object with fields: `source_type`, `locality`, `timestamp`, `source_url`, `point_of_origin`, and `payload`. The payload must contain: `title`, `content_summary`, `raw_text`, `metadata`, and `related_resources`.

### UPSERT Behavior

Records are deduplicated on the composite key (`source_url`, `point_of_origin`). Duplicate inserts update the existing record rather than creating a new one.

### Geographic Adaptability

The `locality` column decouples all data from Victor, NY. The schema supports multi-locality from the start.

### Single Source of Truth

The `docs/specifications/` folder reflects the current implementation. See the feature spec at `specs/001-foundational-data-layer/spec.md` for the full feature specification.

## Validation Scenarios

See `specs/001-foundational-data-layer/quickstart.md` for runnable validation scenarios (V-001 through V-007).

## Constitution

This project follows the [on-the-board Constitution](.specify/memory/constitution.md):

- **Verifiable Truth**: Distinguish facts from interpretations; no fabrication
- **Maintenance Efficiency**: Prioritize automation over manual effort
- **Geographic Adaptability**: Design for easy forking to new localities
- **Single Source of Truth**: `docs/specifications/` matches the current implementation
