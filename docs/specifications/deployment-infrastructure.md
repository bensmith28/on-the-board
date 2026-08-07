# Deployment & Hosting Infrastructure Specification

## Deployed Components

### Overview
The system is designed to run as a single, self-contained containerized stack on a low-cost Virtual Private Server (e.g., Hetz_ner). The primary goal is "one-command" deployment and high geographic portability.

### Component Breakdown
| Component | Technology | Role |
| :--- | :--- | :--- |
| **API Layer** | FastAPI | Provides the core backend logic, REST endpoints, and serves the HTMX frontend. |
| **Frontend** | HTMX + Tailwind CSS | Handles server-driven UI updates and styling within the API layer/templates. |
| **Orchestrator** | Dramatiq (or RQ) + Redis | Manages asynchronous task execution for periodic data ingestion (Adapters). |
| **Data Store** | PostgreSQL (`pgvector`) | The "Hybrid Repository" storing both structured metadata and JSONB payloads. |
| **Web Server/Proxy**| Caddy | Handles SSL termination (via Let's Encrypt) and serves as the entry point. |

### Networking & Connectivity
*   **Internal Network**: All services communicate via a private Docker bridge network. Only the web server (Caddy) exposes ports to the public internet.
*   **External Dependencies**: Egress traffic is required for Adapters to reach municipal websites, YouTube, etc. Ingress is limited to standard HTTP/HTTPS.

### Resource Requirements
To ensure system stability during high-intensity scraping tasks:
*   **CPU & RAM**: All service containers (especially Workers and PostgreSQL) must utilize **Docker resource limits** (`cpus`, `memory`) to prevent a sudden surge in parsing activity from starving the API or Database of resources.
*   **Storage**: Persistent volume for PostgreSQL data and Litestream-backed backup storage (e.g., Cloudflare R2).

## Deployment Process

### Environment Strategy


The system uses a single-environment approach (Production) that is easily replicated for Development or Staging. Each deployment instance corresponds to a specific municipality ("fork").

### Deployment Workflow
1.  **Trigger**: A code push to the main branch triggers a **GitHub Actions** workflow.
2.  **Build**: The workflow builds a new Docker image containing the API, Workers, and Frontend assets.
3.  **Deploy**: The workflow connects to the target VPS via SSH and executes `docker compose pull && docker compose up -d`.

## Configuration & Secret Delivery Patterns

To maintain the principle of "zero configuration" for new forks while preserving security, the following patterns are used to populate the host's `.env` file:

### 1. Manual Provisioning (Baseline)
* **Use Case**: Initial deployment or small-scale local testing.
* **Process**: The administrator SSHs into the VPS and manually creates/edits a `.env` file using standard text editors (e.g., `nano`). Values are sourced from a secure internal password manager.

### 2. Automated Provisioning (Scalable)
* **Use Case**: Rapidly deploying new municipality forks or automated infrastructure scaling.
* **Process**: An **Ansible** playbook is executed via a CI/CD runner. The playbook retrieves secrets from a centralized, secure store (e.g., GitHub Secrets, HashiCorp Vault, or AWS Secrets Manager) and securely writes them to the host's `.env` file as part of the server bootstrapping process.

### Best Practices
* **Never Version Control Secrets**: The `.env` file must always be included in `.gitignore`.
* **Principle of Least Privilege**: GitHub Actions should only possess the specific SSH keys and scoped permissions required to perform the `docker compose pull && docker compose up` command.
*   **Immutable Infrastructure**: Treat the VPS as disposable; all configuration (including the structure of the `.env` file) should be reproducible via IaC.

## Infrastructure Configuration

To ensure zero-config deployment readiness for new forks, configuration is split into two components:

*   **Caddyfile**: A minimal, version-controlled template that defines routing logic and configures `trusted_proxies` to correctly process `X-Forwarded-For` headers from CloudFront.
*   **.env File**: A deployment-specific file (not versioned) containing the necessary runtime parameters:
    *   **Identity**: `DOMAIN_NAME`, `MUNICIPALITY_ID`.
    *   **Secrets**: Database credentials, API keys, and cloud storage access keys.

## CI/CD Infrastructure

### Continuous Integration
*   **Linting & Type-Checking**: Automated checks run on every PR to ensure code quality and compliance with the `on-the-board` standards.
*   **Testing**: Unit and integration tests are executed within the CI pipeline to prevent regressions in Adapter logic or API endpoints.

### Continuous Deployment
*   **Automated Rollout**: Following a successful build, GitHub Actions automates the update of the containerized stack on the remote VPS using SSH-based deployment commands.

### Infrastructure as Code (IaC)
*   **Docker Compose**: The primary tool used for defining the entire application stack and its configuration.
*   **Ansible (Optional)**: Can be used to automate the initial provisioning of the VPS (e.g., installing Docker, setting up user permissions).

## Security & Identity

### Identity & Access Management (IAM)
*   **Service Authentication**: Inter-service communication relies on the internal Docker network; services do not expose credentials to each other via the public internet.
*   **User Access**: Administrative access to the server is restricted to authorized SSH keys.

### Secrets Management
Secrets are categorized by their usage and management lifecycle:

#### 1. Database & Broker Secrets
*   **Secrets**: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DATABASE_URL`, `REDIS_URL`.
*   **Usage**: Used by the FastAPI API and Dramatiq/RQ Workers to authenticate with storage and orchestration layers.
*   **Management**: Stored in a `.env` file on the host server, strictly excluded from version control.

#### 2. Cloud Storage & Integration Secrets
*   **Secrets**: `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `SENTRY_DSN`.
*   **Usage**: Used by Litestream for backup streaming and by the application for error reporting to Sentry.
*   **Management**: Injected into containers at runtime via the host's `.env` file or environment variables within the Docker Compose configuration.

#### 3. Deployment & Infrastructure Secrets
*   **Secrets**: GitHub Repository Secrets (SSH Private Key, Server IP).
*   **Usage**: Used by GitHub Actions to authenticate with and deploy code to the target VPS.
*   **Management**: Stored securely within the GitHub repository's settings; never exposed in logs or code.

### Data Protection & Encryption
*   **At Rest**: PostgreSQL data volumes are protected by host-level backups and cloud storage encryption (e.g., Cloudflare R2).
*   **In Transit**: All public-facing traffic is encrypted via TLS/SSL, terminated at the web server/proxy.

### Network Security
*   **Firewall**: The VPS firewall (e.g., `ufw`) restricts all ingress traffic except for HTTP (80) and HTTPS (443).
*   **Network Segmentation**: Services are logically separated within Docker networks to minimize the blast radius of a compromised component.

## Observability & Monitoring

### Logging
*   **Structured Logging**: All services emit logs in JSON format for machine-readability and easier parsing during debugging.
*   **Aggregation**: Logs are collected via `docker logs` and can be forwarded to an aggregator if complexity warrants it.

### Metrics & Alerting
*   **System Metrics**: Monitoring of CPU, RAM, and disk usage on the host.
*   **Application Health**: Automated alerts triggered by Sentry for code-level exceptions or through "Health Check" adapters for data staleness.

### Distributed Tracing
*   **Traceability**: Requests are logged with unique identifiers within the API/Worker flow to track execution from ingestion through storage.

## Disaster Recovery & Backup

### Backup Strategy
*   **Database Backups**: Real-time database streaming using **Litestream**, which replicates PostgreSQL WAL (Write Ahead Log) to cloud object storage (e.g., Cloudflare R2).
*   **Retention**: Configurable retention periods defined within the Litestream configuration to balance cost and recovery depth.

### Recovery Objectives (RTO/RPO)
*   **Recovery Point Objective (RPO)**: Aiming for near-zero data loss by utilizing real-time WAL streaming.
*   **Recovery Time Objective (RTO)**: Minimal downtime, as the system can be restored to a functional state as soon as the Docker container and Litestream restore processes complete on a new instance.

### Disaster Recovery Plan
In the event of total VPS failure:
1.  Provision a new VPS instance with the same or similar specifications.
2.  Re-deploy the `on-the-board` stack via Git/Docker Compose.
3.  Execute Litestream restore to pull the latest database state from object storage.
