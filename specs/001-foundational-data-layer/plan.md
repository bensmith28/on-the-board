# Implementation Plan: Foundational Data Layer

**Branch**: `001-foundational-data-layer` | **Date**: 2026-08-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-foundational-data-layer/spec.md`

## Engineering Goal

At the end of this feature, the following will be **finished and runnable**:

1. **PostgreSQL 18.x with pgvector** — running in Docker, with both `ingested_records` and `sources_registry` tables created via migration scripts.
2. **SQLModel entity models** — Python classes for `IngestedRecord` and `SourceRegistry` that map correctly to the database schema.
3. **IngestionResult validation** — a `validator.py` module that validates adapter output against the `IngestionResult` contract before DB writes; invalid payloads are rejected with errors.
4. **Manual verification procedure** — SQL queries and a Python test script (`tests/integration/test_db_insertion.py`) that prove records insert, update (UPSERT on `source_url` + `point_of_origin`), and query correctly.

**What is NOT in scope**: Adapter implementations (Phase 1.2), orchestration engine (Phase 1.3), and API/presentation layer (Phase 1.4). This feature is the storage layer only — you can run `docker compose up`, apply migrations, insert a test record via psql, and query it back directly.

## Summary

This plan covers the implementation of the foundational data layer for `on-the-board`: provisioning PostgreSQL 18.x with `pgvector`, creating the `ingested_records` and `sources_registry` tables, defining SQLModel entity models, and establishing verification procedures. The primary goal is to validate the data lifecycle for the Meeting Minutes adapter (Phase 1.2) by ensuring the storage layer can correctly receive, store, and serve the `IngestionResult` contract.

### Source Material

This plan was derived from the following source documents:

**Specifications:**
- **`specs/001-foundational-data-layer/spec.md`** — Feature specification: schema, functional requirements, success criteria, UPSERT conflict key (`source_url` + `point_of_origin`), PostgreSQL 18.x target.
- **`docs/specifications/storage.md`** — Core schema (`ingested_records`, `sources_registry`), JSONB payload contract, layer interactions.
- **`docs/specifications/adapter-orchestration.md`** — `sources_registry` usage, `IngestionResult` contract, UPSERT flow, adapter input/output contracts.
- **`docs/specifications/backend-fastapi.md`** — SQLModel entity definitions, `ActivityItem` model, HTMX response contracts.
- **`docs/specifications/adapter-template.md`** — Data contract mapping pattern for adapter-to-storage column and payload mapping.

**Research:**
- **`docs/research/research-data-store.md`** — Data modeling evaluation (Model A: Hybrid Relational + Wide JSONB selected), technology selection (Self-hosted PostgreSQL via Docker Compose on Hetzner), pgvector roadmap alignment.
- **`docs/research/research-data-ingestion.md`** — Adapter architecture strategy, `IngestionResult` contract, data source categorization, prioritization of Meeting Minutes as Phase 1 target.
- **`docs/research/research-data-retention.md`** — Data lifecycle strategy (Aggregator Model), PostgreSQL for metadata, R2 for large files, 10-year archival threshold.
- **`docs/research/research-data-egress.md`** — Open data distribution strategy (Phase 1: research only), data formats (CSV/JSON), Schema.org integration.
- **`docs/research/research-development.md`** — Development methodology (spec-driven), testing strategy (unit/integration/contract/regression), deployment strategy (Docker Compose on Hetzner, litestream backups), monitoring (structured logs + Sentry + health check adapters).
- **`docs/research/research-presentation.md`** — Backend API selection (FastAPI), frontend (HTMX + Tailwind), session-based auth, self-hosted Docker Compose hosting.
- **`docs/research/research-cost-modeling.md`** — Infrastructure cost model (~$6.67/month per municipality on Hetzner CX23 + R2), scaling projections.

**Conflicts with source material**: None identified. All technical decisions in this plan are consistent with the feature spec and research findings.

## Technical Context

**Language/Version**: Python 3.12+ (target; aligned with FastAPI, SQLModel, and adapter ecosystem from `research-development.md` and `research-presentation.md`)

**Primary Dependencies**: FastAPI (backend API), SQLModel (ORM), Pydantic (payload validation), `asyncpg` (async PostgreSQL driver)

**Storage**: PostgreSQL 18.x (latest stable) with `pgvector` extension, self-hosted via Docker Compose on Hetzner (per `research-data-store.md` and `research-development.md`)

**Testing**: pytest (unit), integration tests for adapter→DB→API flow, contract tests for `IngestionResult` payload validation

**Target Platform**: Linux VPS (Hetzner CX23 tier, 2 vCPU / 4GB RAM) via Docker Compose

**Project Type**: Web service (FastAPI backend + HTMX frontend) with background adapter workers

**Performance Goals**: Ingestion operations complete within reasonable time for low-volume municipal data (hundreds to low thousands of PDFs/files per municipality/year); API responses serve HTMX fragments under 200ms p95

**Constraints**: 
- Must support `pgvector` for Phase 3 semantic search (rules out serverless SQLite options)
- Must be forkable with minimal external configuration (rules out managed NoSQL)
- Low-cost target (~$6.67/month per municipality from cost model)
- Victor, NY is initial locality; schema must support multi-locality from start

**Scale/Scope**: Phase 1 targets a single municipality (Victor, NY) with one adapter (Meeting Minutes). Schema designed for multi-locality expansion. Initial data volume: hundreds to low thousands of records per municipality.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

Based on the project's core principles (from `AGENTS.md` and the project constitution):

**Verifiable Truth Principle**:
- ✅ Spec includes mandatory evidence mapping (`source_url`, `point_of_origin`) as non-nullable fields
- ✅ `IngestionResult` payload contract enforces traceability
- ✅ Verification requirements (FR-017 to FR-019) ensure data integrity checks

**Maintenance Efficiency Principle**:
- ✅ Self-hosted PostgreSQL via Docker Compose (lowest maintenance overhead for MVP)
- ✅ Hybrid JSONB approach avoids per-source-type DDL migrations
- ✅ Data retention strategy uses cloud-native lifecycle policies (no custom migration code)
- ✅ Automation hierarchy: Fully automated backups via litestream (Phase 3)

**Geographic Adaptability Principle**:
- ✅ `locality` column in `ingested_records` and `sources_registry` decouples data from Victor, NY
- ✅ Docker Compose deployment enables "one-command" fork to new municipalities
- ✅ No hardcoded municipality names in schema or data contracts
- ✅ `sources_registry.config` JSONB allows per-municipality adapter configuration

**GATE STATUS**: All principles satisfied. No violations requiring complexity tracking.

*GATE: Before marking implementation as COMPLETED, `docs/specifications/` MUST be updated to reflect the current implementation (Single Source of Truth per constitution). This is a blocking gate — implementation cannot be marked complete until this gate passes.*

## Project Structure

### Documentation (this feature)

```text
specs/001-foundational-data-layer/
├── spec.md              # Feature specification
├── plan.md              # This file (implementation plan)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output (validation scenarios)
```

### Source Code (repository root)

```text
src/
├── db/
│   ├── models/          # SQLModel entity definitions (ingested_records, sources_registry)
│   ├── migrations/      # SQL migration scripts for schema creation
│   └── config.py        # Database connection configuration (env-based)
├── adapters/
│   └── base.py          # Base adapter class with IngestionResult contract
├── api/
│   └── routes.py        # FastAPI endpoints (/feed, /nav/categories, /health)
└── ingestion/
    └── validator.py     # IngestionResult payload validation

tests/
├── unit/
│   ├── test_payload_validation.py
│   └── test_sqlmodel_models.py
├── integration/
│   └── test_db_insertion.py
└── contract/
    └── test_ingestion_result.py
```

**Structure Decision**: Single-project structure (`src/` + `tests/`) chosen because this is a monolithic Python application (FastAPI + adapters + workers) without separate frontend build pipeline (HTMX renders server-side).

## Complexity Tracking

> No constitution violations to justify. All design decisions align with core principles.
