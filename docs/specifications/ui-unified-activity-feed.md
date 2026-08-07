# UI Specification: Unified Activity Feed (The "Quick Scan" View)

## 1. High Level Description
This UI is a streamlined, mobile-responsive dashboard featuring a chronological stream of recent town activities (e.g., new meeting minutes, agenda postings, approved resolutions). Each entry consists of a high-level, standardized summary card generated from the ingestion pipeline. To minimize cognitive burden, cards use Tailwind CSS badges to categorize activity types (e.g., "Zoning," "Budget").

Crucially, every card includes a prominent, one-click "View Official Source" button that links directly to the original PDF or YouTube recording, satisfying the resident's need for immediate verification without deep diving into archives. This "low-friction" approach allows the resident to stay informed during brief breaks throughout their day using HTMX-powered dynamic updates that avoid full page re-loads.

## 2. Visual Mockup (ASCII)

```text
___________________________________________________________________________
| [ Logo ]  Search: [__________]    [ All ] [ Zoning ] [ Budget ] [ Help ] | <--- Global Nav (HTMX Filter)
|__________________________________________________________________________|
|                                                                          |
|  RECENT ACTIVITY                                          [ Dashboard ]  |
| ________________________________________________________________________ |
| | [ ZONING ] 2 hours ago                                               | |
| | New Site Plan: 123 Main St.                                          | |
| | Address: 123 Main St.                                                | |
| | Summary: Proposed change to R-1 residential to C-1 commercial...     | |
| | [ View Official Source (PDF) ]                                       | |
| |______________________________________________________________________| | <--- Activity Card
|                                                                          |
| ________________________________________________________________________ |
| | [ BUDGET ] 5 hours ago                                               | |
| | Resolution #2026-42: Annual Audit Approval                           | |
| | Summary: The board has officially approved the...                    | |
| | [ View Official Source (PDF) ]                                       | |
| |______________________________________________________________________| |
|                                                                          |
| ________________________________________________________________________ |
| | [ LEGAL ] 1 day ago                                                  | |
| | Public Notice: Rezoning of District A                                | |
| | Address: N/A                                                         | |
| | Summary: Notice of upcoming hearing regarding...                     | |
| | [ View Official Source (PDF) ]                                       | |
| |______________________________________________________________________| |
|                                                                          |
| ________________________________________________________________________ |
| | [ CODE ] 3 days ago                                                  | |
| | Amendment to Section 12.4: Street Trees                              | |
| | Summary: Update regarding planting requirements for...               | |
| | [ View            ]                                                  | |
| |______________________________________________________________________| |
|                                                                          |
|  [ Sidebar - Upcoming (Desktop Only) ]                                   |
|  - Aug 12: Planning Board Meeting                                        |
|  - Aug 15: ZBA Public Hearing                                            |
|__________________________________________________________________________|
```

## 3. Component Level Descriptions

### 3.1 Global Navigation Header
*   **Role**: Primary entry point for navigation and filtering.
*   **Technologies**: Tailwind CSS (styling), HTMX (filtering logic).
*   **Elements**:
    *   `Search Bar`: Text input to search by keyword/address (`hx-trigger="keyup changed delay:500ms"`).
    *   `Category Filters`: A group of buttons representing activity types (`Zoning`, `Budget`, `Legal`, `Code`). Clicking a filter sends an HTMX request to the backend to refresh only the feed container with filtered results.

### 3.2 The Activity Feed (Main Container)
*   **Role**: The central container hosting the chronological list of cards.
*   **Technologies**: FastAPI (Backend rendering), HTMX (`hx-target`).
*   **Behavior**: This container is the even the target for all filtering and search updates. It should implement a "loading" state (e.CSS class via `htmx-indicator`) when new data is being fetched.

### 3.3 The Activity Card
*   **Role**: Modular unit of information representing one event.
*   **Elements**:
    *   `Type Badge`: A color-coded Tailwind CSS badge indicating the category (e.g., Blue for `Zoning`, Green for `Budget`, Red for `Legal`, Purple for `Code`).
    *   `Timestamp`: Relative time string (e.g., "2 hours ago").
        `.   `Title`: Bold, high-level heading of the event.
    *   `Address`: (Optional) The specific geographic location associated with the event (e.g., "123 Main St."). Shown primarily for Zoning and Planning updates.
    *   `Summary Text`: A 1-3 sentence snippet extracted by the pipeline.
    *   `Source Button`: An anchor tag (`<a>`) styled as a button that opens the `source_url` in a new browser tab.

### 3.4 Sidebar: Upcoming Milestones (Desktop Only)
*   **Role**: Contextual awareness of future town events.
*   **Behavior**: Hidden or moved to the bottom of the stack on mobile devices using Tailwind responsive utilities (`hidden lg:block`).

## 4. Interaction Descriptions

| User Action | System Response | Technology/Logic |
| :--- | :--- | :--- |
| **Click Category Filter** | The main Activity Feed container refreshes to show only items matching that category without a page reload. | `hx-get="/feed?category=..."` |
| **Type in Search Bar** | As the user types, the feed updates dynamically (debounced) to match keywords. | `hx-trigger="keyup changed delay:500ms"` |
| **Click "View Source"** | The browser opens the official PDF or YouTube URL in a new tab/window. | Standard `</strong>` |
| **Scroll to bottom of feed** | If more history is available, the system fetches the next page of results and appends them via infinite scroll. | `hx-trigger="revealed"` |

## 5. User Flows (Proactive Resident)

### Flow A: The Morning Briefing (Quick Scan)
1.  **Start**: User opens the web app on their mobile device during a coffee break.
2.  **Action**: User glances at the `Activity Feed` to see if any new badges have appeared since yesterday.
3.  **Observation**: They notice a new `[ ZONING ]` badge from "1 hour ago".
4.  **End**: They close the app, having stayed informed in < 30 seconds.

### Flow B: The Deep Dive (Verification)
1.  **Start**: User sees a summary about a proposed change to "123 Main St."
2.  **Action**: Suspicious of how this affects their property value, the user clicks **[ View Official Source (PDF) ]**.
3.  **Process**: The browser opens the official Town Clerk PDF.
4.   **End**: User reads the technical legal language in the original document to confirm the summary's accuracy.

## 6. Testable Feature Requirements

### Functional Requirements
*   [ ] **Requirement F1 (Filtering)**: Clicking a category button must update the feed with *only* relevant items within < 500ms.
*   [ ] **Requirement F2 (Search)**: Entering a specific address (e.g., "123 Main") must filter out all non-matching cards.
*   [ ] **Requirement F3 (Source Integrity)**: Every card *must* render an `<a>` tag with a valid, clickable URL pointing to the source document.
*   [ ] **Requirement F4 (Responsiveness)**: On viewports < 640px, the Sidebar must be hidden/relocated, and the Header must collapse into a hamburger menu or simplified bar.

### UI/UX Requirements
*   [ ] **Requirement U1 (Visual Feedback)**: A loading spinner or skeleton screen must be visible during HTMX requests to prevent the user from thinking the app is frozen.
*   [ ] **Requirement U2 (Readability)**: Text contrast between badges and backgrounds must meet WCAG AA standards.
*   [ ] **Requirement U3 (Performance)**: The initial page load of the feed should be < 1s on a standard 4G connection.

## TODOs

### Decisions Needed
- [ ] **Decision**: Should we implement "Infinite Scroll" or simple "Load More" pagination? (Infinite scroll is smoother but harder to implement with accessibility in mind).
- [ ] **Decision**: What is the specific color palette for categories? (e.g., Zoning = Blue, Budget = Green, Legality = Red).

### Clarifications Needed
- [ ] **Clarification**: Do we need "User Accounts" to allow residents to "Follow" specific categories, or should the feed remain purely public and anonymous?
- [ ] **Clarification**: Should the summary text be expandable within the card, or is a single snippet enough for the "Quick Scan" phase?

### Identified Gaps (For Future Consideration)
*   **Video Integration**: Currently, we only provide links to YouTube. While simple, an embedded player would reduce friction but increase complexity.
*   **Spatial Context**: Adding an interactive map view of all active zoning/planning projects could be powerful, but for now, we rely on the text-based address field and external GIS tools.
*   **Real-time Alerting**: The system is a periodic poll (a few times per day), not a real-time stream. Future iterations could introduce push notifications or email alerts via the "Notify Me" mechanism.
