# Architecture Specification: on-the-board


## Overview
The `on-the-board` project uses a "Modular Pythonic Pipeline" architecture designed for low maintenance, geographic adaptability, and incremental complexity. The goal is to transition from simple batch collection to natural language interrogation of unstructured data without major architectural shifts.

## Core Principles
All architectural decisions are driven by the [Project Constitution](.specify/memory/constitution.md):
* **Verifiable Truth**: Every piece of data must be traceable back to its original source.
* **Maintenance Efficiency**: Prioritize automation and minimize human intervention (See `AGENTS.md` for implementation hierarchy).
* **Geographic Adaptability**: Components must be modular so that a new municipality can be added via configuration and new adapters with minimal friction.

## Architectural Layers

### 1. Data Ingestion (The Adapter Layer)
A Python-based orchestration engine executes "Adapters" on a scheduled basis. Each data source is encapsulated in its own module, implementing the **Adapter Pattern**.
* **Mechanism**: Uses a Python-based executor (Refer to `research-data-ingestion.md` for orchestration alternatives and specific source analysis).
* **Compliance**: Every adapter must adhere to the [Ingestion Policy: Source Validation & Fact Integrity](./ingestion-policy.md), ensuring that all extracted data includes mandatory evidence mapping (Source URL, Point of Origin, etc.) and follows the standards for "Ground Truth" data types.
* **Evolution**: Progresses from simple web scraping/PDF parsing toward LLM-driven structured extraction.

### 2. Data Store (The Hybrid Repository)
A central repository using **PostgreSQL** to handle both structured metadata and highly variable unstructured content.
* **Data Modeling**: Uses a "Hybrid" approach with relational columns for stable metadata and `JSONB` for schema-on-read payloads (See `research-data-store.md` for modeling alternatives).
* **Future Proofing**: Leverages the `pgvector` extension to support semantic search in future phases.

### 3. Web Interface (The Presentation Layer)
A lightweight interface for presenting ingested data to the public.
* **Stack**: **FastAPI** (Backend API) + **HTMX/Tailwind CSS** (Frontend). This avoids the complexity of a heavy SPA while allowing dynamic updates.
* **Deployment**: Primarily targets a self-hosted, containerized stack (See `research-presentation.md` for hosting alternatives and strategy).

## Development & Operations

### Methodology
Development follows a **Spec-Driven Development** approach to ensure reliability in an agent-led environment (Refer to `research-development.md` for details on the implementation pattern and testing strategy).

### Observability & Maintenance
The system implements multi-layered monitoring to detect "silent failures" in automated pipelines, ranging from simple structured logging to proactive "health check" adapters (See `research-development.md` for error detection strategies).

## Strategic Positioning: Template vs. Aggregator

The long-term strategic goal for `on-the-board` is to serve as a **reproducible template** rather than a centrally managed aggregator. While the architecture allows for multiple municipalities to be run from a single instance (Aggregator), the design priority is to ensure that any individual can fork the repository and deploy a highly customized, local instance with minimal friction (Template). This means prioritizing **single-tenant portability**, **modular adapters**, and **Infrastructure as Code (IaC)** over complex multi-tenancy features.

## Technology Stack Summary

| Layer | Component | Technology |
| :--- | :--- | :--- |
| **Orchestration** | Scheduler | Python (`schedule`) / Cron |
| **Ingestion** | Adapters | Python |
| **Storage** | Database | PostgreSQL (JSONB + pgvector) |
| **API** | Web Server | FastAPI |
| **Frontend** | UI/UX | HTML, HTMX, Tailwind CSS |
| **Deployment** | Infrastructure | Docker Compose |
