# Research: Quantitative Cost Modeling

This document outlines the methodology and structure for transitioning from qualitative cost assessments to a predictable financial model for the `on-the-board` project.

## 1. Objective
To establish a repeatable, data-driven framework for estimating the monthly infrastructure costs of deploying a single municipality instance and projecting total expenditure as the platform scales.

## 2. Infrastructure Components (The "Cost Drivers")
*Identified from architecture and retention research.*

### 2.1 Compute & Orchestration
*   **Primary Stack**: Docker Compose on Hetzner Cloud (CX23 tier).
*   **Estimated Footprint**: 2 vCPU, 4GB RAM (Practical floor for stability).

### 2.2 Database (Metadata)
*   **Engine**: PostgreSQL.
*   **Estimated Footprint**: Small-footprint container running alongside the app; ~500MB - 1GB disk space per municipality for metadata/indices.

### 2.3 Object Storage (Source Documents)
*   **Provider**: Cloudflare R2 (preferred for zero egress fees).
*   **Growth Factor**: ~12GB of PDF/text data ingested per year per municipality.

### 2.4 Networking & Egress
*   **Traffic Type**: Inbound (Ingestion) and Outbound (Open Data Strategy).
*   **Estimated Volume**: Minimal, given R2's zero egress model; primarily focused on API/HTML delivery overhead.

## 3. Cost Estimation Methodology (Feasibility Study Results)

### 3.1 Unit Cost Calculation (Single Municipality)
| Metric | Value (USD) |
| :--- | :--- |
| Monthly cost for smallest Hetzner instance (CX23) | $6.49 |
| Object Storage cost per GB/month (Cloudflare R2) | $0.015 |
| Monthly storage cost at 12GB/year ingestion | $0.18 |
| **Total Estimated Monthly Cost (1 Municipality)** | **$6.67** |

### 3.2 Comparative Scaling Projections (Persona Analysis)
The following table compares the monthly infrastructure costs across different deployment personas based on a standardized specification of ~2 vCPU and 4GB RAM.

| Deployment Persona | Provider | Monthly Instance Cost (USD) | Key Advantage/Trade-off |
| :---                | :---     | :---                        | :---                      |
| **VPS Market**      | Vultr       | ~$20.00 - $24.00            | Lowest raw cost; high manual ops burden (patching, backups, firewall) |
| **Managed Lite**    | AWS Lightsail| ~$24.00                     | Bundled simplicity; easy snapshots, DNS, and path to AWS ecosystem   |
| **Zero-Cost**       | Oracle Cloud | $0.00                       | Extremely high risk (Availability/Policy); Requires ARM64 compatibility |

### 3.3 Scaling Projections (Hetzner Baseline)
*Logic for calculating Total Cost = (Cost of Single Instance * N) + Centralized Orchestration Overhead.*

| Number of Municipalities (N) | Total Monthly Infrastructure Cost | Projected Annual Expenditure |
| :--- :| :--- :| :--- :|
| 1 (Pilot) | $6.67 | $80.04 |
| 10 (Regional) | $66.70 | $800.40 |
| 50 (Scale) | $333.50 | $4,002.00 |

## 4. Conclusion

The feasibility study confirms that the `on-the-board` architecture is exceptionally scalable and economically viable. By leveraging a "Template" model on low-cost infrastructure (Hetzner Baseline), we can expand to 50 municipalities for an estimated annual expenditure of approximately $4,002.

While the "Managed Lite" approach (AWS Lightsail) offers reduced operational complexity, it introduces a ~3.5x cost multiplier per unit. However, since our architectural roadmap prioritizes high-level automation and relies on agent-led maintenance (as per `AGENTS.md`), the "Ops Tax" of using raw VPS instances can be mitigated through automated patching, monitoring, and backup orchestration. 

**Decision**: We will proceed with the **Hetzner Baseline** as our primary target for production deployments to maximize long-term scalability and minimize infrastructure overhead.



