# Research: Development Strategy for on-the-board

This document explores the strategies, challenges, and methodologies for developing the `on-the-board` project, focusing on maintaining high reliability and low maintenance through spec-driven development.

## 1. Development Methodology

### Spec-Driven Development
Development is centered around detailed specifications. Before any code is written, a specification (using tools like [spec-kit](https://github.com/github/spec-kit)) must define the expected behavior, inputs, outputs, and edge cases. This allows for:
*   **Clear Intent**: Eliminates ambiguity for both humans and coding agents.
*   **Testable Requirements**: Specifications provide a direct blueprint for creating regression tests.
*   **Verifiable Progress**: Success is measured by how closely the implementation adheres to the defined spec.

### Implementation Pattern
1.  **Define Specification**: Create or update a `.spec` file describing the feature/bug fix.
2.  **Write Test Cases**: Implement tests (unit, integration, or regression) that reflect the requirements in the specification.
3.  **Develop Implementation**: Write the minimum amount of code necessary to satisfy the specification and pass the tests.
4.  **Verify & Lint**: Run existing linting and type-checking suites to ensure code quality and consistency.

## 2. Development Challenges

Given the modular, adaptive nature of the project and the reliance on autonomous agents, several key challenges must be addressed:

### 1. Maintaining Specification Integrity
As the project evolves through multiple phases (e.g., moving from plain text scraping to LLM-driven extraction), there is a risk of "specification drift."
*   **Challenge**: Ensuring that updated specifications for new features do not inadvertently break or contradict existing architectural principles or established data contracts.
*   **Mitigation**: Strict adherence to the **Verifiable Truth** and **Geographic Adaptability** principles, and using the specification as the single source of truth for all automated testing.

### 2. Handling Unstructured Data Evolution (Schema-on-Read)
The use of a `JSONB` "payload" column provides flexibility but introduces complexity in how data is consumed downstream.
*   **Challenge**: As adapters evolve to extract more complex data, the logic in the API and Frontend layers must be robust enough to handle varying structures within the same database table without breaking.
*   **Mitigation**: Implementing a well-defined validation layer at the ingestion point (the Adapter layer) that ensures even variable payloads meet a minimum "contract" required by the presentation layer.

### 3. Agent Autonomy vs. System Stability
The use of coding agents for primary development introduces the risk of automated regressions or architectural violations.
*   **Challenge**: Agents might implement a feature that works in isolation but violates long-term maintenance goals (e.g., introducing a high-maintenance manual workflow instead of an automated one).
*   **Mitigation**: Integration of the **Constitution** and **Agent Operational Guidelines** into the agent's prompt context, along with strict enforcement of the test suite and linting in all CI/CD workflows.

### 4. Managing Dependency on External Unstructured Sources
The project relies heavily on scraping third-party websites (CivicPlus, YouTube, etc.) which are outside our control.
*   **Challenge**: Changes in external website structures (HTML changes, new JS rendering) can silently break adapters, leading to a "stale" or empty database without immediate error indicators in the application logic itself.
*   **Mitigation**: Implementing specialized monitoring and "health check" adapters that validate not just if a scrape *succeeded*, but if the extracted data *makes sense* (e.g., checking for expected patterns or non-empty results).

## 3. Testing Strategy

Testing is the primary mechanism for safeguarding functionality during rapid, agent-led development.
*   **Unit Tests**: Focus on individual Adapter logic (parsing specific HTML/PDF structures) and API endpoint transformations.
*   **Integration Tests**: Verify the interaction between the Adapter layer, the PostgreSQL database, and the FastAPI backend.
*   **Regression Tests**: A growing suite of tests specifically designed to ensure that fixes for previously identified issues (e.g., a broken scraper for a specific board) remain effective.
*   **Contract Testing**: Ensure that the structure of the `JSONB` payload produced by Adapters adheres to what the API and Frontend expect.

## 4. Deployment Strategy

The deployment strategy focuses on achieving the project's core principles of **Maintenance Efficiency** and **Geographic Adaptability**. The primary goal is to ensure that "forking" the project for a new municipality is as simple as deploying a single containerized stack.

### 1. Deployment Challenges

*   **Operational Burden vs. Cost**: There is a direct tension between the desire for "zero-maintenance" (which usually requires expensive managed services) and the requirement for "low cost" (which necessitates managing your own infrastructure).
*   **Data Durability & Backups**: In a low-cost, self-hosted environment, the responsibility for database backups, point-in-time recovery, and volume persistence rests entirely on the developer.
*   **Geographic Portability (The "One-Command" Goal)**: A successful deployment strategy must allow a new user to clone the repository and have a functional instance running with minimal environmental configuration or external account setup.
*   **CI/CD Complexity**: While automation is desired, introducing complex CI/CD pipelines (e.g., multi-stage Docker builds, automated migrations) can increase the "maintenance surface area" if not kept lightweight.

### 2. Alternative Strategies

#### Strategy 1: Self-Hosted Docker Compose (The Baseline)
Running a full application stack (FastAPI, PostgreSQL + `pgvector`, Redis) on a single low-cost VPS (e.g., Hetzner, DigitalOcean) using `docker-compose`.

*   **Pros**:
    *   **Highest Portability**: The entire environment is encapsulated in Docker; "forking" to a new town is as easy as running `docker compose up -d`.
    *   **Lowest Cost**: Leverages the fixed, predictable cost of a single VPS.
    *   **Full Control**: Complete access to database extensions (`pgvector`) and system-level configurations.
*   **Cons**:
    *   **High Operational Overhead**: Requires manual management of OS security patches, Docker updates, and backup orchestration.
    *   **Single Point of Failure**: If the VPS fails or is misconfigured, all services and data are at risk.

#### Strategy 2: Managed Platform-as-a-Service (PaaS) (e.g., Railway, Render)
Using a managed service to handle container orchestration, SSL termination, and automated deployments from a Git repository.

*   **Pros**:
    *   **Minimal Maintenance**: Abstracts away server management, scaling, and infrastructure patching.
    *   **Smooth Development Flow**: "Push-to-deploy" workflows are standard and highly integrated with GitHub.
*   **Cons**:
    *   **Higher Cost**: You pay a significant premium for the convenience of managed abstraction compared to raw VPS compute.
    *   **Reduced Control**: Potential difficulties in configuring specific database extensions or managing complex networking requirements between containers.

#### Strategy 3: Serverless / Edge-First (e.g., Cloudflare Workers/D1)
Leveraging edge computing and serverless databases for a "zero-server" architecture.

*   **Pros**:
    *   **Zero Infrastructure Management**: Entirely eliminates the concept of a "running server."
    *   **Scale-to-Zero Cost**: Extremely cost-effective for workloads that are intermittent (e.g., once-a-day ingestion).
*   **Cons**:
    *   **High Architectural Friction**: Requires significant changes to the Python-based Adapter logic and may not support all necessary libraries or `pgvector` capabilities.
    *   **Vendor Lock-in**: Deeply ties the project to the Cloudflare ecosystem, complicating geographic portability.

### 3. Recommended Direction

The project will prioritize **Strategy 1 (Self-Hosted Docker Compose)** as the primary implementation target. To mitigate its downsides, development will focus on:
1.  **Automated Backups**: Using tools like `litestream` or simple cron-based `pg_dump` to remote object storage (e.g., S3/R2).
2.  **CI/CD Integration**: Utilizing GitHub Actions to automate the building of Docker images and the deployment of the updated stack to the VPS via SSH, effectively bringing the "ease of deployment" from Strategy 2 into the low-cost model of Strategy 1.

## 5. Monitoring & Observability

Effective monitoring and observability are critical for a system that relies on autonomous data ingestion from external, uncontrollable sources. The goal is to detect "silent failures"—where the pipeline is technically running but no longer producing useful or accurate data.

### 1. Monitoring Challenges

*   **Silent Failures (Data Drift/Stale Data)**: An adapter might successfully scrape a page and return a `200 OK`, but the structure of the content has changed such that no meaningful information was extracted.
*   **Observability vs. Complexity**: Implementing a full observability stack (logging, metrics, tracing) can quickly exceed the "low maintenance" principle if it requires managing additional infrastructure like Prometheus or Grafana.
*   **Alert Fatigue**: In an automated system, improper alert thresholds can lead to constant notifications for non-critical issues (e.g., a single failed scrape that will be retried) causing developers to ignore actual outages.
*   **External Dependency Blindness**: It is difficult to distinguish between a failure in our code and a change/restriction on the source website (e.g., a `robots.txt` update or a site layout change) without specialized monitoring.

### 2. Alternative Strategies

#### Strategy 1: Simple Log-Based Monitoring (The Baseline)
Utilizing standard Python logging and structured logs (JSON format) that can be easily parsed by tools like `grep` or basic log aggregators.

*   **Pros**:
    *   **Zero Additional Infrastructure**: Leverages existing application logic and `docker logs`.
    *   **Low Complexity**: Easy to implement and does not increase the maintenance surface area.
*   **Cons**:
    *   **Reactive, Not Proactive**: You generally only discover issues after checking the logs or when a user reports missing data.
    *   **Difficult to Aggregate**: Analyzing trends or error frequencies across long periods requires manual effort or external log-parsing scripts.

#### Strategy 2: Error Tracking & Alerting (The "Critical Path" Approach)
Integrating a specialized tool like **Sentry** to capture and alert on explicit application exceptions and errors in real-time.

*   **Pros**:
    *   **Immediate Notification**: Provides instant alerts when the code crashes or an unhandled exception occurs.
    *   **Rich Context**: Includes stack traces, local variables, and request metadata, making debugging much faster.
*   **Cons**:
    *   **Limited to Code Failures**: Does not detect "silent" failures where the code runs perfectly but extracts no data (e.g., empty lists or structural changes).
    *   **Potential Cost/Dependency**: Introduces a third-party dependency and potential usage costs.

#### Strategy 3: Proactive "Health Check" Adapters (The Robust Approach)
Developing specialized, lightweight adapters that do not ingest data but instead validate the *state* of existing data pipelines (e.g., checking for the presence of new meeting minutes in the database).

*   **Pros**:
    *   **Detects Silent Failures**: Specifically designed to catch data staleness and structural changes by asserting on expected outcomes.
    *   **High Signal-to-Noise**: Alerts are only triggered when specific, pre-defined business logic constraints are violated (e.g., "No new minutes found for Town Board in 30 days").
*   **Cons**:
    *   **Increased Development Effort**: Requires writing and maintaining a separate suite of validation logic as the project grows.
    *   **Complexity in Logic**: Must be carefully designed to avoid false positives caused by legitimate delays in municipal publishing.

### 3. Recommended Direction

The strategy will follow a layered approach:
1.  **Foundation (Logs)**: Implement structured (JSON) logging across all adapters and the API to ensure fundamental traceability.
2.  **Error Detection (Sentry)**: Integrate Sentry for real-time alerting on explicit execution errors and exceptions.
3.  **Semantic Validation (Health Checkers)**: Implement a "Data Integrity" task that periodically runs assertions against the database (e.g., checking for unexpected empty payloads or stale timestamps) to detect the most dangerous class of failure: the silent, unnotified change in data source structure.

## 6. Conclusion

The development of `on-the-board` is predicated on creating a resilient, automated ecosystem that scales with minimal human intervention. By adhering to a **Spec-Driven Development** methodology, we establish a verifiable chain of intent that spans from initial requirements to the final deployed container. All components—from the way agents write code using [spec-kit](https://github.com/github/spec-kit) to how health checkers validate data integrity—are unified by the core principles of **Maintenance Efficiency**, **Geographic Adaptability**, and **Verifiable Truth**.

The project's strength lies in its architectural loop:
1.  **Spec & Test**: Clear specifications provide the blueprint for automated regression and contract testing, which serves as the primary safeguard against both human error and agent-led regressions.
2.  **Deploy & Automate**: A standardized Docker Compose stack, managed via CI/CD, ensures that expanding the project to new municipalities is a low-friction, repeatable process.
3.  **Monitor & Validate**: Proactive observability (via structured logs and health check adapters) protects against the most insidious threat: the silent failure of external data sources.

Ultimately, this strategy transforms development from a manual, reactive struggle against changing web structures into a proactive, automated lifecycle capable of maintaining high-fidelity historical records for any community with minimal long-term overhead.

