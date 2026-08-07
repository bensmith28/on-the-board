# Project Roadmap: On-The-Board

This document outlines the phased implementation strategy for the `on-the-board` platform, following a "Vertical Slice" approach to prioritize high-risk technical validation and end-to-end functionality.

## Phase 1: The Core Pipeline (High Risk / High Value)
**Goal**: Validate the entire data lifecycle using the most complex component (Meeting Minutes Adapter).

### 1.1 Foundational Data Layer
- [x] **Storage Implementation**: Set up PostgreSQL with `pgvector` extension.
- [x] **Schema Definition**: Implement `ingested_records` and `sources_registry` tables using SQLModel.
- [x] **Verification**: Manual query to ensure JSONB payload structure matches the specification.

### 1.2 The "Type B" Adapter (Meeting Minutes)
- [ ] **Browser Automation**: Implement Playwright logic for navigating the CivicPlus Agenda Center JavaScript interface.
- [ ] **Content Extraction**: Integrate `PyMuPDF` to parse PDF text and extract meeting dates/titles.
- [ ] **Verification**: Run a single execution to confirm PDFs are downloaded and parsed into the `ing0ested_records` table.

### 1.3 Orchestration Engine (MVP)
- [ ] **Task Dispatcher**: Implement the core loop to trigger adapters based on the `sources_registry`.
- [ ] **Error Handling**: Implement basic `transient_failure` retry logic within the orchestrator.
- [ ] **Verification**: Ensure a scheduled run completes and logs success/failure in structured JSON.

### 1.4 API & Presentation Layer
- [ ] **FastAPI Backend**: Implement `/feed` and `/nav/categories` endpoints for HTMX consumption.
- [ ] **HTMX Frontend**: Create the `ActivityCard` template and a basic list view using Tailwind CSS.
- [ ] **Verification**: End-to-end test: Run adapter -> Check DB -> Refresh Browser to see new activity card.

## Phase 2: Expansion & Complexity Reduction
**Goal**: Scale the system by adding simpler data sources and improving operational efficiency.

### 2.1 "Type A" Adapter Integration
- [ ] **Press Releases Adapter**: Implement CSS/Regex-based scraping for news feeds.
- [ ] **Town Board Roster Adapter**: Implement structured parsing for official personnel lists.
- [ ] **Verification**: Validate that all adapters follow the standardized `IngestionResult` contract.

### 2.2 Advanced Search & Discovery
- [ ] **Full-Text Search**: Enable PostgreSQL `tsvector` search capabilities on `title` and `summary`.
- [ ] **Filtering UI**: Implement HTMX-powered category filters (e.g., Zoning, Budget) in the global navigation.
- [ ] **Verification**: Perform searches via API to ensure relevant records are returned accurately.

## Phase 3: Infrastructure & Scalability
**Goal**: Move from a functional prototype to a production-ready, "one-command" deployment system.

### 3.1 Deployment Automation
- [ ] **Container Orchestration**: Finalize the `docker-compose` stack (API, Workers, Redis, Postgres, Caddy).
- [ ] **CI/CD Pipeline**: Implement GitHub Actions for automated testing and SSH-based deployment to VPS.
- [ ] **Verification**: Successful "code push -> auto-deploy" workflow.

### 3.2 Resilience & Observability
- [ ] **Backup Strategy**: Integrate `Litestream` for real-time PostgreSQL WAL streaming to Cloudflare R2.
- [ ] **Monitoring**: Implement structured JSON logging and basic health check endpoints.
- [ ] **Verification**: Simulate a container failure and verify data recovery via Litestream.
