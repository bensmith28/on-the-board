# Research: Data Lifecycle & Retention Strategy

## Context
This document captures the research and decision-making process regarding addressing **Research Gap #3: Data Lifecycle & Retention Policy** from `research-gaps.md`.

## Objective
To define a sustainable strategy for long-term storage management and cost control without introducing excessive architectural complexity.

## Initial Complexity Assessment
An unconstrained approach to this problem would have required:
*   **Multi-tier storage architecture**: Managing the logic between "Hot" (Post-greSQL) and "Cold" (S3/R2) tiers.
*   **Custom Migration Pipelines**: Building and monitoring automated jobs to move data based on usage patterns or age.
*   **Complex Verification**: Implementing audits to ensure data integrity during movement.
*   **Cost Modeling**: Significant effort spent analyzing query frequency vs. retrieval latency trade-offs.

## Simplified Strategy (The "Aggregator" Model)
To minimize human intervention and maintenance (aligning with the `Maintenance Efficiency` principle), we will adopt the following assumptions:

### 1. Role Definition: Aggregator, Not System of Record
We are not a permanent vault for municipal records. Our role is to provide an accessible, queryable interface for existing dataholders. This removes the legal and operational burden of "Data Durability."

### 2. Separation of Concerns (Large vs. Small Data)
*   **PostgreSQL**: Reserved exclusively for small, high-velocity metadata (e.g., meeting titles, dates, resolution numbers, and pointers).
*   **Object Storage (S3/R2)**: All "large" source files (PDFs, images, meeting recordings) must be uploaded directly to object storage at the point of ingestion.

### 3. Infrastructure-Led Archiving (Time-based)
Instead of custom application logic, we will leverage cloud-native lifecycle policies.
*   **Threshold**: Data older than 10 years will be transitioned to colder storage tiers (e.g., Glacier/Archive). Given the current scope only covers up to 1 year of history, this threshold provides a ~9-year buffer for re-evaluation.
*   **Implementation**: Rely on S3/R2 Lifecycle Rules to handle the transition automatically without writing custom migration code.

## Benefits of This Approach
*   **Reduced Database Bloat**: Keeps PostgreSQL small, making backups, vacuuming, and scaling trivial.
*   **Lower Maintenance Overhead**: Leverages existing cloud infrastructure for "moving" data (Automation Hierarchy: Fully Automated).
*   **Simplified Engineering**: Focuss the development effort on metadata orchestration rather than storage engineering.

## Future Implementation Roadmap

To transition from strategy to execution, the following areas require formal planning:

### 1. Orphaned Object Cleanup
Establish a mechanism to identify and purge files in object storage that were uploaded but never successfully committed to the PostgreSQL metadata store (handling ingestion failures).

### 2. Integrity Audit Strategy ("The Heartbeat")
Define a periodic task to verify that all object storage keys listed in PostgreSQL remain valid and that their content matches recorded checksums, mitigating `Source Rot`.

### 3. Standardized Metadata Contract
Formalize the required metadata schema (e.g., `checksum_sha256`, `file_size`, `mime_type`) to ensure consistency across all ingestion pipelines and technical enforceability of the "Separation of Concerns."
