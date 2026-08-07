---

description: "Task list for Foundational Data Layer feature implementation"

---

# Tasks: Foundational Data Layer

**Feature Number**: 001
**Branch**: `001-foundational-data-layer`
**Input**: Design documents from `/specs/001-foundational-data-layer/`
**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md
**Tests**: Integration tests for DB insertion (per plan.md) and payload validation unit tests

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root

<!--
  ============================================================================
  Tasks for Feature 001: Foundational Data Layer
  Organized by user story / deliverable phase
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, Docker provisioning, and dependency setup

- [ ] T001 [P] Create project directory structure (src/db/models, src/db/migrations, src/adapters, src/api, src/ingestion, tests/unit, tests/integration, tests/contract)
- [ ] T002 [P] Create Docker Compose file for PostgreSQL 18.x with pgvector at docker-compose.yml
- [ ] T003 [P] Create environment configuration template at .env.example with DATABASE_URL and related vars
- [ ] T004 [P] Create Python requirements file at requirements.txt with FastAPI, SQLModel, Pydantic, asyncpg, pytest dependencies

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core database infrastructure that MUST be complete before any adapter or API work

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Setup PostgreSQL Docker service with pgvector extension in docker-compose.yml (postgres:18 image, vector extension, volume mount, port 5432)
- [ ] T006 Create initial migration SQL script at src/db/migrations/001_initial_schema.sql with ingested_records and sources_registry tables, indexes, and pgvector extension
- [ ] T007 Create database config module at src/db/config.py with env-based connection string parsing (DATABASE_URL from env), async engine setup, and connection pool configuration — satisfies FR-004 (externalized config, no hardcoded credentials)
- [ ] T008 [P] Create SQLModel model for IngestedRecord at src/db/models/ingested_record.py mapping to ingested_records table columns and constraints
- [ ] T009 [P] Create SQLModel model for SourceRegistry at src/db/models/source_registry.py mapping to sources_registry table columns and constraints
- [ ] T010 Create models package init at src/db/models/__init__.py exporting IngestedRecord and SourceRegistry
- [ ] T007b [P] Create adapter registration guard at src/adapters/registry.py with function that queries sources_registry for active adapters and raises if adapter not found — satisfies FR-009/FR-010
- [ ] T024b [P] Add unit test at tests/unit/test_adapter_registry.py for registration guard (valid adapter passes, unregistered adapter raises)

**Checkpoint**: Foundation ready - database provisioning, schema migrations, SQLModel models, and adapter registration guard are in place

---

## Phase 3: User Story 1 - PostgreSQL Provisioning and Schema (Priority: P1)

**Goal**: Database is running with pgvector enabled, both tables created with all columns, indexes, and constraints from data-model.md

**Independent Test**: Run `docker compose up`, apply migrations via psql, verify tables exist with correct schema using `\d ingested_records` and `\d sources_registry`

### Implementation for User Story 1

- [ ] T011 [US1] Create Docker Compose PostgreSQL service with pgvector at docker-compose.yml (postgres:18, POSTGRES_USER=otb, POSTGRES_PASSWORD=otb_dev, POSTGRES_DB=on_the_board, volume persistence)
- [ ] T012 [US1] Create migration 001_initial_schema.sql at src/db/migrations/001_initial_schema.sql with: CREATE EXTENSION vector, ingested_records table (UUID PK, source_type, locality, timestamp, ingestion_timestamp, source_url, point_of_origin, JSONB payload, VECTOR(1536) embedding — reserved for Phase 3), sources_registry table (UUID PK, name, source_type, locality, JSONB config, last_run, status, created_at, updated_at)
- [ ] T013 [US1] Add all required indexes to migration: idx_ingested_upsert_key (unique on source_url + point_of_origin), idx_ingested_source_type, idx_ingested_locality, idx_ingested_timestamp, idx_ingested_source_type_locality, idx_sources_type (unique), idx_sources_locality, idx_sources_status — NOTE: UPSERT behavior enforced via ON CONFLICT (source_url, point_of_origin) in migration 001
- [ ] T014 [US1] Add CHECK constraint on ingested_records.payload to enforce all five IngestionResult keys (title, content_summary, raw_text, metadata, related_resources)

**Checkpoint**: PostgreSQL runs with pgvector, both tables created with full schema, indexes, and payload CHECK constraint

---

## Phase 5: User Story 2 - SQLModel Entity Models (Priority: P2)

**Goal**: SQLModel models for IngestedRecord and SourceRegistry correctly map to database schema with proper types, constraints, and JSONB handling

**Independent Test**: Import models, instantiate with test data, verify field names match DB columns, confirm JSONB payload typing

### Implementation for User Story 2

- [ ] T015 [US2] Create IngestedRecord SQLModel class at src/db/models/ingested_record.py with columns: id (UUID, default gen_random_uuid), source_type (VARCHAR(50)), locality (VARCHAR(100)), timestamp (TIMESTAMPTZ), ingestion_timestamp (TIMESTAMPTZ, default now), source_url (TEXT), point_of_origin (TEXT), payload (JSONB), embedding (VECTOR(1536), nullable — reserved for Phase 3)
- [ ] T016 [US2] Create SourceRegistry SQLModel class at src/db/models/source_registry.py with columns: id (UUID, default gen_random_uuid), name (VARCHAR), source_type (VARCHAR(50)), locality (VARCHAR(100)), config (JSONB), last_run (TIMESTAMPTZ, nullable), status (VARCHAR, default 'active'), created_at (TIMESTAMPTZ, default now), updated_at (TIMESTAMPTZ, default now)
- [ ] T017 [US2] Update src/db/models/__init__.py to export both models and add any shared types or constants
- [ ] T018 [US2] Add SQLModel table metadata (TableClause, __tablename__) to both models matching ingested_records and sources_registry table names

**Checkpoint**: Both SQLModel models correctly map to database schema with all columns, types, and defaults

---

## Phase 6: User Story 3 - IngestionResult Validation (Priority: P3)

**Goal**: A validator module that validates adapter output against the IngestionResult contract before DB writes; invalid payloads are rejected with descriptive errors

**Independent Test**: Pass valid IngestionResult through validator (accepts), pass invalid payloads missing required fields (rejects with errors)

### Implementation for User Story 3

- [ ] T019 [US3] Create IngestionResult Pydantic model at src/adapters/base.py with fields: source_type (str), locality (str), timestamp (datetime), source_url (str), point_of_origin (str), payload (dict with title, content_summary, raw_text, metadata, related_resources)
- [ ] T020 [US3] Create validation module at src/ingestion/validator.py with validate_ingestion_result() function that checks VR-001 through VR-007 rules (defined in spec.md §3.7) (source_url non-empty valid URL, point_of_origin non-empty, payload.title/content_summary/raw_text non-empty, payload.metadata non-null, payload.related_resources non-null)
- [ ] T021 [US3] Create validation error types at src/ingestion/validator.py with custom exception classes for validation failures (e.g., IngestionValidationError) with descriptive error messages per validation rule
- [ ] T022 [US3] Add IngestionResult model to src/adapters/__init__.py exports and base adapter class stub with ingest() method signature returning IngestionResult

**Checkpoint**: IngestionResult contract defined, validator rejects invalid payloads with specific errors, accepts valid payloads

---

## Phase 7: User Story 4 - Verification and Integration Testing (Priority: P4)

**Goal**: Integration test script proving records insert, update (UPSERT on source_url + point_of_origin), and query correctly; manual verification procedures from quickstart.md

**Independent Test**: Run tests/integration/test_db_insertion.py against live Docker PostgreSQL to verify insert, UPSERT, and query operations

### Implementation for User Story 4

- [ ] T023 [US4] Create integration test at tests/integration/test_db_insertion.py that: starts Docker PostgreSQL, applies migrations, inserts test record with valid IngestionResult payload, verifies record exists, performs UPSERT with duplicate source_url+point_of_origin, verifies no duplicate created, queries by source_type and locality
- [ ] T024 [US4] Create unit test at tests/unit/test_payload_validation.py that tests validate_ingestion_result() with valid payload (passes) and invalid payloads missing each required field (fails with appropriate error)
- [ ] T025 [US4] Create contract test at tests/contract/test_ingestion_result.py that validates IngestionResult model enforces all VR-001 through VR-007 rules (defined in spec.md §3.7) via Pydantic validation
- [ ] T026 [US4] Create unit test at tests/unit/test_sqlmodel_models.py that verifies IngestedRecord and SourceRegistry model fields match database schema columns from data-model.md
- [ ] T027a [US4] Create verification test suite at tests/integration/test_verification.py that: runs FR-017 checks (payload key presence), FR-018 checks (evidence field non-null/non-empty), FR-019 checks (sources_registry status validity)

**Checkpoint**: All integration and unit tests pass against live PostgreSQL; IngestionResult contract enforced; docs/specifications/ updated to match implementation (Single Source of Truth)

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cleanup

- [ ] T027 [P] Verify all quickstart.md validation scenarios (V-001 through V-007) pass against the implementation
- [ ] T028 Update docs/specifications/ folder to reflect current implementation (Single Source of Truth per constitution) — must pass before Phase 8 completion
- [ ] T029 Create README or CONTRIBUTING guide with setup instructions for the foundational data layer
- [ ] T030 Add gitignore entries for Python artifacts (.pyc, __pycache__, .env, etc.)

---

### Pre-Completion Gate: Single Source of Truth

Before marking this feature as COMPLETED, verify:

- [ ] Every file in `docs/specifications/` that was referenced by this feature has been reviewed
- [ ] `docs/specifications/storage.md` reflects the final schema (columns, indexes, constraints)
- [ ] `docs/specifications/adapter-orchestration.md` reflects the final IngestionResult contract
- [ ] Any files in `docs/specifications/` that are now obsolete have been archived or removed
- [ ] Diff between `docs/specifications/` and `specs/001-foundational-data-layer/` shows no unmerged changes

**This gate blocks feature completion. Do not proceed without passing all items.**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Adapter Registration Guard (Phase 2)**: Depends on Foundational completion (T007b, T024b)
- **User Stories (Phase 3-7)**: All depend on Foundational + Guard completion
  - User Story 1 (PostgreSQL + Schema) can proceed first
  - User Story 2 (SQLModel models) can start after Foundational phase (Phase 2)
  - User Story 3 (IngestionResult validation) can start after Foundational phase (Phase 2)
  - User Story 4 (Verification tests) depends on User Stories 1-3 completion
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - PostgreSQL provisioning and schema
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - SQLModel models (independent of US1 once DB schema exists)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - IngestionResult validation (independent of US1/US2)
- **User Story 4 (P4)**: Depends on US1 + US2 + US3 + Guard (Phase 2) - Integration tests require all components

### Within Each User Story

- Models before services
- Services before validation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] (T001-T004) can run in parallel
- All Foundational tasks marked [P] (T008, T009) can run in parallel
- Once Foundational phase completes, Adapter Guard (Phase 2) can proceed
- Once Guard completes, User Stories 1-3 can proceed in parallel
- Models within User Story 2 (T015, T016) can run in parallel
- Validation components within User Story 3 (T019-T021) can run in parallel
- Test files within User Story 4 (T023-T026) can run in parallel (after US1-3 complete)

---

## Parallel Example: Foundational Models

```bash
# Launch SQLModel models in parallel (different files, no cross-dependencies):
Task: "Create IngestedRecord SQLModel at src/db/models/ingested_record.py"
Task: "Create SourceRegistry SQLModel at src/db/models/source_registry.py"
```

## Parallel Example: User Story 3 (Phase 6) - Validation

```bash
# Launch IngestionResult model and validator in parallel:
Task: "Create IngestionResult Pydantic model at src/adapters/base.py"
Task: "Create validation module at src/ingestion/validator.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2 (includes Adapter Registration Guard tasks T007b/T024b)
4. Complete Phase 3: User Story 1 (PostgreSQL + Schema)
5. Complete Phase 5: User Story 2 (SQLModel models)
6. Complete Phase 6: User Story 3 (IngestionResult validation)
7. **STOP and VALIDATE**: Apply migrations, run psql verification queries, test validator
8. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Complete Adapter Registration Guard (Phase 2) → Guard verified
3. Add User Story 1 → Apply migrations, verify schema → Demo (PostgreSQL running with correct tables)
4. Add User Story 2 → Import and test SQLModel models → Demo (ORM layer working)
5. Add User Story 3 → Validate IngestionResult contract → Demo (validation pipeline working)
6. Add User Story 4 → Run integration tests → Demo (full pipeline verified)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: Adapter Registration Guard (Phase 2)
   - Developer B: User Story 1 (PostgreSQL + Schema)
   - Developer C: User Story 2 (SQLModel models)
   - Developer D: User Story 3 (IngestionResult validation)
3. All complete → Developer team: User Story 4 (Integration tests)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Constitution compliance: locality column decouples from Victor, NY; Docker Compose enables geographic adaptability; hybrid JSONB approach minimizes maintenance
