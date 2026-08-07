# Storage Specification: PostgreSQL Layer

## Overview
The storage layer provides the "Hybrid Repository" for `on-the-board`, utilizing PostgreSQL to manage both structured metadata and unstructured, variable-schema content. This specification defines the database schema, the interactions between the adapter (ingestion) and backend (API) layers, and the data contracts that ensure consistency across diverse municipal data sources.

## Data Modeling Strategy: Hybrid Relational + Wide JSONB
Following the architectural decision, the system uses a hybrid approach to balance fixed-schema stability with the flexibility required for "Geographic Adaptable" adapters.

### Core Table: `ingested_records`
The primary table stores all incoming data from various adapters.

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID (PK) | Unique identifier for the record. |
| `source_type` | VARCHAR(50) | Identifier for the adapter type (e.g., `meeting_minutes`, `press_release`, `social_media`). |
| `locality` | VARCHAR(100) | The municipality/entity the data belongs to (e.g., `Victor, NY`). |
| `timestamp` | TIMESTAMPTZ | The official date/time of the event or publication. |
| `ingestion_timestamp` | TIMESTAMPTZ | When the record was actually processed and stored. |
| `source_url` | TEXT | The original URL from which the data was extracted (Mandatory per Ingestion Policy). |
| `point_of_origin` | TEXT | Specific page number, section header, or timestamp within the source (Mandatory per Ingestion Policy). |
| `payload` | JSONB | The flexible, source-specific content (see "Data Contract" below). |
| `embedding` | VECTOR(n) | (Future/Phase 3) Semantic vector for similarity searches via `pgvector`. |

### Supporting Tables

#### `sources_registry`
Tracks the configuration and status of active adapters.
* `id`: UUID (PK)
* `name`: VARCHAR (e.g., "Town Board Minutes")
* `source_type`: VARCHAR(50) (e.g., `meeting_minutes`, `press_release`)
* `locality`: VARCHAR(100) (e.g., `Victor, NY`)
* `config`: JSONB (Contains CSS selectors, API endpoints, etc.)
* `last_run`: TIMESTAMPTZ
* `status`: VARCHAR (e.g., `active`, `failed`, `maintenance`)
* `created_at`: TIMESTAMPTZ (defaults to now())
* `updated_at`: TIMESTAMPTZ (defaults to now())

## Data Contract: The Ingestion Result
To ensure the "Contract instead of configurability" principle, all adapters must return a standardized object that satisfies the following schema when writing to the `payload` column of `ingested_records`.

### Standardized Payload Structure
Every `payload` entry must contain at least these keys:

1.  **`title`**: (String) A human-readable title for the record.
2.  **`content_summary`**: (String) A brief text excerpt or cleaned version of the primary content.
3.  **`raw_text`**: (Text) The full, unformatted text extracted from the source.
4.  **`metadata`**: (JSONB) Source-specific key-value pairs.
    *   *Example (Meeting Minutes)*: `{ "board": "Town Board", "agenda_link": "..." }`
    *   *Example (YouTube)*: `{ "channel_id": "...", "duration_seconds": 3600 }`
5.  **`related_resources`**: (Array of Objects) Resource pointers (e.g., links to full resolution texts). Each object must include its own `source_url` and `point_of_origin`.

## Layer Interactions & Contracts

### 1. Adapter -> Storage (The Ingestion Contract)
**Responsibility**: The Adapter layer is responsible for extraction, cleaning, and transformation into the contract format.
* **Mechanism**: Python-based adapters execute, parse data, and perform an `INSERT` or `UPSERT` operation into `ing0_records`.
* **Enforcement**: Adapvers must validate that all "Mandatory Evidence Mapping" (Source URL, Point of Origin) is present before the database write.

### 2. Backend -> Storage (The Retrieval Contract)
**Responsibility**: The FastAPI backend layer provides filtered access to the stored data via REST endpoints.
* **Mechanism**: The Backend uses SQLAlchemy or a similar ORM/driver to query `ingested_records`.
* **Interface Requirements**:
    *   `GET /records/{source_type}?locality=...`: Returns a list of records, mapping the `payload` JSONB directly to the API response.
    *   `GET /records/search?q=...`: (Phase 3) Utilizes the `embedding` column for semantic text search.

## Consistency with Data Sources
The schema is designed to accommodate the high variability found in `research-data-ingestion.md`:
* **Simple HTML/PDFs** (e.g., Meeting Minutes, Rosters): Use standard keys in the `payload`.
* **Dynamic Web Content** (e.g., GIS, YouTube, Facebook): The `payload` stores API-specific JSON responses and metadata without requiring schema changes.
* **Multi-Part Documents** (e.g., Building Permits, Zoning Maps): Uses the `metadata` object within the `payload` to track associated file links or secondary permit IDs.
