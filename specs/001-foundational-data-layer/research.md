# Research: Foundational Data Layer (Phase 0)

## Overview

This research consolidates findings from existing project research documents relevant to the Foundational Data Layer (Phase 1.1). It resolves technical decisions for PostgreSQL provisioning, data modeling, and deployment strategy.

## Decisions

### Decision: PostgreSQL 18.x with pgvector via Docker Compose

**Rationale**: PostgreSQL 18.x (latest stable) provides the most mature `pgvector` support. Self-hosted Docker Compose on Hetzner (CX23, ~$6.49/month) aligns with the project's core principles of Maintenance Efficiency and Geographic Adaptability. The `research-data-store.md` evaluation ruled out managed NoSQL (high cost, less pgvector idiomatic) and managed serverless (vendor lock-in, higher fork friction).

**Alternatives considered**:
- Managed Serverless PostgreSQL (Supabase, Neon) — rejected due to configuration drift for new users
- Managed NoSQL (MongoDB Atlas) — rejected due to higher cost and less pgvector support
- SQLite + Litestream — rejected due to lack of pgvector support for Phase 3

### Decision: Hybrid Relational + Wide JSONB (Model A)

**Rationale**: The hybrid approach balances flexibility (adapters can change output schema without migrations) with query capability (fixed columns for `source_type`, `locality`, `timestamp` are indexed and filterable). `research-data-store.md` evaluated Model A vs. EAV vs. Polymorphic Relational and selected Model A for geographic adaptability and low maintenance.

**Alternatives considered**:
- Entity-Attribute-Value (EAV) — rejected for extreme query complexity and poor performance at scale
- Polymorphic Relational — rejected for low flexibility (requires DDL changes per adapter) and fragmented retrieval

### Decision: UPSERT Conflict Key = (`source_url`, `point_of_origin`)

**Rationale**: These two fields together uniquely identify a piece of content per the Ingestion Policy's mandatory evidence requirement. `source_url` alone is insufficient (same URL can contain multiple agenda items). (`source_url`, `point_of_origin`) is the most precise deduplication key.

**Alternatives considered**:
- `id` (UUID) — would not deduplicate re-ingested content
- `source_url` alone — insufficient for multi-item pages
- `source_type` + `timestamp` + `title` — too fuzzy, risk of false positives

### Decision: Victor, NY as Initial Locality with Multi-Locality Schema

**Rationale**: The `locality` column in both `ingested_records` and `sources_registry` decouples the schema from Victor, NY. The initial deployment targets Victor, NY as a pilot, but the schema is designed for multi-locality expansion from the start.

**Assumptions**:
- Victor, NY's CivicPlus/CivicEngage instance is the first adapter target
- The schema supports `VARCHAR(100)` locality names (sufficient for any municipality name)

### Decision: Object Storage (R2) for Large Files, PostgreSQL for Metadata

**Rationale**: Per `research-data-retention.md`, PostgreSQL is reserved for small, high-velocity metadata. Large source files (PDFs, images) are uploaded to R2 at ingestion time. This keeps the database small (trivial backups, vacuuming, scaling) and leverages R2's zero egress fees.

**Assumptions**:
- Cloudflare R2 is the object storage provider (zero egress fees, low cost at $0.015/GB/month)
- 10-year threshold for lifecycle transition to colder storage (Glacier/Archive)

### Decision: Docker Compose Deployment with litestream Backups

**Rationale**: Per `research-development.md` and `research-cost-modeling.md`, Docker Compose on Hetzner provides the highest portability ("one-command" fork) and lowest cost (~$6.67/month per municipality). litestream provides real-time WAL streaming to R2 for point-in-time recovery.

**Alternatives considered**:
- Managed PaaS (Railway, Render) — rejected for higher cost (~3.5x multiplier)
- Cloudflare Edge-First — rejected for lack of pgvector support and Python runtime constraints

### Decision: pgvector VECTOR(n) Dimension = 1536 (OpenAI Embeddings)

**Rationale**: Phase 3 semantic search will use OpenAI text-embedding models (e.g., `text-embedding-3-small` produces 1536-dimensional vectors). Reserving `VECTOR(1536)` aligns with the most common embedding dimension for municipal text search use cases.

**Assumptions**:
- OpenAI embeddings will be the default embedding model for Phase 3
- If a different model is chosen, the VECTOR dimension can be adjusted via migration

### Decision: Data Retention — Aggregator Model

**Rationale**: Per `research-data-retention.md`, on-the-board is an aggregator, not a system of record. This removes the legal and operational burden of "data durability." PostgreSQL stores metadata; R2 stores large files. Data older than 10 years transitions to colder storage via R2 lifecycle rules.

**Implications**:
- No custom migration pipelines needed
- No multi-tier storage architecture in the application layer
- Integrity audit ("heartbeat") task needed to verify object storage keys match PostgreSQL metadata
