# Feature Specification: Meeting Minutes & Agendas Adapter

**Feature Number**: 002
**Short Name**: meeting-minutes-adapter
**Created**: 2026-08-07
**Phase**: 1.2 — The Core Pipeline
**Status**: Draft

## Clarifications

### Session 2026-08-07

- Q: What is the maximum acceptable duration for a single adapter run (processing all boards)? → A: Under 15 minutes
- Q: How many retry attempts should the adapter make for transient failures before marking the run as failed? → A: 3 retries with exponential backoff
- Q: Should each board (Town Board, Planning Board, ZBA, etc.) have its own `source_type` value, or should all meeting records share a single `source_type`? → A: Single `source_type` (`meeting_minutes`) for all boards
- Q: What level of structured logging should the adapter produce, and where should logs be stored? → A: Structured JSON logs per document with run summary
- Q: Should multiple instances of this adapter be allowed to run concurrently for the same source? → A: No — runs must be serialized (one at a time per source)

## 1. Overview

This feature implements the "Type B" adapter for ingesting meeting agendas and minutes from the Town of Victor's CivicPlus Agenda Center. It automates the retrieval of PDF documents for multiple boards (Town Board, Planning Board, ZBA, etc.) and processes them into the `ingested_records` table established in Phase 1.1.

The adapter is the highest-risk component in Phase 1 because it must handle a JavaScript-rendered website, download and parse PDFs with variable layouts, and produce structured records that satisfy the `IngestionResult` contract and the Ingestion Policy's Mandatory Evidence Mapping requirements.

### Source Material

This specification was derived from the following source documents:

- **`docs/roadmap.md`** — Phase 1.2 task definition: browser automation, PDF content extraction, verification.
- **`docs/specifications/adapters/meeting-minutes-agendas-adapter.md`** — Primary adapter spec: target entity, URL, extraction logic, data contract, challenges, error handling.
- **`docs/specifications/adapter-orchestration.md`** — `IngestionResult` contract, adapter input/output interface, error signaling, orchestration flow, retry policy.
- **`docs/specifications/storage.md`** — `ingested_records` schema, `IngestionResult` payload contract, layer interactions.
- **`docs/specifications/adapter-template.md`** — Adapter specification structure and data contract mapping pattern.
- **`docs/ingestion-policy.md`** — Verifiable Truth standards, source trustworthiness criteria, Mandatory Evidence Mapping requirements.
- **`docs/architecture.md`** — Modular adapter pattern, geographic adaptability principle, technology stack.

**Conflicts with source material**: None identified. The adapter spec's data contract, extraction logic, and error handling align with the orchestration, storage, and ingestion policy specifications.

## 2. User Scenarios & Testing

### Primary User Scenarios

1. **System Operator verifies adapter execution**: After a scheduled adapter run, the operator can check structured logs for success/failure status, confirm that new records appear in `ingested_records`, and validate that each record has valid evidence fields (source URL, point of origin).

2. **Resident views new meeting data**: A resident visits the activity feed and sees newly ingested meeting agendas or minutes displayed as activity cards, with links to the original PDF source for verification.

3. **Developer adds a new board or municipality**: A developer configures the adapter to target a different board or municipality by updating the `sources_registry` entry (base URL, selectors), without modifying adapter code.

### Testing Considerations

- Single-execution verification: run the adapter manually to confirm PDFs are downloaded and parsed into `ingested_records`.
- Incremental ingestion test: run the adapter twice to confirm the second run skips already-recorded documents (using `last_run_timestamp` comparison against `sources_registry`).
- Error handling test: simulate network failure and PDF parsing failure to verify `transient_failure` and `permanent_failure` signaling.
- Evidence mapping test: confirm every ingested record has non-empty `source_url` and `point_of_origin`.
- JavaScript rendering test: verify the headless browser correctly navigates the year selection interface and renders the full document list.

## 3. Functional Requirements

### 3.1 Browser Automation

- **FR-001**: The adapter MUST use a headless browser to load and render the JavaScript-driven CivicPlus Agenda Center, ensuring all dynamically loaded content is available before extraction.
- **FR-002**: The adapter MUST programmatically navigate through the year selection interface to discover all available boards across all accessible years. All discovered records MUST use `source_type` = `meeting_minutes` regardless of board.
- **FR-003**: The adapter MUST extract direct URLs to PDF documents from the rendered page for each discovered board.
- **FR-004**: The adapter MUST traverse documents starting from the most recent and moving into the past, stopping when either 5 consecutive already-recorded documents are found OR 365 days into the past is reached (whichever comes first).

### 3.2 PDF Content Extraction

- **FR-005**: The adapter MUST download each discovered PDF and parse its text content.
- **FR-006**: The adapter MUST extract meeting dates and titles from the parsed PDF text using patterns that accommodate variable layouts across boards and years.
- **FR-007**: The adapter MUST produce a `content_summary` from the parsed text (a brief excerpt or cleaned version of the primary content).
- **FR-008**: The adapter MUST preserve the full extracted text as `raw_text` for each record.

### 3.3 Data Contract Compliance

- **FR-009**: Every ingested record MUST satisfy the `IngestionResult` payload contract with all five required keys: `title`, `content_summary`, `raw_text`, `metadata`, and `related_resources`.
- **FR-010**: The `metadata` JSONB MUST include at minimum the board name (e.g., `"board": "Town Board"`) and the original agenda link (e.g., `"agenda_link": "..."`).
- **FR-011**: The `related_resources` array MUST contain resource pointers with `source_url` and `point_of_origin` for every linked resource (e.g., the PDF file itself, any referenced external resources like YouTube streams).
- **FR-012**: The `source_url` MUST be the exact link where the document link was found in the Agenda Center list.
- **FR-013**: The `point_of_origin` MUST be a specific identifier within the source, such as the PDF filename or date-based identifier.
- **FR-014**: Records that fail any validation rule from the `IngestionResult` contract (as defined in Phase 1.1, VR-001 through VR-007) MUST be rejected and logged with the specific failed rule.

### 3.4 Incremental Ingestion

- **FR-015**: The adapter MUST consume the `last_run_timestamp` from the orchestration `context` to determine which documents to process.
- **FR-016**: The adapter MUST compare discovered document links against the `sources_registry` to identify new, previously unrecorded PDF links. Only new links are downloaded and processed.
- **FR-017**: After a successful run, the adapter MUST update the `last_run_timestamp` in the `sources_registry` for the corresponding entry.

### 3.5 Error Handling & Signaling

- **FR-018**: Network or browser execution failures (e.g., timeouts, connection errors) MUST be signaled as `transient_failure` with `error_type` `network_error`, triggering up to 3 retry attempts with exponential backoff within the same run session.
- **FR-019**: PDF parsing failures (e.g., corrupted or unreadable PDFs) MUST be signaled as `permanent_failure` with `error_type` `parsing_error`, and the specific record MUST be skipped without stopping the pipeline.
- **FR-020**: Persistent failures (3 consecutive failed runs for the same source) MUST trigger an alert via the Core Engine's error-handling system for manual investigation.
- **FR-021**: The adapter MUST implement randomized delays between requests to avoid rate limiting on the CivicPlus platform.

### 3.6 Update Frequency & Scheduling

- **FR-022**: The adapter MUST be configured to run on a twice-weekly schedule (Tuesday and Friday at midnight) via the orchestration engine's scheduler.
- **FR-023**: The adapter MUST support manual trigger invocation for ad-hoc runs (e.g., initial data load, re-ingestion).

### 3.7 Performance Constraints

- **FR-024**: A single adapter run (processing all configured boards) MUST complete within 15 minutes under normal conditions.

### 3.8 Observability & Logging

- **FR-025**: The adapter MUST produce structured JSON logs for every document processed, including document title, source URL, processing status (success/failure), processing duration, and any error details.
- **FR-026**: At the end of each run, the adapter MUST log a run summary containing total documents discovered, documents ingested, documents skipped (already recorded), documents failed, and total run duration.
- **FR-027**: Logs MUST be written to stdout in structured JSON format, enabling log aggregation by the orchestration engine or container runtime.

### 3.9 Concurrency Constraints

- **FR-028**: Multiple adapter runs for the same source MUST NOT execute concurrently. The orchestrator MUST ensure serialized execution per source via a lock or queue mechanism.

## 4. Success Criteria

### 4.1 Measurable Outcomes

- **SC-001**: A single manual adapter execution successfully downloads and parses at least one PDF from the Agenda Center and inserts a valid record into `ingested_records` with all required `IngestionResult` payload keys.
- **SC-002**: The adapter correctly identifies new documents on a second run by comparing against `sources_registry`, processing zero records when no new documents exist.
- **SC-003**: Every ingested record has non-empty `source_url` and `point_of_origin` fields, satisfying the Ingestion Policy's Mandatory Evidence Mapping requirement.
- **SC-004**: Transient failures (simulated network errors) trigger up to 3 automatic retries with exponential backoff before the run is marked as failed.
- **SC-005**: Permanent failures (corrupted PDFs) are skipped gracefully without stopping the pipeline, and the failure is logged with the correct `error_type`.
- **SC-006**: The adapter discovers and processes documents from at least 3 different boards (e.g., Town Board, Planning Board, ZBA) in a single run.
- **SC-007**: The `sources_registry` `last_run_timestamp` is updated after each successful run.
- **SC-008**: A single adapter run completes within 15 minutes when processing all configured boards with no transient failures.
- **SC-009**: Every run produces structured JSON logs with per-document details and a final run summary, verifiable by inspecting stdout output.

## 5. Key Entities

### 5.1 Adapter Context (Input)

| Field | Type | Description |
|:---|:---|:---|
| `locality` | String | Municipality/entity name (e.g., `Victor, NY`) |
| `config` | JSONB | Adapter-specific parameters: `base_url`, `selectors`, `max_days_back`, `consecutive_skip_threshold` |
| `last_run_timestamp` | TIMESTAMPTZ | Timestamp of the previous successful execution for incremental ingestion |

### 5.2 IngestionResult (Output)

| Key | Type | Required | Description |
|:---|:---|:---|:---|
| `title` | String | Yes | Human-readable title (e.g., "Town Board Agenda - July 27, 2026") |
| `content_summary` | String | Yes | Brief text excerpt from the parsed PDF |
| `raw_text` | Text | Yes | Full unformatted text extracted from the PDF |
| `metadata` | JSONB | Yes | Source-specific data: `board`, `agenda_link`, etc. |
| `related_resources` | Array[Object] | Yes | Resource pointers with `source_url` and `point_of_origin` |

### 5.3 Error Signal (Output)

| Field | Type | Description |
|:---|:---|:---|
| `status` | String | `success`, `transient_failure`, or `permanent_failure` |
| `error_message` | String | Descriptive error string for debugging |
| `error_type` | String | Categorization: `network_error`, `parsing_error`, `schema_inconsistency`, etc. |

### 5.4 sources_registry Entry (Managed by Orchestrator)

| Field | Type | Description |
|:---|:---|:---|
| `name` | VARCHAR | Human-readable name (e.g., "Town of Victor Agenda Center") |
| `source_type` | VARCHAR | `meeting_minutes` |
| `locality` | VARCHAR | `Victor, NY` |
| `config` | JSONB | `{"base_url": "https://www.townofvictorny.gov/AgendaCenter", "boards": ["Town Board", "Planning Board", "ZBA"]}` |
| `last_run` | TIMESTAMPTZ | Updated after each successful run |
| `status` | VARCHAR | `active`, `failed`, `maintenance` |

## 6. Assumptions

- The CivicPlus Agenda Center's structure (DOM elements, year navigation pattern, document list format) remains stable enough for selector-based extraction to work long-term.
- PDFs from the Agenda Center are text-based (not scanned images), making text extraction sufficient without OCR.
- The Town of Victor's Agenda Center does not implement aggressive bot detection beyond standard rate limiting.
- "Board name" can be reliably extracted from the page context or URL when the adapter discovers documents for each board.
- The `sources_registry` entry for this adapter will be pre-populated by a SQL migration or manual setup before the adapter is first run.
- Victor, NY is the initial locality; the adapter's `config` is parameterized to support other municipalities with minimal code changes.

## 7. Dependencies

- **Phase 1.1 (Foundational Data Layer)**: Requires `ingested_records` table, `sources_registry` table, `IngestionResult` contract, and validation rules (VR-001 through VR-007) to be in place.
- **Phase 1.3 (Orchestration Engine)**: Requires the orchestrator to trigger the adapter on schedule, provide the execution `context`, and handle retry logic for `transient_failure` errors.
- **Phase 1.4 (API & Presentation Layer)**: Depends on ingested data from this adapter to populate the `/feed` endpoint and display activity cards.
- **External**: CivicPlus Agenda Center at `townofvictorny.gov` must remain accessible and structurally consistent. `robots.txt` compliance must be monitored.
