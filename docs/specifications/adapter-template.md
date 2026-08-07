# Adapter Specification Template

[Template instructions:
1. Create a unique name for this adapter (e.g., "Town Board Minutes Adapter").
2. Ensure the specification is complete and follows the [Ingestion Policy](./ingestion-policy.md).
3. Verify that all required data fields for the `IngestionResult` contract are addressed.
4. Remove these template instructions before finalizing.]

## Overview

[Guidance: A brief description of what this adapter does, which data source it targets, and its primary purpose within the pipeline.]

## Data Source Profile

### Target Entity
[Guidance: Identify the specific municipality or entity this adapter serves (e.g., Town of Victor, Village of Victor, etc.).]

### Primary URL/Endpoint
[Guidance: The base URL or starting point for the scraper/API consumer. Do not guess, mark as TODO if necessary. If the adapter needs to do more than hit a single url (for example, read a parent page to find the latest document), describe that here as well.]

### Access Constraints & Compliance
[Guidance: Detail any `robots.txt` restrictions, API authentication requirements, or paywall barriers. Do not guess, mark as TODO if necessary. Explicitly state how the adapter adheres to the [Ingestion Policy](./ingestion-policy.md).]

### Sample Source Data
[Capture, in part or in whole, source data from the intended target. Capture enough to make clear what the adapter needs to do, and no more. Where not feasible to capture in-line, ie video or pdf, capture as a separate sample file in this directory (should be clearly named to be related to this file). Do not guess, ask for help if you need it. Do not move past this point without capturing this sample.]

## Technical Implementation Strategy

### Adapter Type
[Guidance: Categorize as one of the following:
- **Type A (Generic/Config)**: For CSS selectors and regex-based scraping.
- **Type B (Specialized)**: For API integration, OCR, or complex extraction logic.

Describe your reasoning.]

### Extraction Logic
[Guidance: Describe the step-by-step process for retrieving and parsing the data. Mention specific tools or libraries to be used (e.g., `BeautifulSoup`, `Playwright`, `YouTube Data API`, `PyMuPDF`).]

### Execution Context & Input Contract
[Guidance: Describe how the adapter utilizes the `context` object provided by the orchestrator (including `locality`, `config`, and `last_run_timestamp`) to drive its execution logic. Explicitly confirm that this implementation is designed to consume this standard structure for incremental ingestion.]

### Update Frequency & Trigger
[Guidance: Specify how often the adapter should run (e.g., weekly, monthly) and what triggers a re-run (e.g., presence of new files, change in page content).]

## Data Contract Mapping

### Ingested Records Column Mapping
[Guidance: Define how this adapter populates the primary columns in the `ingested_records` table. Ensure all mandatory fields from the [Storage Specification](./docs/specifications/storage.md) are addressed.]

| Column Name | Source/Logic | Description |
| :--- | :--- | :--- |
| `source_type` | ... | Identifier for the adapter type (e.g., meeting_minutes). |
| `locality` | ... | The municipality/entity handled by this adapter. |
| `timestamp` | ... | Official date/time of the event or publication. |
| `source_url` | ... | The direct link to the original source. |
| `point_of_origin` | ... | Specific page, section, or timestamp within the source. |

### Payload Schema (`JSONB`)
[Guidance: Define the specific keys that will be populated within the `payload` column of the `ingested_records` table. Every key defined in the [Adapter Orchestration Specification](./adapter-orchestration.md) (title, content_summary, raw_text, metadata, and related_resources) MUST be present and populated according to its type. Ensure these are consistent with the [Storage Specification](./docs/specifications/storage.md).]

| Key | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `title` | String | ... | ... |
| `content_summary` | String | ... | ... |
| `raw_text` | Text | ... | ... |
| `metadata` | JSONB | ... | ... |
| `related_resources` | Array of Objects | ... | ... |

### Sources Registry Configuration
[Guidance: Describe any specific configuration parameters (to be stored in the `config` column) or deployment needs for the `sources_registry` table.]

### Mandatory Evidence Mapping
[Guidance: Explicitly define how the following fields are extracted for every record to ensure traceability:
- `source_url`: The direct link to the original source.
- `point_of_origin`: Specific page, section, or timestamp within the source.]

## Potential Challenges & Mitigations

### Ingestion Obstacles
[Guidance: Identify known risks such as JavaScript-rendered content, heavy PDF layouts, or rate limits, and describe the planned mitigation strategy.]

### Error Handling
[Guidance: Describe how the adapter will handle failures (e.g., retry logic, alerting via the Core Engine). Explicitly map known failure modes (e.g., network timeouts, parsing errors) to either `transient_failure` or `permanent_failure` as defined in the [Orchestration Specification](./adapter-orchestration.md).]

