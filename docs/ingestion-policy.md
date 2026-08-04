# Ingestion Policy: Source Validation & Fact Integrity

This document defines the standards for data veracity and source trustworthiness. All municipality adapters must adhere to these principles to uphold the **Verifiable Truth** principle of the `on-the-board` Constitution.

## 1. Data Veracity Standards

To minimize complexity and ensure high integrity, ingestion is limited to "Ground Truth" facts. We intentionally exclude interpretative or subjective data types.

### Permitted Data Types (Ground Truth)
The following categories are considered verifiable:
*   **Temporal Facts**: Meeting dates, start/end times, resolution deadlines.
*   **Procedural Facts**: Presence of quorum, motion status (carried/failed), vote counts.
*   **Identification Facts**: Resolution numbers, ordinance IDs, official names of officials or committees.
*   **Structural Facts**: Agenda items, committee assignments, public hearing notices.

### Prohibited Data Types (Interpretative)
The following must be excluded from automated ingestion:
*   **Opinions/Sentiment**: Comments made during public comment periods that lack a recorded vote outcome.
*   **Summaries**: Descriptive text that interprets the *intent* or *impact* of a resolution unless explicitly part of the official record.
*   **Speculation**: Unverified reports of future actions not yet formalized in minutes or notices.

## 2. Source Trustworthiness Criteria

An adapter is only as reliable as its source. All data extraction must originate from a "Trusted Source."

### Trusted Source Requirements
A source is considered trusted if it meets at least one of the following:
*   **Official Domain**: The URL belongs to an official `.gov`, `.ny.us`, or a verified municipality-managed domain (e.g., `victor.ny.us`).
*   **Direct Linkage**: The data can be traced back to a specific, permanent resource (e.g., a PDF of meeting minutes or an archived web page).
*   **Verifiable Chain of Custody**: For third-party sources, there is a clear and documented path back to the official municipal record.

## 3. Mandatory Evidence Mapping

Every single data point ingested into the system **must** be accompanied by its "Evidence Anchor." An ingestion job is considered failed if it cannot provide:
1.  **Source URL**: The exact link where the information was found.
2.  **Point of Origin**: (If applicable) The specific page number, section header, or timestamp within the source file/stream.
3.  **Extraction Timestamp**: When the data was pulled from the source.

*Failure to provide this metadata violates the principle of Verifiable Truth and prevents the data from being committed to the database.*

## 4. Referential Data & Resource Pointers

To maintain the **Verifiable Truth** principle without unnecessary complexity, all "referential" information (e.g., links to full resolution texts, candidate biographies, or external ordinance PDFs) shall be treated as **Resource Pointers**.

### Implementation Standard
*   **Structure**: Use a `related_resources` field containing an array of objects.
*   **Requirement**: Every pointer must follow the same **Mandatory Evidence Mapping** rules as primary facts. This means every link *must* include its own `source_url` and, where possible, a specific `point_of_origin`.
*   **Scope**: Avoid creating separate database entities for links in the MVP phase; keep them as metadata attached to the primary verifiable fact.
