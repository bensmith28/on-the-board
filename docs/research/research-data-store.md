# Research: Data Store Layer

## Overview
The Data Store layer serves as the "Hybrid Repository," acting as the single source of truth for all information ingested by the Adapter layer. Based on the architecture specification, it is designed to handle both structured metadata and unstructured/variable-schema payloads using a combination of relational columns and JSONB.

## Data Modeling

This section proposes different data structure models for storing municipal data. The goal is to balance ease of ingestion (handling variable schemas from different adapters) with ease of retrieval and usability for downstream tasks like semantic search and natural language querying.

### Model A: Flat Relational + Wide JSONB (The "Hybrid" Approach)
*As specified in the architecture.* Use fixed columns for universal metadata (`id`, `source_type`, `timestamp`, `locality`) and a single `payload` JSONB column for all source-specific content.

*   **Pros**:
    *   **High Flexibility**: Adapters can change their output schema without database migrations.
    *   **Low Complexity**: Single, unified table structure for all incoming data.
    *   **Schema-on-Read**: Enables downstream processes to parse only what they need.
*   **Cons**:
    *   **Lack of Type Safety**: The database cannot enforce structure on the payload content.
    *   **Query Complexity**: Complex filters on nested JSON attributes can become syntactically heavy and potentially slower than native columns.
    *   **Data Integrity**: Risk of inconsistent data structures across different sources (e.g., one source using `date` vs another using `timestamp`).

### Model B: Entity-Attribute-Value (EAV)
Store each piece of information as a separate row in an attribute table, where every "attribute" is linked to a specific entity and has its own value.

*   **Pros**:
    *   **Infinite Extensibility**: New attributes can be added without any schema changes.
    *   **Granular Querying**: Highly flexible for querying arbitrary properties across different source types.
*   **Cons**:
    *   **Extreme Query Complexity**: Retrieving a "complete" record requires numerous joins, which is computationally expensive and difficult to write.
    *   **Loss of Context**: The relationship between attributes is implicit rather than structural.
    *   **Poor Performance**: Becomes extremely slow as the number of rows grows.

### Model C: Polymorphic Relational (The "Typed" Approach)
Use a base `metadata` table for common properties and separate, specialized tables for different source types (e.g., `meeting_minutes`, `project_updates`, `legal_notices`), each with its own defined schema.

*   **Pros**:
    *   **Strong Type Safety**: Enforces strict schemas and data integrity via native SQL types.
    *   **Optimized Query Performance**: Fast, native indexing on specific columns (e.g., `decision_date` in a dedicated table).
    *   **Clearer Documentation**: The database schema itself serves as documentation for the expected data shape.
*   **Cons**:
    
    *   **Low Flexibility**: Adding a new source type or changing an existing one requires a DDL (Data Definition Language) change/migration.
    *   **High Maintenance**: Increased complexity in managing multiple tables and much higher effort for developers to implement new adapters.
    *   **Fragmented Retrieval**: Querying "all recent updates" across all sources requires complex `UNION` queries or application-layer aggregation.

## Technology

This section evaluates technology options for the Data Store layer, focusing on the requirements of geographic adaptability, low maintenance, and the long-term roadmap for vector-based semantic search.

### Option A: Self-hosted PostgreSQL (via Docker Compose)
*The current architectural baseline.* Hosting a standard PostgreSQL instance alongside the application stack in a containerized environment.

* **Examples**: Running a Dockerized Postgres instance on **Hetzner** Cloud or a dedicated VPS.
* **Maintenance & DevOps Overhead**: **Moderate**. The user/agent is responsible for configuring backups, managing disk space, and handling database updates or migrations.
* **Infrastructure Cost**: **Low**. Leverages existing VPS/Server costs; no premium for managed services.
* **Roadmap Support**: **Excellent**. Native support for `JSONB` (for the Adapter layer) and the `pgvector` extension (for Phase 3 semantic search) makes this the most future-proof option.
* **Geographic Adaptability**: **High**. Highly portable via Docker; can be deployed to any environment with minimal configuration changes.

### Option B: Managed Serverless PostgreSQL
Utilizing a cloud-native, managed PostgreSQL service that abstracts the underlying infrastructure.

* **Examples**: **Supabase**, **Cloudflare D1** (SQLite-based), or **Neon**.
* **Maintenance & DevOps Overhead**: **Very Low**. Handles backups, patching, and high availability automatically.
* **Infrastructure Cost**: **Variable**. Highly cost-effective for low/intermittent workloads (pay-per-use), but costs can scale aggressively as data volume and query frequency increase.
* **Roadmap Support**: **Excellent**. Most modern managed Postgres providers are heavily optimizing for `pgvector` and advanced JSON capabilities.
* **Geographic Adaptability**: **Moderate**. Introduces a dependency on specific cloud providers or regions, potentially complicating "edge" or local-only deployments.

### Option C: Managed NoSQL
A document-oriented database approach, prioritizing the flexible schema of the JSON payloads.

* **Examples**: **MongoDB Atlas**.
* **Maintenance & DevOps Overhead**: **Low**. Fully managed service with easy scaling and monitoring.
* **Infrastructure Cost**: **High**. Typically more expensive than self-hosted or serverless relational options at scale due to the premium on managed document features.
* **Roadmap Support**: **Moderate**. While excellent for unstructured "Schema-on-Read" data, implementing the hybrid relational + vector search roadmap is less idiomatic and more complex compared to PostgreSQL's integrated approach.
* **Geographic Adaptability**: **Moderate**. Primarily cloud-dependent (Atlas/AWS/GCP).

### Forkability & Geographic Adaptability

While all options can be adapted to a new locality, they differ in the "friction" involved during a/a fork/deployment:

* **Low Friction (Highest Adaptability):** 
  Options **1 (Self-hosted)** and **4 (SQLite/Litestream)** are the most portable. Since they rely on standard containers or simple files, a new user can clone the repository and have a functional database instance with minimal external configuration or account setup.

* **Medium Friction:** 
  Option **2 (Managed Serverless)** is still highly adaptable but introduces "configuration drift." A new user must create their own cloud accounts (e.g., Supabase/Cloudflare), manage API keys, and update environment variables.

* **High Friction:** 
  Option **3 (Managed NoSQL)** is the most difficult to fork due to its dependency on specific third-party cloud ecosystems (like MongoDB Atlas) which involve more complex permissioning and a higher barrier to entry for rapid local deployment.

| Option | Relative Cost | Scaling Profile |
| :--- | :--- | :--- |
| **1. Self-hosted (Hetzner)** | **Lowest/Fixed** | Linear cost increase only when upgrading VPS or adding disks. Highly predictable. |
| **2. Managed Serverless (Supabase/D1)** | **Near Zero to Low** | Extremely cheap for low usage; can spike with high query volume or storage growth. |
| **3. Managed NoSQL (Atlas)** | **Higher** | Higher baseline cost; scales based on complexity and throughput. |
| **4. SQLite + Litestream** | **Negligible** | Virtually zero, essentially just the cost of minimal R2 object storage usage. |

## 3. Conclusion

Based on the evaluation of different data modeling approaches and the projected technology requirements, the following selections have been made for the `on-the-board` Data Store layer:

### Data Modeling: Model A (Hybrid Relational + Wide JSONB)
The **Hybrid Approach** is selected to balance ease of ingestion with retrieval flexibility. 
* **Reasoning**: It provides the high flexibility needed for varying adapter schemas (**Geographic Adaptability**) while maintaining enough structure for efficient querying and downstream semantic search tasks.

### Technology: Option A (Self-hosted PostgreSQL via Docker Compose)
The **Self-hosted PostgreSQL** approach on a VPS (e.g., **Hetzner**) is selected as the primary implementation target.
* **Reasoning**: This choice prioritly aligns with our core principles of **Maintenance Efficiency** and **Geographic Adaptability**. 
    * **Highest Forkability**: A containerized PostgreSQL instance is easy for any new user to clone and run with minimal external configuration or account creation.
    * **Lowest Cost**: It offers the most predictable, fixed-cost profile by leveraging existing or low-cost VPS infrastructure.
    * **Roadmap Readiness**: It provides full access to `JSONB` and `pgvector`, ensuring the architectural transition to semantic search (Phase 3) is seamless and does not require a database migration.
