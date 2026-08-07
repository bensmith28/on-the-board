# Implementation Plan: Meeting Minutes & Agendas Adapter

**Branch**: `002-meeting-minutes-adapter` | **Date**: 2026-08-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

This feature implements the "Type B" adapter for ingesting meeting agendas and minutes from the Town of Victor's CivicPlus Agenda Center. The adapter uses a headless browser (Playwright) to navigate the JavaScript-rendered Agenda Center, discovers PDF documents across multiple boards (Town Board, Planning Board, ZBA, etc.), downloads and parses them (PyMuPDF), and stores structured records in the `ingested_records` table. It supports incremental ingestion via `sources_registry`, implements retry with exponential backoff for transient failures, and produces structured JSON logs for observability.

### Source Material

- **`docs/specifications/adapters/meeting-minutes-agendas-adapter.md`** — Primary adapter spec: target entity, URL, extraction logic, data contract, challenges, error handling
- **`docs/specifications/adapter-orchestration.md`** — `IngestionResult` contract, adapter input/output interface, error signaling, orchestration flow, retry policy
- **`docs/specifications/storage.md`** — `ingested_records` schema, `sources_registry` schema, `IngestionResult` payload contract
- **`docs/specifications/adapter-template.md`** — Adapter specification structure and data contract mapping pattern
- **`docs/specifications/backend-fastapi.md`** — FastAPI backend layer, activity feed endpoints, `ActivityItem` entity
- **`docs/specifications/deployment-infrastructure.md`** — Docker Compose stack, Dramatiq/RQ workers, Caddy proxy, PostgreSQL
- **`docs/research/research-data-ingestion.md`** — Data source categorization, adapter architecture strategy, CivicPlus/Javascript rendering challenges
- **`docs/research/research-data-store.md`** — Hybrid relational + JSONB data modeling, PostgreSQL technology selection
- **`docs/research/research-development.md`** — Spec-driven development methodology, testing strategy, deployment approach
- **`docs/research/research-presentation.md`** — FastAPI + HTMX architecture recommendation
- **`docs/research/research-cost-modeling.md`** — Cost model for single-municipality deployment (Hetzner baseline)
- **`docs/ingestion-policy.md`** — Verifiable Truth standards, Mandatory Evidence Mapping requirements

**Conflicts with source material**: None identified. The adapter spec's data contract, extraction logic, and error handling align with the orchestration, storage, and ingestion policy specifications.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Playwright (headless browser), PyMuPDF/fitz (PDF text extraction), httpx (HTTP client), structlog or python-json-logger (structured JSON logging)

**Storage**: PostgreSQL (via `ingested_records` table and `sources_registry` table established in Phase 1.1)

**Testing**: pytest (unit + integration), pytest-asyncio (async test support), Playwright test runner (browser automation testing)

**Target Platform**: Linux server (Docker container on Hetzner VPS)

**Project Type**: CLI data ingestion adapter (ephemeral Python process, orchestrated by Dramatiq/RQ workers)

**Performance Goals**: Single adapter run (all boards) completes within 15 minutes under normal conditions

**Constraints**: 
- Must handle JavaScript-rendered CivicPlus Agenda Center (requires headless browser)
- PDFs are text-based (not scanned images) — no OCR needed
- Runs must be serialized (one at a time per source)
- Rate limiting on CivicPlus platform — randomized delays required
- 3 retries with exponential backoff for transient failures
- Stop scanning after 5 consecutive already-recorded documents OR 365 days into the past

**Scale/Scope**: Targets ~5-6 boards across multiple years; estimated hundreds to low thousands of PDF files; low-KB to low-MB PDFs each

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Verifiable Truth**: ✅ Compliant — Every ingested record includes mandatory `source_url` and `point_of_origin` fields per the Ingestion Policy. The adapter preserves raw text and content summaries directly from source PDFs without fabrication.

**Maintenance Efficiency**: ✅ Compliant — Fully automated ingestion (tier 1). Incremental ingestion via `last_run_timestamp` minimizes redundant processing. No manual intervention required for normal operation.

**Geographic Adaptability**: ✅ Compliant — `locality` and `config` (base_url, selectors, boards) are parameterized. The adapter's `config` column in `sources_registry` is municipality-agnostic. Victor, NY is the initial locality, not a hardcoded constant.

**Single Source of Truth**: ✅ Compliant — `docs/specifications/` folder will be updated to match the implementation before completion.

*GATE: Before marking implementation as COMPLETED, verify that the `docs/specifications/` folder is updated to reflect the current implementation (Single Source of Truth).*

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
adapters/
├── meeting_minutes/
│   ├── __init__.py
│   ├── adapter.py          # Main adapter entry point
│   ├── browser.py          # Playwright browser automation (navigation, year traversal)
│   ├── pdf_parser.py       # PyMuPDF text extraction and date/title parsing
│   ├── models.py           # Data classes: IngestionResult, ErrorSignal, DocumentInfo
│   └── config.py           # Adapter configuration (sources_registry config schema)
└── shared/
    ├── logging.py          # Structured JSON logging utilities
    └── retry.py            # Exponential backoff retry decorator
tests/
├── adapters/
│   └── meeting_minutes/
│       ├── test_browser.py     # Browser navigation tests (mocked)
│       ├── test_pdf_parser.py  # PDF parsing unit tests
│       ├── test_adapter.py     # Integration tests (mocked HTTP/DB)
│       └── test_incremental.py # Incremental ingestion tests
└── conftest.py
```

**Structure Decision**: The adapter lives under `adapters/meeting_minutes/` as a self-contained module with its own entry point, browser automation, PDF parsing, and data models. Shared utilities (logging, retry) live in `adapters/shared/`. Tests mirror the source structure under `tests/adapters/meeting_minutes/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
