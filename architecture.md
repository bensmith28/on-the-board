# Architecture Specification: on-the-board

## Overview
The `on-the-board` project utilizes a "Modular Pythonic Pipeline" architecture designed for low maintenance, geographic adaptability, and incremental complexity. The primary goal is to start with simple batch collection and scale toward natural language interrogation of unstructured data without requiring major architectural shifts.

## Core Architectural Layers

### 1. Data Ingestion (The Adapter Layer)
*   **Mechanism**: A Python-based orchestration engine that executes "Adapters" on a scheduled basis (e.g., via `cron` or `schedule` library).
*   **Pattern**: **Adapter Pattern**. Each data source (e.g., Victor, NY meeting minutes) is encapsulated in its own adapter module.
*   **Evolution**: 
    *   *Phase 1*: Simple web scraping and plain text extraction.
    *   *Phase 2*: PDF parsing and complex unstructured text processing.
    *   *Phase 3*: LLM-driven structured data extraction from raw text.
*   **Principle**: Decoupled logic ensures that adding a new municipality only requires creating a new adapter, fulfilling the **Geographic Adaptability** principle.

### 2. Data Store (The Hybrid Repository)
*   **Technology**: **PostgreSQL**.
*   **Data Modeling**: A hybrid approach using:
    *   **Relational Columns**: For stable metadata (e.g., `id`, `source_type`, `timestamp`, `locality`).
    *   **JSONB Column**: To store the unstructured, variable-schema payloads from various adapters (**Schema-on-Read**).
    *   **pgvector Extension**: Reserved for future integration of vector embeddings to support semantic search and natural language querying.
*   **Principle**: Provides a single source of truth that handles both structured metadata and highly variable unstructured content.

### 3. Web Interface (The Presentation Layer)
*   **Backend API**: **FastAPI** (Python). A lightweight, asynchronous API layer that serves the data stored in PostgreSQL.
*   **Frontend**: **HTML + HTMX + Tailwind CSS**. 
    *   Uses **HTMX** for dynamic content updates without a heavy SPA (Single Page Application) framework.
    *   Uses **Tailwind CSS** for rapid, utility-first styling.
*   **Evolution**:
    *   *Phase 1*: A simple dashboard to browse and filter historical records.
    *   *Phase 2*: Advanced filtering and full-text search capabilities.
    *   *Phase 3*: Natural language interface (Chat/Query) powered by the `pgvector` embeddings.

## Technology Stack Summary

| Layer | Component | Technology |
| :--- | :--- | :--- |
| **Orchestration** | Scheduler | Python (`schedule`) / Cron |
| **Ingestion** | Adapters | Python |
| **Storage** | Database | PostgreSQL (JSONB + pgvector) |
| **API** | Web Server | FastAPI |
| **Frontend** | UI/UX | HTML, HTMX, Tailwind CSS |
| **Deployment** | Infrastructure | Docker Compose (Self-hosted / Low-cost VPS) |

## Design Principles
1.  **Maintenance Efficiency**: Prioritize automation; avoid manual data entry or updates.
2.  **Geographic Adaptability**: Logic for one municipality must be portable to another via configuration and new adapters.
3.  **Verifiable Truth**: Every piece of extracted data must be traceable back to its original source/adapter.
