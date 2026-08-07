# Adapter Orchestration Specification

The `on-the-board` orchestration layer is responsible for managing the lifecycle of various data adapters. It ensures that scheduled discovery tasks are executed, new data is discovered according to the [Ingestion Policy](../ingestion-policy.md), and all extracted information is correctly persisted into the PostgreSQL database following the [Storage Specification](./docs/specifications/storage.md).

## Orchestration Flow

The orchestration cycle follows a structured lifecycle designed to ensure data integrity and minimize redundant processing:

1.  **Triggering**: A scheduled event (e.g., via cron) or a manual request initiates the orchestration process for specific `source_type` entries in the `sources_registry`.
2.  **Discovery & Dispatch**: The orchestrator identifies active adapters, retrieves their configuration from the `sources_registry`, and dispatches execution tasks to the appropriate runtime environment (e.g., as ephemeral Python processes).
3.  **Execution**: Individual adapters execute in sequence, performing web scraping, API calls, or OCR as required by their specific implementation strategy.
4.  **Validation & Ingestion**: As adapters return `IngestionResult` objects, the orchestrator validates them against the [Ingestion Policy](../ingestion-policy.md) and performs an `UPSERT` into the `ingested_records` table.
5.  **Completion & Reporting**: The cycle terminates by updating the last run timestamp in the `sources_registry` and logging the outcome (success/failure/partial_success) to the system logs.

## Registry Management

The `sources_registry` serves as the single source of truth for all orchestration activities.

-   **Adapter Registration**: Adding a new adapter requires an entry in the `sources_registry` defining its `source_type`, `locality`, and the initial `config` (e.g., base URL, parsing strategy).
-   **Configuration Updates**: The orchestrator can dynamically update adapter settings (like `update_frequency`) via the API without requiring a redeployment of the orchestration engine itself.
-   **State Tracking**: The registry tracks the `last_run_timestamp` and `status` for every registered source, allowing the orchestrator to implement incremental ingestion and detect stale data.

## Execution Strategy

To maintain system stability and scalability, the execution strategy focuses on isolation and controlled concurrency:

-   **Task Dispatching**: Adapters are executed as independent, ephemeral tasks (e.g., using a task queue or individual process spawns) to prevent a single failing adapter from impacting the entire pipeline.
-   **Concurrency Control**: The orchestrator implements limits on the number of concurrent adapter runs to prevent resource exhaustion (CPU/Memory/Network) on the host system.
-   **Environment Isolation**: Each adapter run is provided with a specific `context` object containing necessary environment variables, credentials (if any), and municipality-specific metadata.

## Monitoring & Observability

The orchestration engine provides multi-layered visibility into the health of the data pipeline:

-   **Structured Logging**: All lifecycle events, including dispatch, execution start/end, and ingestion results, are recorded in structured JSON logs for programmatic analysis.
-   **Health Check Adapters**: Specialized, lightweight "check" adapters are used to verify that primary content-producing adapters (like the Meeting Minutes Adapter) are actually discovering new data and not silently failing due to upstream website changes.
-   **Success/Failure Metrics**: The system tracks success rates and latency per `source_type`, allowing for proactive alerting when failure thresholds are exceeded.

## Error Handling & Retries

The system is designed to be resilient against transient network issues and temporary upstream service unavailability:

-   **Retry Policy**: For errors classified as transient (e.g., HTTP 5xx, connection timeouts), the orchestrator implements an exponential backoff retry strategy.
-   **Error Classification**: Adapators must signal whether a failure is `transient` (retryable) or `permanent` (requires developer intervention, e.g., schema change).
-   **Dead-Letter Notification**: If an adapter fails after all retries, the event is flagged in the system logs and can trigger notifications via the Core Engine's alerting mechanism.

## Scalability & Resource Management

The architecture supports the growth of the `on-the-board` ecosystem through:

-   **Horizontal Scaling Potential**: The decoupled nature of the orchestration flow allows the execution layer to be moved to separate worker nodes or serverless functions as the number of adapters grows.
-   **Resource Quotas**: The orchestrator can enforce limits on the duration of an adapter run to prevent "runaway" processes caused by complex HTML parsing or infinite loops.
-   **Incremental Processing**: By leveraging `last_run_timestamp` from the registry, the system ensures that the workload for each run scales with the *amount of new data* rather than the *total volume of historical data*.

## Adapter Interface & Requirements

To ensure compatibility with the orchestration layer, every adapter must adhere to a strict contract:

### 1. Input Contract
Every adapter must accept a `context` object containing:
-   `locality`: The municipality/entity name.
-   `config`: A JSON object containing adapter-specific parameters (e.g., `base_url`, `selectors`).
-   `last_run_timestamp`: The timestamp of the previous successful execution to facilitate incremental scraping.

### 2. Output Contract (`IngestionResult`)
All adapters must return a standardized object that populates the `ingested_records` table. This includes both the primary record columns and the structured payload.

#### Primary Record Columns
Every adapter must provide values for these core columns:
- `source_type`: The identifier for this adapter's domain (e.g., `meeting_minutes`).
- `locality`: The municipality/entity name (e.g., `Victor, NY`).
- `timestamp`: The official date/time of the event or publication.
- `source_url`: The direct link to the original source (Mandatory per Ingestion Policy).
- `point_of_origin`: Specific page number, section header, or timestamp within the source (Mandatory per Ingestion Policy).

#### Standardized Payload (`JSONB`)
Every entry in the `payload` column must contain at least these keys:
1.  **`title`**: (String) A human-readable title for the record.
2.  **`content_summary`**: (String) A brief text excerpt or cleaned version of the primary content.
3.  **`raw_text`**: (Text) The full, unformatted text extracted from the source.
4.  **`metadata`**: (JSONB) Source-specific key-value pairs (e.g., board name, channel ID).
5.  **`related_resources`**: (Array of Objects) Resource pointers, each including its own `source_url` and `point_of_origin`.

### 3. Error Signaling
Adapters must communicate failure states using a standardized error schema:
-   `status`: One of `success`, `transient_failure`, or `permanent_failure`.
-   `error_message`: A descriptive string for debugging.
-   `error_type`: Categorization (e.g., `network_error`, `parsing_error`, `schema_inconsistency`).
