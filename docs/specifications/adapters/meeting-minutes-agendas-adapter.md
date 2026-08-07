# Meeting Minutes & Agendas Adapter

## Overview

This adapter targets the Town of Victor's Agenda Center to ingest meeting agendas and minutes. It automates the retrieval of PDF documents for various boards (Town Board, Planning Board, ZBA, etc.) to provide a searchable archive of municipal decisions and upcoming actions within the `on-the-board` pipeline.

## Data Source Profile

### Target Entity

Town of Victor, NY

### Primary URL/Endpoint

The primary entry point is the Agenda Center at `https://www.townofvictorny.gov/AgendaCenter`. The adapter must navigate this interface to find specific boards and their respective document archives.

### Access Constraints & Compliance

* **Robots.txt**: Generally permissive for `/AgendaCenter`, but excludes several administrative and search paths (e.g., `/admin`, `/search.aspx`).
* **Technical Obstacles**: The Agenda Center uses JavaScript (`javascript:changeYear(...)`) to navigate between years, requiring a headless browser (e.g., Playwright) to trigger the correct views for scraping.
* **Compliance**: This adapter adheres to the [Ingestion Policy](../../ingestion-policy.md) by ensuring every ingested record contains verifiable evidence mapping (Source URL and Point of Origin).

### Sample Source Data

[this sample text was read in from [the sample pdf here](./meeting-minutes-agendas-sample.pdf)]

**Victor Town Board Agenda - Monday, July 27, 2026**
85 East Main Street, 1st Floor Main Meeting Room

**PUBLIC EDUCATIONAL WORKSHOP**
Workshop from 6:30pm - 7:00pm
Call to Order Meeting at 7:00pm

**Agenda Items:**
*   Flag Salute
*   Roll Call
*   Approval of July 13, 2026, Bill Pay Meeting Minutes
*   Supervisor Announcements
*   Payment of Bills – Manifest No. 14
*   **Public Hearing:** Consolidated Sewer District Connection Charge
*   **Privilege of the Floor**
*   **Public Comments** (3 minutes, please)
*   **Reports of Town Officials:**
    *   Planning & Building
    *   Finance
    *   Highway
*   **Action Items:**
    *   **Finance:** Amend 2026 Budget for Gymnasium Floor, ARPA Revenue/Expense, Budget Transfer, Authorization to Lease Facilities.
    *   **Parks and Recreation:** Appointment of Student Representative to Parks and Recreation Citizens Advisory Committee.
    *   **Supervisor:** After Public Hearing Consolidated Sewer District Connection Charge.
    *   **Town Clerk:** Stone Brook LOC Release No. 2
*   Public Comment
*   Adjourn

**Note:** This meeting will be held at the Victor Town Hall and live streamed via YouTube with text commenting available. Go To: https://www.youtube.com/c/townofvictornewyork

## Technical Implementation Strategy

### Adapter Type
**Type B (Specialized)**

The adapter requires a headless browser to interact with the JavaScript-driven navigation (`javascript:changeYear(...)`) used by the CivicPlus Agenda Center to traverse different years of archives.

### Extraction Logic
1.  **Navigation**: Use **Playwright** to load `https://www.townofvictorny.gov/AgendaCenter`.
2.  **Discovery**: Programmatically click through year selection elements to identify all available boards (Town Board, Planning Board, etc.).
3.  **Link Retrieval**: Traverse the list of documents for each board and extract direct URLs to PDF files.
4.  **Content Extraction**: Use **PyMuPDF** (`fitz`) to parse the downloaded PDFs and extract text content.
5.  **Transformation**: Map extracted text into the standardized `IngestionResult` schema, identifying meeting dates, titles, and summaries.

### Update Frequency & Trigger

The adapter will run on a **weekly schedule**. 

* **Incremental Ingestion**: To optimize resources, the adapter will use the `last_run_timestamp` from the execution `context` to compare discovered document links against the `sources_registry`. Only new, previously unrecorded PDF links will be downloaded and processed for ingestion.
* **Scanning Scope**: On each run, the adapter will traverse the Agenda Center starting with the most recent and moving into the past, until either it discovers 5 consecutive alread-recorded documents OR a maximum of 365 days into the past.
* **Trigger**: The run is primarily schedule-driven (twice weekly, Tuesday and Friday at midnight), ensuring that any newly posted agendas or minutes are captured within days of their publication.
* **Performance Constraint**: A single adapter run (processing all configured boards) MUST complete within 15 minutes under normal conditions.

## Data Contract Mapping

### Payload Schema (`JSONB`)

This adapter's output strictly adheres to the `IngestionResult` payload schema defined in the [Adapter Orchestration Specification](./../../adapter-orchestration.md).

| Key | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `title` | String | A human-readable title for the record. | "Town Board Agenda - July 27, 2026" |
| `content_summary` | String | A brief text excerpt or cleaned version of the primary content. | "Meeting held at 7:00pm..." |
| `raw_text` | Text | The full, unformatted text extracted from the source. | "...[full text]..." |
| `metadata` | JSONB | Source-specific key-value pairs. | `{ "board": "Town Board", "agenda_link": "..." }` |
| `related_resources` | Array (Objects) | Resource pointers with `source_url` and `point_of_origin`. | `[{ "source_url": "...", "point_of_origin": "..." }]` |

### Mandatory Evidence Mapping

*   **`source_url`**: Extracted from the `href` attribute of the document link found in the Agenda Center list.
*   **`point_of_origin`**: For agendas/minutes, this will be the specific filename or date-based identifier within the PDF metadata or parsed text (e.g., "Page 1: Header").

## Potential Challenges & Mitigations

### Ingestion Obstacles

* **JavaScript-Rendered Content**: The Agenda Center relies on JavaScript for navigation and year selection. 
  * *Mitigation*: Use **Playwright** as a headless browser to execute scripts and ensure the full DOM is rendered before extraction.
* **Variable PDF Layouts**: Different boards or different years may have slightly different document structures.
  * *Mitigation*: Use robust text-based parsing with **PyMuPDF** rather than relying on fixed coordinate-based OCR, and implement flexible regex patterns for date/title extraction.
* **Rate Limiting**: Frequent scraping could trigger protections on the CivicPlus platform.
  * *Mitigation*: Implement randomized delays between requests and adhere to a respectful weekly cadence.

### Error Handling

* **Extraction Failures (Permanent)**: If a PDF is corrupted or unreadable, it will be signaled as a `permanent_failure` with an appropriate `error_type` (e.g., `parsing_error`), and the specific record will be skipped to prevent pipeline stoppage.
* **Network/Browser Errors (Transient)**: Playwright execution failures (e.g., timeouts) will be signaled as a `transient_failure` (e.g., `network_error`) and will trigger up to 3 retry attempts with exponential backoff within the same run session.
* **Alerting**: Persistent failures (e.g., 3 consecutive failed runs) will trigger an alert via the Core Engine's error-handling system for manual investigation.

### Monitoring & Logging

* **Per-Document Logging**: For every document processed, the adapter MUST produce structured JSON log entries containing: document title, source URL, processing status (success/failure), processing duration, and any error details.
* **Run Summary Logging**: At the end of each run, the adapter MUST log a run summary containing: total documents discovered, documents ingested, documents skipped (already recorded), documents failed, and total run duration.
* **Log Output**: All logs MUST be written to stdout in structured JSON format, enabling log aggregation by the orchestration engine or container runtime.

