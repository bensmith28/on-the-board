# Research Presentation: Web Interface (Presentation Layer)

## Overview
This document presents the architectural alternatives for the third layer of the `on-the-board` architecture: the **Web Interface**. This layer is responsible for presenting ingested and processed data to the public, enabling transparency and community engagement.

The design should adhere to the core principles of **Maintenance Efficiency**, **Geographic Adaptability**, and support the long-term roadmap for **Semantic Search** (Phase 3).

---

## Backend API
*Focusing on the presentation of stored PostgreSQL/JSONB data.*

### Proposing Alternatives

#### 1. FastAPI (The Baseline)
A lightweight, asynchronous Python framework.
* **Pros**:
    * High performance and native support for `async`.
    * Excellent developer experience with automatic OpenAPI/Swagger documentation.
    * Seamless integration with the existing Python-based Adapter layer and SQLAlchemy/SQLModel.
    * Extremely easy to extend with new endpoints as data sources grow.
* **Cons**:
    * Requires managing a running web server process (e.g., via Uvicorn/Gunicorn).

#### 2. Flask (The Classic)
A mature, synchronous WSGI micro-framework.
* **Pros**:
    * Extremely large ecosystem of extensions and community support.
    * Simple, "batteries-not-included" approach that is very easy to understand.
* **Cons**:
    * Synchronous nature can be a bottleneck for highly concurrent I/O-bound tasks (though less critical for this specific use case).
    * Requires more manual setup for modern features like async support and automated documentation compared to FastAPI.

#### 3. Django (The Monolith)
A robust, "batteries-included" full-stack web framework.
* **Pros**:
    * Includes a built-in Admin interface, which would be incredibly useful for manually auditing or correcting data (supporting the **Verifiable Truth** principle).
    * Built-in ORM, authentication, and robust security features.
* **Cons**:
    * Significantly higher overhead and complexity ("overkill" for a lightweight API).
    * Harder to maintain "minimal" footprint; more moving parts to manage/update.

---

## Cross-Cutting Concerns
*System-wide architectural decisions that impact both Backend and Frontend.*

### 1. Security & Authentication (AuthN/AuthZ)
The strategy for protecting data and managing user identities.
* **Options**:
    * **Session-based (Cookie-based)**: Standard, highly secure for browser-centric apps; simple to implement with FastAPI and HTMX.
    * **Token-based (JWT/OAuth2)**: Better for decoupled architectures or mobile apps, but adds complexity in handling token rotation and storage on the client side.

### 2. Data Intelligence Pipeline (Phase 3)
The architectural approach to processing unstructured data into searchable vectors.
* **Options**:
    * **Synchronous Processing**: Embeddings generated during ingestion; simple but can slow down the ingestion pipeline.
    * **Asynchronous Worker Pattern**: Using a task queue (e.g., Celery/Redis) to handle heavy LLM and embedding tasks out-of-band, ensuring high availability of the main API.

### 3. Observability & Monitoring
How we ensure system health and reliability.
* **Requirements**:
    * **Error Tracking**: Tools like Sentry to capture frontend and backend exceptions.
    * **Logging & Metrics**: Centralized logging (e.g., ELK stack or simpler file-based logs) and performance monitoring to track API latency and ingestion success rates.

### 4. External Integrations & Third-Party Services
How the system interacts with external providers like Google Maps, Email services, or Social Media APIs.

---

## Hosting & Infrastructure
*Focusing on deployment, cost-effectiveness, and portability.*

### Proposing Alternatives

#### 1. Self-Hosted Docker Compose (The Baseline)
Running a full application stack (FastAPI, PostgreSQL, Redis, etc.) inside a single `docker-compose.yml` on a VPS.
* **Pros**:
    * **Highest Portability**: A single command (`docker compose up -d`) can deploy the entire system anywhere that supports Docker.
    * **Lowest Cost**: Leverages fixed-cost, low-cost providers (e.g., Hetzner, DigitalOcean) with no premium for managed services.
    * **Full Control**: Complete control over database configuration, extensions (`pgvector`), and backup strategies.
* **Cons**:
    * **Operational Overhead**: Responsibility for backups, security patching, and monitoring falls on the developer.
    * **Single Point of Failure**: If the VPS goes down, the entire system is offline (though this can be mitigated with simple automated backups).

#### 2. Managed Serverless/PaaS (e.g., Railway, Render, or Fly.io)
Using a Platform-as-a-Service to handle deployment and auto-scaling.
* **Pros**:
    * **Minimal Maintenance**: Abstracts away the underlying server management, patching, and scaling logic.
    * **Fast Deployment**: Standardized workflows for CI/CD integration (e.g., "push to GitHub to deploy").
* **Cons**:
    * **Higher Cost**: Typically more expensive than a raw VPS as you pay a premium for the managed abstraction.
    * **Potential Vendor Lock-in**: Moving between PaaS providers can sometimes require adjusting configuration or handling platform-specific features.

#### 3. Cloudflare "Edge-First" (Cloudflare Ecosystem)
Leveraging a serverless approach using Cloudflare's integrated suite of services (Workers, D1, R2).
* **Pros**:
    * **Zero Server Management**: Entirely serverless; no VMs or containers to patch or scale.
    * **Extreme Performance**: API logic runs at the edge, closest to the user.
    * **Seamless Integration**: Uses your existing Cloudflare infrastructure and domain management.
    * **Cost Efficiency**: Pay-per-request model is ideal for low/intermittent workloads.
* **Cons**:
    * **Runtime Constraints**: Moving from a standard Python environment to Cloudflare Workers (WASM-based) can limit the use of certain heavy Python libraries.
    * **Database Limitations**: While D1 is excellent, it lacks the mature `pgvector` ecosystem found in PostgreSQL, which could complicate the Phase 3 roadmap for semantic search.

---

## Conclusion

*Summary of recommendations and next steps.*

### Core Recommendation: The "Low-Complexity" Stack
To align with the project's core principles of **Maintenance Efficiency** and **Geographic Adaptability**, the recommended architecture for the Web Interface is:
* **Backend**: **FastAPI**
* **Frontend**: **HTMX + Tailwind CSS**

#### Reasoning & Considerations
1.  **Operational Simplicity**: By leveraging HTMX, we avoid the "JavaScript fatigue" of managing separate SPA build pipelines and complex client-side state. This keeps the development focus on the Python-based Adapter layer.
2.  **Single Language Paradigm**: Keeping most logic within the Python ecosystem (FastAPI) makes it easier for a single developer or small team to maintain and iterate.
3.  **Performance & Accessibility**: Server-side rendered fragments via HTMX provide excellent performance, especially on mobile devices or low-bandwidth connections where municipal users might be accessing data.
4.  **Path to Phase 3**: While this stack starts simple, it is architecturally prepared for the introduction of heavier workloads (e.g., LLM-driven embedding generation) through an asynchronous worker pattern (e.g., Celery/Redis), without requiring a complete overhaul of the frontend or API layer.

### Implementation Strategy
*   **Security**: Initially implement **Session-based Authentication** to minimize complexity and leverage the strengths of HTMX.
*   **Observability**: Establish basic error tracking (Sentry) and structured logging early to ensure the "Verifiable Truth" principle can be audited.
*   **Hosting**: Prioritize a **Self-Hosted Docker Compose** approach on a VPS. This provides the highest portability for geographic expansion and ensures full compatibility with `pgvector` for Phase 3. While Cloudflare offers powerful edge capabilities, the current priority is maintaining the Python-based processing power and database flexibility required for our roadmap.
*   **Next Steps**: Researching specific low-cost VPS providers (e.g., Hetzner) and automating deployment via CI/CD to ensure minimal manual intervention.
