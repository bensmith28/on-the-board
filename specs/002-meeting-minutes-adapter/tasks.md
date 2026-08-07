---

description: "Task list for Meeting Minutes & Agendas Adapter implementation"

---

# Tasks: Meeting Minutes & Agendas Adapter

**Feature Number**: 002
**Input**: Design documents from `/specs/002-meeting-minutes-adapter/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (adapter-context.md, error-signal.md, ingestion-result.md)

**Tests**: Test tasks included in Phase 8 below.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Adapter source: `adapters/meeting_minutes/`
- Shared utilities: `adapters/shared/`
- Tests: `tests/adapters/meeting_minutes/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for the adapter module

- [ ] T001 Create adapter directory structure: `adapters/meeting_minutes/`, `adapters/shared/`, `tests/adapters/meeting_minutes/`
- [ ] T002 Create `adapters/meeting_minutes/__init__.py` with module metadata
- [ ] T003 Create `adapters/__init__.py` and `adapters/shared/__init__.py`
- [ ] T004 Create `pyproject.toml` with dependencies: playwright, pymupdf, httpx, python-json-logger, asyncpg
- [ ] T005 Create `adapters/meeting_minutes/__main__.py` for CLI invocation via `python -m adapters.meeting_minutes`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 [P] Implement shared retry module with decorator in `adapters/shared/retry.py`: configurable attempts (default 3), exponential backoff (1s, 2s, 4s base), randomized jitter, retry-able exception types
- [ ] T007 [P] Implement shared structured JSON logging utilities in `adapters/shared/logging.py`
- [ ] T008 [P] Create data models in `adapters/meeting_minutes/models.py`: DocumentInfo, IngestionResult, ErrorSignal dataclasses; add `extraction_timestamp: datetime` field to IngestionResult per Ingestion Policy Mandatory Evidence Mapping
- [ ] T009 [P] Create adapter configuration module in `adapters/meeting_minutes/config.py`: config schema parsing, defaults, validation
- [ ] T010 Create CLI entry point with argument parsing in `adapters/meeting_minutes/adapter.py`: --locality, --config, --last-run-timestamp flags

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Adapter Execution (Priority: P1) 🎯 MVP

**Goal**: Single manual adapter execution downloads and parses at least one PDF from the Agenda Center and inserts a valid record into `ingested_records` with all five IngestionResult payload keys.

**Independent Test**: Run `python -m adapters.meeting_minutes.adapter --locality "Victor, NY" --config '{"base_url": "...", "boards": ["Town Board"], "selectors": {...}}' --last-run-timestamp null` and verify at least one record with non-empty `source_url` and `point_of_origin` appears in `ingested_records`.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement browser navigation module in `adapters/meeting_minutes/browser.py`: headless Chromium setup, page loading, year selection traversal, document link extraction
- [ ] T012 [P] [US1] Implement PDF text extraction module in `adapters/meeting_minutes/pdf_parser.py`: download PDF via httpx, extract full text via PyMuPDF, parse meeting date/title with flexible regex, produce content_summary
- [ ] T013 [US1] Implement core adapter orchestration in `adapters/meeting_minutes/adapter.py`: wire browser + parser together, iterate discovered documents, produce IngestionResult payloads, write to `ingested_records` via PostgreSQL
- [ ] T014 [US1] Add structured JSON logging for per-document output (title, source_url, status, duration_ms) and run summary (documents_discovered, documents_ingested, documents_skipped, documents_failed, total_duration_ms) in `adapters/meeting_minutes/adapter.py`
- [ ] T015 [US1] Implement mandatory evidence mapping: ensure every record has non-empty `source_url` (from related_resources), `point_of_origin` (PDF filename or date-based identifier), and `extraction_timestamp` (UTC time of extraction) in `adapters/meeting_minutes/adapter.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently — a single manual execution successfully ingests meeting minutes from the Agenda Center.

---

## Phase 4: User Story 2 - Incremental Ingestion (Priority: P2)

**Goal**: Adapter correctly identifies new documents on a second run by comparing against `sources_registry`, processing zero records when no new documents exist, and updating `last_run`.

**Independent Test**: Run the adapter twice with the same source; the second run should log zero documents ingested and update `sources_registry.last_run` to a new timestamp.

### Implementation for User Story 2

- [ ] T016 [US2] Implement `last_run` consumption from sources_registry and incremental scan logic in `adapters/meeting_minutes/browser.py`
- [ ] T017 [US2] Implement URL deduplication against `sources_registry` to identify new, previously unrecorded PDF links in `adapters/meeting_minutes/adapter.py`
- [ ] T018 [US2] Implement stop conditions: halt scanning after 5 consecutive already-recorded documents OR 365 days into the past in `adapters/meeting_minutes/adapter.py`
- [ ] T019 [US2] Implement `last_run` update in `sources_registry` after each successful run in `adapters/meeting_minutes/adapter.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently — the adapter performs both full and incremental ingestion correctly.

---

## Phase 5: User Story 3 - Error Handling & Resilience (Priority: P3)

**Goal**: Adapter handles transient and permanent failures gracefully with retry (up to 3 attempts with exponential backoff), skips corrupted PDFs without stopping the pipeline, and triggers persistent failure alerts after 3 consecutive failures.

**Independent Test**: Simulate network failure (invalid base_url) and PDF parsing failure (corrupted PDF) to verify retry behavior and graceful skip.

### Implementation for User Story 3

- [ ] T020 [P] [US3] Integrate retry module (T006) into browser navigation and PDF parsing: apply decorator to browser navigation methods and PDF download calls, configure retry-able exceptions (ConnectionError, TimeoutError), log retry attempts
- [ ] T021 [P] [US3] Extend ErrorSignal model in `adapters/meeting_minutes/models.py` with persistent failure alerting logic (3 consecutive failures per source)
- [ ] T022 [US3] Implement persistent failure state tracking in `adapters/meeting_minutes/adapter.py`: persist consecutive failure count to `sources_registry` or local state file, trigger alert via Core Engine error-handling system after 3 consecutive failures per source

 - [ ] T023 [US3] Implement randomized delays between requests for rate limiting compliance on the CivicPlus platform in `adapters/meeting_minutes/browser.py`

**Checkpoint**: All user stories 1 through 3 should now be independently functional — the adapter is robust against transient failures and gracefully handles permanent ones.

---

## Phase 6: User Story 4 - Multi-Board Discovery & Scheduling (Priority: P4)

**Goal**: Adapter discovers and processes documents from at least 3 different boards (Town Board, Planning Board, ZBA) in a single run, supports manual trigger invocation, and completes within 15 minutes.

**Independent Test**: Run adapter with multi-board config (`["Town Board", "Planning Board", "ZBA"]`) and verify records in `ingested_records` have `metadata.board` values for at least 3 different boards.

### Implementation for User Story 4

- [ ] T024 [US4] Implement multi-board year traversal in `adapters/meeting_minutes/browser.py`: iterate configured boards, extract board name from page context or URL
- [ ] T025 [US4] Add CLI argument support for manual trigger invocation (ad-hoc runs, initial data load, re-ingestion) in `adapters/meeting_minutes/adapter.py`
- [ ] T026 [US4] Implement performance monitoring: track and log run duration, enforce 15-minute constraint in `adapters/meeting_minutes/adapter.py`

**Checkpoint**: All user stories should now be independently functional — the adapter discovers documents from multiple boards, handles scheduling, and meets performance constraints.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T027 [P] Verify `docs/specifications/` matches the current implementation (Single Source of Truth compliance gate)
- [ ] T028 [P] If verification fails, update `docs/specifications/` to reflect the current implementation
- [ ] T029 Validate implementation against all quickstart.md scenarios (Scenarios 1-8)
- [ ] T031 Code cleanup: remove debug output, add type hints, ensure consistent error messages

---

## Phase 8: Testing

**Purpose**: Unit and integration tests for all user stories

- [ ] T032 [P] Create `tests/adapters/meeting_minutes/conftest.py` with shared fixtures (mock browser, mock DB, temp PDFs)
- [ ] T033 [P] Implement `tests/adapters/meeting_minutes/test_browser.py`: mocked browser navigation, year traversal, document link extraction
- [ ] T034 [P] Implement `tests/adapters/meeting_minutes/test_pdf_parser.py`: PDF text extraction, date/title parsing, content_summary generation
- [ ] T035 [P] Implement `tests/adapters/meeting_minutes/test_adapter.py`: integration tests for core orchestration with mocked HTTP/DB
- [ ] T036 [P] Implement `tests/adapters/meeting_minutes/test_incremental.py`: incremental ingestion, deduplication, stop conditions
- [ ] T037 [P] Implement `tests/adapters/meeting_minutes/test_retry.py`: retry decorator, exponential backoff, jitter behavior
- [ ] T038 [P] Implement `tests/adapters/meeting_minutes/test_logging.py`: structured JSON log output format, run summary structure

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can proceed sequentially in priority order (P1 → P2 → P3 → P4)
  - US1 and US2 can be combined for MVP delivery
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories. **This is the MVP.**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — Builds on US1 core orchestration
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — Builds on US1/US2 implementations
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) — Extends US1 browser traversal

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T006-T009) can run in parallel
- Within US1: T011 (browser.py) and T012 (pdf_parser.py) can run in parallel
- Within US3: T020 (adapter.py retry integration), T021 (models.py), and T022 (persistent failure tracking) can run in parallel
- Within US4: T024 (browser.py) and T025 (adapter.py CLI) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch browser and PDF parser modules in parallel (different files, no cross-dependencies):
Task: "Implement browser navigation module in adapters/meeting_minutes/browser.py"
Task: "Implement PDF text extraction module in adapters/meeting_minutes/pdf_parser.py"

# After both complete, implement core orchestration:
Task: "Implement core adapter orchestration in adapters/meeting_minutes/adapter.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Verify SC-001: Single manual execution downloads and parses at least one PDF
6. Verify SC-003: Every record has non-empty `source_url` and `point_of_origin`
7. Verify SC-009: Structured JSON logs produced with per-document details and run summary

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (incremental ingestion)
4. Add User Story 3 → Test independently → Deploy/Demo (error resilience)
5. Add User Story 4 → Test independently → Deploy/Demo (multi-board, scheduling)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (browser + parser + core)
   - Developer B: User Story 2 (incremental ingestion)
   - Developer C: User Story 3 (error handling)
3. Stories complete and integrate independently

---

## Notes

- **[P]** tasks = different files, no dependencies
- **[Story]** label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

## Success Criteria Mapping

| Task | Maps To | Success Criterion |
|------|---------|-------------------|
| T011, T012, T013 | US1 | SC-001: Single execution downloads/parses PDF, inserts valid record |
 | T015 | US1 | SC-003: Every record has non-empty `source_url` and `point_of_origin` |
 | T015 | US1 | Ingestion Policy: Every record has `extraction_timestamp` |
| T014 | US1 | SC-009: Structured JSON logs with per-document details and run summary |
| T016, T017 | US2 | SC-002: Second run skips already-recorded documents |
| T019 | US2 | SC-007: `last_run` updated after each successful run |
| T006, T020 | US3 | SC-004: Transient failures trigger up to 3 retries with exponential backoff |
| T021 | US3 | SC-005: Permanent failures skipped gracefully without stopping pipeline |
| T032-T038 | Tests | Test coverage for all user stories and shared utilities |
| T024 | US4 | SC-006: Discovers documents from at least 3 different boards |
| T026 | US4 | SC-008: Single run completes within 15 minutes |
