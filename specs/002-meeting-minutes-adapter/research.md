# Research: Meeting Minutes & Agendas Adapter

## Overview

This research document consolidates findings from the source material relevant to the Meeting Minutes & Agendas Adapter (Feature 002). It resolves technical decisions for browser automation, PDF parsing, data ingestion, and deployment.

## Decision 1: Headless Browser — Playwright

**Decision**: Use **Playwright** for browser automation to interact with the CivicPlus Agenda Center.

**Rationale**: The Agenda Center at `townofvictorny.gov/AgendaCenter` uses JavaScript (`javascript:changeYear(...)`) for year navigation and document listing. Static HTTP requests cannot access the dynamically rendered content. Playwright was selected from the research findings because:
- It supports headless Chromium, which can execute the JavaScript required by CivicPlus
- It provides programmatic navigation APIs (click, wait for navigation) suitable for traversing the year selection interface
- It is lightweight compared to Selenium and has excellent Python support via `playwright` package
- The research identified JavaScript/AJAX-rendered content as the primary practical blocker for CivicPlus sources

**Alternatives considered**:
- **Selenium**: More mature ecosystem but heavier resource footprint; Playwright offers equivalent capability with better performance
- **Static HTTP requests with reverse-engineered API calls**: CivicPlus does not expose a documented API; the document list is rendered client-side via JavaScript, making this approach fragile and likely to break with site updates

## Decision 2: PDF Text Extraction — PyMuPDF (fitz)

**Decision**: Use **PyMuPDF** (`fitz`) for PDF text extraction.

**Rationale**:
- The source data assumption states PDFs are text-based (not scanned images), making text extraction sufficient without OCR
- PyMuPDF is fast, well-maintained, and provides robust text extraction from PDFs
- It handles variable PDF layouts (different boards/years) via raw text extraction, avoiding fragile coordinate-based parsing
- The research confirmed that flexible regex patterns on extracted text (rather than fixed layouts) is the appropriate mitigation for variable PDF layouts

**Alternatives considered**:
- **pdfplumber**: Good for tabular data extraction but slower; not needed since we extract full raw text
- **pdfminer.six**: More complex API; PyMuPDF provides simpler text extraction with comparable results for text-based PDFs
- **OCR (Tesseract)**: Not needed per the assumption that PDFs are text-based; would add significant complexity and processing time

## Decision 3: HTTP Client — httpx

**Decision**: Use **httpx** for PDF downloads and any HTTP requests.

**Rationale**:
- httpx is an async-compatible HTTP client with a requests-like API
- It supports both sync and async modes, providing flexibility for the adapter implementation
- It has built-in timeout handling and connection pooling, important for rate limiting compliance

**Alternatives considered**:
- **requests**: Sync-only; would require threading for concurrent downloads
- **aiohttp**: More complex API; httpx provides a simpler interface with similar async capabilities

## Decision 4: Structured Logging — python-json-logger

**Decision**: Use **python-json-logger** (or equivalent) for structured JSON logging to stdout.

**Rationale**:
- The adapter MUST produce structured JSON logs per document and a run summary (FR-025, FR-026, FR-027)
- python-json-logger integrates with Python's standard `logging` module, requiring minimal code changes
- JSON output enables log aggregation by the orchestration engine or container runtime (Docker)
- The deployment infrastructure spec confirms that structured logging is the baseline observability strategy

**Alternatives considered**:
- **structlog**: More powerful but adds external dependency; python-json-logger is sufficient for the required output format
- **Custom JSON formatting**: Equivalent capability; using an established library reduces maintenance burden

## Decision 5: Retry Strategy — Exponential Backoff with Randomized Jitter

**Decision**: Implement **3 retries with exponential backoff** and **randomized delays** between requests.

**Rationale**:
- The spec mandates 3 retries with exponential backoff for transient failures (FR-018)
- Randomized delays prevent thundering herd effects and reduce likelihood of triggering rate limits on CivicPlus
- The research identified rate limiting as a key constraint on the CivicPlus platform
- Exponential backoff (e.g., 1s, 2s, 4s) balances retry frequency with giving upstream services time to recover

**Alternatives considered**:
- **Fixed delay**: Simpler but less robust; exponential backoff adapts to transient failure duration
- **Circuit breaker pattern**: More complex; 3 retries is sufficient for transient network issues per the spec
- **Orchestrator-managed retries**: The orchestrator (Phase 1.3) also handles transient_failure signaling, but the adapter should implement its own retry for in-run resilience

## Decision 6: Incremental Ingestion — sources_registry last_run

**Decision**: Use `last_run` from `sources_registry` for incremental ingestion, scanning from most recent to oldest.

**Rationale**:
- The adapter MUST consume `last_run` from the orchestration context (FR-015)
- The adapter MUST compare discovered document links against `sources_registry` to identify new PDFs (FR-016)
- Scanning from most recent to oldest and stopping after 5 consecutive already-recorded documents (FR-004) minimizes processing time
- The 365-day maximum scan depth bounds the worst-case processing time

**Alternatives considered**:
- **Full re-scan every run**: Simpler but wastes resources; incremental ingestion is required by the spec
- **Hash-based deduplication**: More complex; comparing document URLs against `sources_registry` is sufficient for this use case

## Decision 7: Concurrency Control — Serialized Execution via Orchestrator

**Decision**: Adapter runs MUST be serialized (one at a time per source), enforced by the orchestrator.

**Rationale**:
- The spec explicitly states multiple instances for the same source MUST NOT run concurrently (FR-028)
- The orchestrator MUST ensure serialized execution via a lock or queue mechanism
- The deployment infrastructure spec identifies Dramatiq (or RQ) + Redis as the orchestration engine, which provides built-in job queuing and locking
- Serialized execution prevents race conditions on `sources_registry` updates and reduces load on the CivicPlus platform

**Alternatives considered**:
- **Distributed locking within the adapter**: Adds complexity; the orchestrator is the natural place for concurrency control
- **Optimistic concurrency (version column)**: Less reliable; serialized execution is simpler and more robust

## Decision 8: Deployment — Docker Container on Hetzner VPS

**Decision**: Deploy the adapter as a Docker container running on a Hetzner VPS via Docker Compose.

**Rationale**:
- The research confirms self-hosted Docker Compose on Hetzner as the primary deployment strategy
- Cost: ~$6.49/month for a CX23 instance, plus ~$0.18/month for R2 object storage per municipality
- The adapter runs as an ephemeral process triggered by the orchestrator (Dramatiq/RQ worker), not as a long-running service
- Docker ensures geographic adaptability: the same container can be deployed to any VPS with minimal configuration

**Alternatives considered**:
- **Serverless (AWS Lambda)**: Execution time limits (15-minute constraint) and Playwright's resource requirements make serverless impractical
- **CI/CD driven (GitHub Actions)**: Not designed for heavy data processing or long-running tasks
- **Managed PaaS (Railway, Render)**: Higher cost than VPS; reduces geographic portability

## Decision 9: Board Discovery — Programmatic Year Traversal

**Decision**: Discover documents by programmatically traversing the year selection interface in the Agenda Center.

**Rationale**:
- The CivicPlus Agenda Center organizes documents by board and year
- The adapter MUST navigate through the year selection interface to discover all available boards across all accessible years (FR-002)
- Programmatic traversal (clicking year selectors) is necessary because the content is JavaScript-rendered
- Board names can be extracted from the page context or URL when the adapter discovers documents for each board

**Alternatives considered**:
- **Hardcoded board/year list**: Fragile; would break when CivicPlus changes the interface or adds new boards
- **URL pattern discovery**: CivicPlus does not expose a documented URL pattern for all documents; programmatic traversal is more robust

## Decision 10: Title and Date Extraction — Flexible Regex Patterns

**Decision**: Extract meeting dates and titles from PDF text using flexible regex patterns that accommodate variable layouts.

**Rationale**:
- PDFs from different boards and years have variable layouts (a known challenge documented in the adapter spec)
- The adapter MUST extract meeting dates and titles from parsed PDF text (FR-006)
- Flexible regex patterns (e.g., matching "Monday, July 27, 2026" or "July 27, 2026") are more robust than fixed-position parsing
- The raw text is preserved in full (FR-008) for downstream use; extracted metadata is supplementary

**Alternatives considered**:
- **LLM-driven extraction**: Overkill for date/title extraction; adds cost and complexity
- **PDF metadata parsing**: Agenda Center PDFs may not have reliable metadata; text extraction is more reliable
- **Fixed coordinate-based extraction**: Too fragile given variable layouts across boards and years
