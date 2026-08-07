# Research: Data Egress & Open Data Strategy

This document investigates methods for distributing processed information from the `on-the-board` platform to external users (journalists, researchers, and civic tech enthusiasts) while maintaining low maintenance overhead.

## 1. Distribution Methods Analysis
*Evaluation of different technical approaches to data delivery.*

### 1.1 Static Datasets (CSV/JSON via Object Storage)
*   **Pros**: Lowest maintenance; zero compute cost; leverages existing R2/S3 infrastructure.
*   **Cons**: Limited interactivity; difficulty in providing real-time updates without re-exporting.

### 1.2 Public-Facing API (REST/GraphQL)
*   **Pros**: High utility for developers; supports complex queries and programmatic access.
*   **Cons**: Higher maintenance (compute, scaling, monitoring); potential for egress cost spikes.

### 1.3 Webhooks & Push Notifications
*   **Pros**: Enables real-time reaction to new data arrivals.
*   **Cons**: Requires managing subscriber lists and delivery reliability.

### 1.4 Agentic Access (MCP/Tool-use Protocols)
*   **Pros**: Directly enables LLM agents and IDEs to "query" the municipality via standardized protocols like Model Context Protocol (MCP).
*   **Cons**: Requires defining robust, structured schema interfaces for agent reliability; potential for high-frequency automated queries.

## 2. User Persona Requirements
*Mapping the needs of different stakeholders to technical features.*

*   **Journalists**: Need easy-to-download, human-readable formats (CSV/Excel).
*   **Researchers/Data Scientists**: Need structured, machine-readable formats (JSON/Parquet) and stable schemas.
*   **Civic Tech Developers**: Need programmatic access (APIs/Webhooks) and standardized interfaces.
*   **AI Agents & LLM Users**: Need highly structured, tool-useable data via protocols like MCP to perform automated analysis or integration into RAG workflows.

## 3. Infrastructure & Cost Implications
*Assessing the impact on the existing maintenance and budget models.*

### 3.1 Relative Cost Scaling
*Estimating how costs grow with usage volume.*

*   **Static Datasets (Lowest Risk)**: Costs scale linearly with R2/S3 egress fees only; virtually zero compute overhead regardless of download frequency.
*   **Public API (Moderate Risk)**: Costs scale with query complexity and database I/O; higher risk of "expensive" queries driving up compute costs.
*   **Agentic Access (Highest Potential Risk)**: High-frequency, automated crawler-like behavior by LLM agents could drive non-linear spikes in both compute usage and egress fees.

### 3.2 Maintenance & Automation Hierarchy
*Mapping delivery methods to the project's core principle of maintenance efficiency.*

*   **Fully Automated (Target)**: Static file updates via pipeline; requires zero ongoing human intervention once configured.
*   **Semi-Automated (Secondary)**: Monitoring API/MCP health and managing rate-limiting rules; requires periodic oversight to ensure stability and cost control.

### 3.3 Observability & Guardrails
*   **Egress Costs**: Analyzing cost delta between static object storage retrieval vs. API-driven traffic.
*   **Rate Limiting & Security**: Identifying simple mechanisms (e.g., IP-based limiting or simple API keys) to prevent abuse without introducing complex authentication overhead.
*   **Anomaly Detection**: The need for basic monitoring of egress volume to detect and mitigate unexpected usage spikes from automated agents.

## 4. Interoperability & Standards
*Ensuring data is usable across the wider civic tech ecosystem by leveraging established patterns.*

### 4.1 Data Formats (The "Data" Layer)
*Focusing on high-compatibility, human/machine-readable formats.*
* **CSV/JSON/GeoJSON**: Adhering to these de facto standards ensures immediate usability for researchers and GIS tools (e.g., QGIS).
* **Schema.org Integration**: Using standardized vocabularies for entities like `Event`, `Organization`, or `GovernmentService` to improve discoverability by search engines and LLMs.

### 4.2 Access Protocols (The "Interface" Layer)
*Leveraging existing standards to avoid reinventing the wheel.*
* **SODA-style REST**: Adopting patterns similar to the Standard Open Data API for predictable, queryable dataset access.
* **Model Context Protocol (MCP)**: Building agentic access around MCP to provide structured, tool-useable context directly to LLM agents and IDEs.

### 4.3 Geospatial Compatibility
*   **OGC Standards**: Utilizing WKT (Well-Known Text) or GeoJSON for all spatial metadata to ensure seamless integration with the broader geospatial ecosystem.

## 5. Proposed Strategy & Roadmap
*Timeline: Deferred. This roadmap tracks the progression toward implementation readiness.*

### Phase 1: Research & Specification (Immediate Priority)
*   **Goal**: Resolve all items in Section 6 (Privacy, Provenance, Lifecycle).
*   **Outcome**: A finalized "Egress Specification" document defining exactly what data is exported and how.

### Phase 2: Feasibility & Prototyping (Triggered by Project Maturity)
*   **Goal**: Test the technical overhead of the chosen methods.
*   **Tasks**: 
    *   Prototype a zero-compute static export pipeline (R2/S3).
    *   Conduct a "Cost-of-Failure" analysis for API/MCP implementation.

### Phase 3: Implementation & Deployment (Long-term)
*   **Goal**: Deploy the chosen distribution layer.
*   **Primary Target**: Start with **Static Datasets** to maximize Maintenance Efficiency, only progressing to API/MCP if usage demand justifies the operational overhead.

## 6. Open Research Questions (Required before implementing egress functionality)
*Critical areas requiring deep investigation before strategy finalization.*

### 6.1 Privacy & Compliance
*How do we ensure public egress does not leak sensitive or PII-related metadata? Needs: automated redaction/anonymization audit within the export pipeline.*

### 6.2 Provenance & Integrity
*How can extracted datasets retain their connection to official sources (e.g., `source_url`, `point_of_origin`)? Needs: investigation into sidecar metadata or embedded headers in CSV/JSON.*

### 6.3 Lifecycle & Versioning
*How do users know if a downloaded dataset is stale? Needs: research into manifest-based distribution (e.g., `manifest.json` with hashes and timestamps) to ensure data continuity and authenticity.*
