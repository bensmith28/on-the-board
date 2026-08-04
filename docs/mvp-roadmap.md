# MVP Roadmap: on-the-board

This document outlines the strategic path for developing the Minimum Viable Product (MVP) of the `on-the-board` project, moving from initial concept to a functional, automated data pipeline.

## 1. User Personas
*Identify the different groups of people who might interact with the system.*

- [ ] **The Proactive Resident (Primary Persona)**: A local Victor, NY resident who cares about community governance but cannot attend every meeting. They want to stay informed about board decisions, upcoming zoning changes, and new town ordinances without manually checking multiple websites or reading through dozens of PDFs.
    - *Alternative Problem Focus*: Reducing the cognitive/time burden of monitoring high-frequency board cadences.
    - *Alternative Problem Focus*: Bridging the verification gap by providing direct links to official "Ground Truth" records.
- [ ] **The Local Developer/Real Estate Professional**: Someone whose business depends on monitoring Planning Board and ZBA activities (e.g., land use applications, site plans). They need timely, structured updates on project statuses and public hearing notices to prepare for impact or opportunity.
- [ ] **The Local Journalist / Community Blogger**: A person providing local news coverage who needs a quick way to find "Ground Truth" facts (meeting dates, vote counts, resolution numbers) across various sources like meeting minutes, press releases, and legal notices to verify stories.
- [ ] **The Civic Activist / Community Organizer**: An individual organizing around specific local issues (e.g., environmental conservation, budget allocation). They use the platform to track historical patterns in board votes, committee assignments, and official communications to build evidence-based arguments.
- [ ] **The Municipal Administrator (Secondary/System Stakeholder)**: While not the primary consumer of the *public* interface, they are interested in a "recurrent template" that could potentially serve as an automated way to archive and present town data in a more accessible format, reducing manual inquiries.

## 2. Critical Persona and MVP Problem Statement
*Define the primary user and the specific, high-impact problem this MVP will solve for them.*

- **Primary Persona**: The Proactive Resident
- **Problem Statement**: Local governance information is fragmented across multiple unindexed, disparate sources (CivicPlus, YouTube, PDF archives, and physical notices), making it nearly impossible for residents to maintain a cohesive understanding of town activity without significant manual effort.

## 3. Critical Feature Set (MVP)
*Identify the minimum set of features required to solve the problem statement for the primary persona.*

### MVP Features
- [ ] **Unified Information Feed**: As a resident, I want to see all recent town activity in one central feed so that I don't have to visit multiple websites like CivicPlus or YouTube.
- [ ] **Standardized Summaries**: As a resident, I want all updates (from PDFs, web pages, or notices) to appear in the same consistent format so that I can quickly scan for key details.

### Post-MVP Features

#### High Value
- [ ] **Topic Filtering**: As a resident, I want to filter the feed by board type (e.g., "ZBA" or "Planning") so that I can ignore information irrelevant to me.
- [ ] **One-Click Verification**: As a resident, I want to click directly from an update to its original official source (like a PDF) so that I can easily verify the facts.

#### Additive
- [ ] **Automated Alerts**: As a resident, I want to receive notifications when new items are added to specific categories so that I stay updated without manual checking.
- [ ] **Concept Search**: As a resident, I want to search for topics like "zoning" across all documents, even if they don't use my exact keywords, to find related information easily.

## 4. System Components

### 1. Ingestion Layer (The "Adapters")
- **Source Adapters**: Python modules for specific sources (e.g., CivicPlus/Agenda Center Scraper).
- **Standardization Logic**: Mapping raw data into the unified schema (Title, Date, Content, Source URL, Evidence Anchor).

### 2. Storage Layer
- **Database Schema**: PostgreSQL with `JSONB` for flexible payload storage.

### 3. Orchestration Layer
- **Task Runner/Scheduler**: Python-based engine (e.g., `schedule`) to manage ingestion cadence.

### 4. Presentation Layer
- **Backend API**: FastAPI service serving aggregated data.
- **Web Interface**: HTMX and Tailwind CSS frontend for the unified feed.

## 5. Phased Development Plan

### Phase 1: Foundation & Initial Ingestion
*Goal: Establish core infrastructure and prove single-source ingestion.*
- [ ] **Task 1**: Implement PostgreSQL schema with `JSONB` support.
- [ ] **Task 2**: Develop the first "Type A" Adapter (Planning Board HTML scraper) with standardization logic.
- [ ] **Task 3**: Build a basic Python Task Runner to execute the adapter on a/a timer.
- **Verification**: Successful ingestion of Planning Board status into the DB and visible in structured logs.

### Phase 2: The Unified Feed (MVP Launch)
*Goal: Deliver the primary user value through a web interface.*
- [ ] **Task 1**: Develop the FastAPI endpoints to query and serve the aggregated feed.
- [ ] **Task 2**: Build the HTMX/Tailwind frontend to render the "Unified Information Feed" as a single, scrollable list.
- **Verification**: A resident can visit a URL and see a populated list of recent activity from the first adapter.

### Phase 3: Scalability & Expansion
*Goal: Expand source coverage and automate maintenance.*
- [ ] **Task 1**: Implement Meeting Minutes & Agendas Adapter (PDF parsing + polling pattern).
- [ ] **Task 2**: Implement Press Releases / News Adapter (HTML scraping).
- [ ] **Task 3**: Implement "High Value" filtering logic in the API/Frontend.
- **Verification**: Multiple disparate sources appearing in a single, filterable dashboard without manual interaction.
