# Research: Data Ingestion Layer

## Technological Alternatives

### 1. Python-based Orchestration (Current Mechanism)
*Python-based engine executing Adapters via `cron` or the `schedule` library.*

* **Compliance**: All adapters developed under this mechanism must implement the **Mandatory Evidence Mapping** defined in [ingestion-policy.md](./ingestion-policy.md) to ensure that every ingested fact is traceable and verifiable.

* **Pros**:
    * Low complexity and overhead.
    * Uses a single programming language for both orchestration and adapters. (Assumes FastAPI backend)
    * High flexibility for custom parsing logic.
* **Cons**:
    * Limited built-in observability and monitoring.
    * Manual management of retries, failures, and task dependencies.
    * Scaling becomes difficult as the number of adapters grows significantly.


### 2. Workflow Orchestration Engines (e.g., Prefect or Dagster)
*Specialized tools designed for managing complex data pipelines.*

* **Pros**:
    * Robust error handling and automatic retries.
    * Excellent observability through built-in UIs (monitoring task status, logs, etc.).
    * Sophisticated dependency management between tasks.
* **Cons**:
    * Significantly higher operational complexity and infrastructure requirements.
    * Potential "overkill" for simple web scraping tasks.

### 3. Serverless / Event-Driven Functions (e.g., AWS Lambda)
*Executing individual adapters as ephemeral, triggered functions.*

* **Pros**:
    * Highly scalable and cost-effective (pay-per-use).
    * Zero server management or maintenance overhead.
    * Naturally decoupled architecture.
* **Cons**:
    * Vendor lock-in to specific cloud providers.
    * Potential execution time limits for long-running scraping tasks.
    * Complexity in managing environment dependencies and state across different functions.

### 4. CI/CD Driven Ingestion (e.g., GitHub Actions)
*Using scheduled CI/CD workflows to trigger the ingestion process.*

* **Pros**:
    * Leverages existing infrastructure and version control.
    * Easy to set up and visible within the repository workflow.
* **Cons**:
    * Not designed for heavy data processing or long-running tasks.
    * Limited ability to manage complex state or sophisticated retry logic.

## Potential Data Sources

### 1. Municipal Meeting Minutes & Agendas
- **Data Format:** PDF (often scanned/adopted copies), hosted in a structured "Agenda Center" (CivicEngage/CivicPlus-style) with per-board archives
- **Ingestion Challenge:** Minutes lag agendas (posted only after adoption at a subsequent meeting), so the same meeting date needs to be revisited and re-ingested over time. PDFs vary in structure across boards, and older archives may be scanned images requiring OCR rather than text-native PDFs.
- **Update Frequency:** Confirmed cadences — Town Board 2nd/4th Monday monthly (~22/yr with holiday exceptions); Planning Board 2nd/4th Tuesday monthly (~24/yr); Zoning Board of Appeals 1st/3rd Monday with several single-meeting-month exceptions (~16–18/yr); Conservation Board 1st/3rd Tuesday with one exception (~23/yr). Agendas post the Friday before each meeting; minutes post after adoption at the next meeting.
- **Data Volume:** **Uncertain** — likely low-KB to low-MB PDFs each, but cumulative archive across 5–6 boards and multiple years could reach hundreds to low thousands of files. No confirmed counts.
- **Access Constraints:** Site runs on CivicPlus/CivicEngage. Actual `robots.txt` content **unverified** (could not be fetched directly). The Agenda Center likely loads results via JavaScript/AJAX search-and-filter rather than static crawlable URLs — a functional obstacle independent of robots.txt. Recommend checking `https://www.townofvictorny.gov/robots.txt` directly before crawling.

### 2. Board & Committee Meeting Video/Audio (YouTube)
- **Data Format:** YouTube livestream + archived video
- **Ingestion Challenge:** Requires speech-to-text transcription; multiple speakers, public comment periods, and legal jargon reduce accuracy. Needs timestamp alignment to agenda items; live YouTube comments are a separate, unarchived informal input channel.
- **Update Frequency:** Tied to meeting cadence above; video posted within 48 hours of the meeting (confirmed).
- **Data Volume:** **Uncertain** — meeting length varies (under an hour to several hours); no total channel video count/hours confirmed.
- **Access Constraints:** YouTube's own `robots.txt` disallows crawling most dynamic paths, but the binding constraint is **YouTube's Terms of Service** — scraping/downloading outside the official YouTube Data API is prohibited. Use the API for metadata/captions; watch for daily quota limits. Check whether auto-generated captions exist before assuming full custom STT is needed.

### 3. Planning Board Project Status Pages
- **Data Format:** HTML webpage listing active projects with bulleted "actions taken" updates
- **Ingestion Challenge:** Semi-structured, frequently-edited free text with no consistent schema; changes are additive/mutating, so history requires periodic diffing/snapshotting rather than a one-time pull.
- **Update Frequency: Uncertain** — likely tied to Planning Board's ~biweekly cadence, but not explicitly confirmed.
- **Data Volume:** **Uncertain** — likely a modest, rotating list (single-digit to low tens of active projects); no confirmed count.
- **Access Constraints:** Standard HTML page on the CivicPlus site; same unverified robots.txt caveat as Source 1.

### 4. Zoning & Land Use Applications (Planning/Building Dept.)
- **Data Format:** PDF applications, site plans, survey maps, sometimes CAD-derived drawings
- **Ingestion Challenge:** Mixed content types in a single filing requiring different extraction approaches; not all filings may be digitized/web-published (reviewed in-person at the Planning Office).
- **Update Frequency:** Loosely tied to board cadence — Planning Board applications due ≥5 weeks before a meeting, ZBA applications ≥2 weeks before.
- **Data Volume:** **Uncertain** — no data on annual application counts or file sizes (drawings could be large).
- **Access Constraints: Uncertain** — depends on whether these are published online at all vs. only available in-person at the Planning & Building Office.

### 5. Town Code / Local Laws
- **Data Format:** HTML/PDF, likely hosted via a third-party codification platform (e.g., Municode or eCode360-style)
- **Ingestion Challenge:** Cross-referencing and versioning — laws amend prior laws, requiring tracking of effective dates and supersession rather than treating the code as static.
- **Update Frequency: Uncertain** — amended irregularly whenever the Town Board passes a new law; no confirmed rate.
- **Data Volume:** **Uncertain** — likely a large, multi-chapter document; no confirmed page/section count for Victor specifically.
- **Access Constraints:** **Uncertain which vendor hosts Victor's code.** Both Municode and eCode360 are known to aggressively block automated access via bot-detection and restrictive robots.txt, since the vendor (not the town) manages the content. Verify hosting platform before designing this adapter.

### 6. Public Notices & Legal Ads
- **Data Format:** PDF postings on the town website, plus print legal notices in the local newspaper (e.g., Daily Messenger)
- **Ingestion Challenge:** Fragmented across at least two independently-controlled publishers; the newspaper copy may be the only "official" published record, raising an access/completeness problem beyond scraping difficulty.
- **Update Frequency: Uncertain** — posted as needed; site shows a rotating "Public Notices" feed suggesting several per month, not a confirmed cadence.
- **Data Volume:** **Uncertain**, especially for newspaper copies possibly behind a paywall.
- **Access Constraints:** Newspaper site is a commercial, subscription-funded property — likely **paywalled**, which is a hard access barrier independent of robots.txt. This is probably the source most likely to be fully blocked rather than just crawl-restricted.

### 7. Newsletter ("Victor Voice") & Parks & Rec Activity Guides
- **Data Format:** PDF, magazine-style layout (multi-column, image-heavy)
- **Ingestion Challenge:** Multi-column PDF layout parsing is error-prone (text ordering, wrapped columns, embedded graphics/tables); mixed announcement/program/narrative content with no consistent structure.
- **Update Frequency:** Appears **seasonal/quarterly** (a "winter 2025" issue was referenced for both publications), inferred from naming convention rather than an explicit stated schedule.
- **Data Volume:** **Uncertain** — likely 8–20 pages per issue based on typical municipal newsletter formats; not confirmed.
- **Access Constraints:** Standard downloadable PDF on the town site; same unverified robots.txt caveat as Source 1.

### 8. Notify Me / Email Subscription Announcements
- **Data Format:** Email (plain text/HTML), organized into topic-based lists
- **Ingestion Challenge:** Requires monitoring an unstructured, subscription-gated email channel; no public web archive of past notifications exists on the site.
- **Update Frequency: Uncertain** — varies per topic/list ("unlimited number of email lists"); no aggregate rate available.
- **Data Volume:** **Uncertain** — likely low per-message; total volume depends on number of active lists, not enumerated in available sources.
- **Access Constraints:** Not a robots.txt issue — requires actual subscription to each list, and there's no bulk/API access implied by the "Notify Me" feature.

### 9. Town Board / Committee Rosters & Elected Official Records
- **Data Format:** HTML pages, occasionally PDF (term expiration tables)
- **Ingestion Challenge:** Changes at irregular intervals (elections, resignations, appointments) with no changelog; detecting changes requires periodic diffing.
- **Update Frequency: Uncertain** — low-frequency by nature (4-year terms for elected officials, 5-year terms for most board/committee appointees).
- **Data Volume:** Very small — likely a single HTML page or short PDF table per board.
- **Access Constraints:** Standard HTML on the town site; same unverified robots.txt caveat as Source 1.

### 10. Budget, Financial, and Tax/Assessment Documents
- **Data Format:** PDF (budgets, audits), possibly a separate GIS/tax-lookup web application
- **Ingestion Challenge:** Dense tabular data hard to extract reliably (multi-level headers, merged cells); assessment data may live behind a dynamic, JavaScript-driven parcel-lookup tool rather than a downloadable file.
- **Update Frequency: Uncertain** — NY town budgets are typically adopted annually, but this specific cadence for Victor was not directly confirmed.
- **Data Volume:** **Uncertain** — budget documents can run dozens of pages; no confirmed size for Victor specifically.
- **Access Constraints:** If hosted on a separate tax/assessment lookup portal, this may be a **dynamic, JS-rendered application** — a functional scraping obstacle distinct from robots.txt.

### 11. GIS / Zoning Maps
- **Data Format:** Interactive web map (JavaScript-based GIS viewer), underlying shapefiles/geodata
- **Ingestion Challenge:** Requires interacting with a dynamic mapping application rather than parsing static documents; map layers may need reconstruction from an API or export rather than visual scraping.
- **Update Frequency: Uncertain** — likely event-driven (zoning changes, subdivisions), no confirmed refresh schedule.
- **Data Volume:** **Uncertain** — geodata for a ~36 sq. mi. town is likely modest, but exact volume unconfirmed.
- **Access Constraints:** If built on ArcGIS Online/Server (common for municipal GIS), there's often a documented **REST feature service** — a better ingestion path than scraping the rendered map, if Victor's instance exposes one. **Unconfirmed** whether it does.

### 12. Building Permits & Code Enforcement Records
- **Data Format:** PDF forms, possibly a searchable but dynamic permit-lookup portal
- **Ingestion Challenge:** Likely gated behind third-party permitting software with session-based/paginated results; individual records may combine typed fields with scanned attachments.
- **Update Frequency: Uncertain** — no published rate of new permits/month found.
- **Data Volume:** **Uncertain** — no data on annual permit counts or record sizes.
- **Access Constraints: Uncertain** — dependent on whichever permitting vendor the town uses; not identified in this research.

### 13. Town Court Records
- **Data Format:** PDF dockets, case listings (where public), possibly none online at all
- **Ingestion Challenge:** Often the most restricted municipal data category — availability may be limited to in-person/FOIL requests rather than open web publication, making this partly a legal-access problem, not just technical.
- **Update Frequency: Uncertain**, and possibly not applicable if not published online.
- **Data Volume:** **Uncertain** — could not confirm whether any structured or bulk records exist publicly.
- **Access Constraints:** Not a robots.txt issue — likely a legal/procedural access barrier (court records are frequently restricted regardless of crawl permissions).

### 14. FOIL (Freedom of Information Law) Request Logs/Responses
- **Data Format:** PDF correspondence, sometimes a request-tracking web portal
- **Ingestion Challenge:** Responsive documents produced on-demand, not proactively published in a central archive; building a corpus requires submitting requests directly or scraping an irregular, non-indexed portal.
- **Update Frequency: Uncertain** — inherently on-demand/event-driven.
- **Data Volume:** **Uncertain** — highly variable per request.
- **Access Constraints:** Not a robots.txt issue — constraint is procedural/legal (must file and await fulfillment).

### 15. Village of Victor Government Data (Separate Entity)
- **Data Format:** Mixed — separate website, its own agendas/minutes/PDFs
- **Ingestion Challenge:** The Village of Victor has a distinct governing and taxing body from the Town, requiring a separate adapter even though it covers overlapping geography.
- **Update Frequency: Uncertain** — likely mirrors typical municipal cadence, but not confirmed for this specific entity.
- **Data Volume:** **Uncertain** — comparable in kind to the Town's own volume, but no Village-specific figures gathered.
- **Access Constraints:** Separate domain/hosting platform likely means a **separate robots.txt** entirely — nothing learned about the Town site necessarily transfers.

### 16. Social Media Posts (Facebook, etc.)
- **Data Format:** HTML/JSON via platform-specific feeds, images, short video
- **Ingestion Challenge:** Platform APIs and ToS restrict automated access; content often duplicative of official announcements but sometimes has unique real-time updates; formats inconsistent (text, image-as-announcement, video).
- **Update Frequency: Uncertain** — likely more frequent than formal publications (potentially weekly+), not confirmed.
- **Data Volume:** **Uncertain** — likely low per-post size; total volume depends on account age/habits.
- **Access Constraints:** Governed by **Meta's API Terms of Service and authentication requirements**, not robots.txt. Scraping public pages outside the Graph API violates Facebook's terms; the Graph API requires app review, an access token, and has rate limits. Treat as an access-permission problem, not a crawling problem.

### 17. Press Releases / News Section
- **Data Format:** HTML "Read on..." news items, sometimes linked PDFs
- **Ingestion Challenge:** Content rendered dynamically within a CMS and may lack stable, individually addressable URLs, complicating reliable long-term archiving.
- **Update Frequency:** Likely frequent but irregular — homepage shows a running list with "View More News," suggesting at least a few postings per month; exact rate **uncertain**.
- **Data Volume:** **Uncertain** — items appear to be short HTML blurbs; total archive size unconfirmed.
- **Access Constraints:** Standard CMS pages on the town site; same unverified robots.txt caveat as Source 1, plus the dynamic-URL concern noted above.

### 18. School District Communications (Victor Central School District)
- **Data Format:** PDF board minutes, HTML news, possibly video board meetings
- **Ingestion Challenge:** Technically a separate taxing/governing entity from the Town, with its own site, board, and cadence — a distinct adapter target.
- **Update Frequency: Uncertain** — NY school boards typically meet monthly or twice monthly, but this district's specific schedule wasn't confirmed.
- **Data Volume:** **Uncertain** — no data gathered on this district's document/video volume.
- **Access Constraints:** Separate domain/hosting platform — likely its own `robots.txt` and CMS constraints, not yet checked.

### 19. County-Level Records Referencing Victor (Ontario County)
- **Data Format:** PDF, HTML, county GIS/records systems
- **Ingestion Challenge:** Victor-specific information is commingled with county-wide data, requiring filtering/entity-resolution to isolate what's relevant to Victor specifically.
- **Update Frequency: Uncertain** — depends on county-level activity, a larger and less Victor-specific cadence than town-level sources.
- **Data Volume:** Likely large in aggregate (county-wide); the Victor-specific subset is **uncertain**.
- **Access Constraints:** Separate hosting entirely from the Town — its own `robots.txt` and access rules, not yet checked.

### 20. Rules of Procedure & Governance Documents
- **Data Format:** Static PDF
- **Ingestion Challenge:** Low ingestion difficulty on its own, but establishes procedural context (comment rules, quorum requirements) that other ingested content implicitly assumes — useful as a low-frequency reference adapter.
- **Update Frequency:** Very low — revised only occasionally (likely years between revisions); no confirmed revision history.
- **Data Volume:** Small — a single, relatively short PDF.
- **Access Constraints:** Standard downloadable PDF on the town site; same unverified robots.txt caveat as Source 1.

---

### Cross-Cutting Notes for Adapter Design

1. **Robots.txt could not be directly verified for any domain in this research pass.** Before building any crawler, pull the live `robots.txt` for each relevant domain (townofvictorny.gov, any Municode/eCode360 subdomain, the Village of Victor site, the school district site, Ontario County's site) directly via browser or `curl`.
2. **The bigger practical blockers are likely not robots.txt at all**, but rather:
   - JavaScript/AJAX-rendered content (CivicPlus Agenda Center search interface, GIS map viewers, tax/assessment lookup tools)
   - Platform Terms of Service (YouTube Data API required instead of scraping; Facebook Graph API required instead of scraping)
   - Paywalls (local newspaper legal notices)
   - Vendor-hosted, bot-resistant platforms (Municode/eCode360, if that's what hosts the Town Code)
   - Legal/procedural access barriers (court records, FOIL responses) that no robots.txt setting would change
3. **Sources with no persistent public archive at all** (Notify Me emails, live YouTube comments, and possibly court records) mean your pipeline may become the *only* durable record — worth prioritizing capture reliability for these even though volume/frequency data is thin.
4. **Two "hidden" adapter targets** worth treating as first-class sources going forward: the Village of Victor (separate governing/taxing body) and Victor Central School District (separate entity) — both cover "Victor" but require independent adapters rather than folding into the Town's.

## Adapter Architecture Strategy

### Data Source Categorization for Adapter Design

Adapters are designed around three distinct categories of data complexity:

1.  **The "Selector" Group (High Feasibility for Config)**:
    *   **Sources**: Meeting Minutes/Agendas, Planning Board Status, Press Releases, Rosters.
    *   **Target**: Standard HTML or PDF files. Can be handled by Type A adapters using CSS selectors and regex.

2.  **The "API/Service" Group (Requires API Integration)**:
    *   **Sources**: YouTube (needs YouTube Data API), Facebook (needs Graph API), GIS Maps (needs REST feature service interaction).
    *   **Target**: Requires Type B adapters to handle authentication, rate limits, and specific JSON schemas.

3.  **The "Complex Extraction" Group (Requires Heavy Logic/ML)**:
    *   **Sources**: Meeting Video (needs STT), Zoning/Building Permits (needs PDF OCR/form parsing), Town Code (needs versioning/diffing logic).
    *   **Target**: Requires Type B adapters to handle intensive computation and data interpretation.

### Contract instead of configurability

A purely configuration-driven approach will fail for many high-value targets. The "Contract" is the right move: instead of making adapters *configurable*, we should ensure they all *implement the same interface*.

The architecture consists of three layers:
1.  **Core Engine**: Manages task execution, persistence to PostgreSQL, and alerting.
2.  **The Contract (Interface)**: Every adapter must ingest a `context` object (town-specific metadata) and return a standardized `IngestionResult` (standardized schema for Title, Date, Content, SourceURL, and Metadata).
3.  **Adapter Implementations**:
    *   **Type A (Generic/Config)**: For the "Selector" group. Minimal code; logic resides in JSON/YAML configuration.
    *   **Type B (Specialized)**: For API-heavy or complex extraction sources. Contains robust, specialized Python logic.


## Conclusion

### Strategic Prioritization

To guide initial development, data sources should be prioritized based on two axes: **Utility for Public Participation** (e.g., ease of contacting officials, knowing when to vote) and **Implementation Feasibility** (technical complexity/access).

#### Phase 1: High Utility & High Feasibility (The "Sweet Spot")
These sources provide immediate value and can be implemented with relatively simple web scraping or PDF parsing logic.
*   **Municipal Meeting Minutes & Agendas**: The most critical source for knowing what is happening; requires a polling pattern to handle late-arriving minutes.
*   **Planning Board Project Status Pages**: Highly relevant for local development concerns; involves monitoring semi-structured HTML updates.
*   **Press Releases / News Section**: High-signal announcements; easy to ingest via standard CMS scraping.
*   **Town Board/Committee Rosters**: Provides the "who" for public contact; extremely low technical barrier.

#### Phase 2: Expansion (Medium Complexity)
Adding breadth to the platform by capturing secondary information streams.
*   **Public Notices & Legal Ads**: High utility but higher difficulty due to potential paywalls and fragmented sources.
*   **Town Code / Local Laws**: Essential context, but requires managing versioning and overcoming potential vendor-based bot detection.

#### Phase 3: Advanced Intelligence (Low Feasibility)
High-impact sources that require significant technical investment in AI/ML and complex processing.
*   **Meeting Video/Audio (YouTube)**: The "gold standard" for transparency, but requires expensive Speech-to-Text transcription and timestamp alignment.
*   **GIS / Zoning Maps**: Highly valuable, but involves complex interaction with dynamic JavaScript mapping platforms.

### Recommended Technical Approach

**Alternative 1 (Python-based Orchestration)** is recommended as the initial approach, provided it is built with a "migration-ready" architecture.

*   **Efficiency & Speed**: It avoids the operational overhead of heavy orchestration engines while the project focuses on validating data sources and building the primary Adapter library.
*   **Design Pattern**: Adapters must be developed as **stateless, modular Python components**. This ensures high portability (**Geographic Adaptability**) and prevents vendor/framework lock-in.
*   **Future-Proofing**: By maintaining a decoupled architecture, the project can transition to **Alternative 2 (Workflow Orchestration Engines)** during Phase 3. At that stage, the existing Python modules can be wrapped in an engine like Prefect or Dagster to handle the increased complexity of transcription, retries, and dependency management without requiring a rewrite of the core ingestion logic.
