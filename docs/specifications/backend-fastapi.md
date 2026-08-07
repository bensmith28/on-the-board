# Backend Specification: FastAPI Layer

## 1. Overview
The FastAPI backend layer serves as the orchestration and presentation engine for the `on-the-board` project. Its primary responsibility is to serve processed data from the PostgreSQL database to the HTMX-powered frontend, providing a highly responsive and low-latency experience for residents. This layer bridges the gap between the raw ingested data (from Adapters) and the structured activity feed displayed in the UI.

The layer is designed to handle complex filtering and search requests, specifically serving HTML fragments (partials) to support the HTMX-driven frontend architecture.

## 2. API Structure & Endpoints

The API is designed around a RESTful approach, optimized for **Server-Side Rendering (SSR)** of components via HTMX. Most endpoints will return partial HTML snippets rather than pure JSON.

### 2.1 Feed Endpoints
These endpoints are the primary targets for the Activity Feed component and Global Navigation filters.

| Method | Endpoint | Description | HTMX Trigger/Context |
| :--- | :--- | :--- | :--- |
| `GET` | `/feed` | Returns the main activity feed container or a partial list of cards. | Initial page load / Category Filter |
| `GET` | `/feed/search` | Returns filtered activity cards based on search queries. | Search Bar (`keyup delay:500ms`) |
| `GET` | `/feed/category/{type}`| Returns filtered activity cards for a specific category (e.g., `zoning`, `budget`). | Category Filter Buttons |
| `GET` | `/feed/page/{page_num}`| Returns the next chunk of activity cards for infinite scrolling. | Infinite Scroll (`revealed`) |

### 2.2 Metadata & Utility Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/nav/categories` | Returns a list of available categories and their associated CSS badge colors for the Global Nav. |
| `GET` | `/health` | Health check endpoint for monitoring service availability. |

## 3. Entity Definitions

All entities are modeled using **SQLModel** (or SQLAlchemy) to interface with PostgreSQL.

### 3.1 ActivityItem (The Core Entity)
This entity represents a single, verifiable event or record in the town's history, as defined by the `IngestionResult` contract.

| Field | Type | Description |
| :---            | :--- | :--- |
| `id` | UUID | Primary key. |
| `type` | String (Enum) | The category of activity (e.g., `ZONING`, `BUDGET`, `LEGAL`, `CODE`, `NEWS`). Corresponds to UI badges. |
| `title` | String | High-level, descriptive title of the event. |
| `summary` | Text | A 1-3 sentence snippet extracted by the ingestion pipeline. |
| `timestamp` | DateTime | The official date/time of the event (e.g., meeting date, publication date). |
| `source_url` | String (URL) | The direct link to the original source (PDF, YouTube, etc.) for verification. |
| `address` | String (Optional)| Geographic context (if applicable), such as a site plan address. |
| `metadata` | JSONB | A flexible payload containing source-specific attributes (e.g., Board name, meeting duration, author). |
| `created_at` | DateTime | Internal timestamp for when the record was ingested. |

### 3.2 Ingestion Metadata (Reference)
To ensure consistency with the Adapter layer, the `metadata` JSONB field will follow a schema derived from known sources:
- **Meeting Records**: `{ "board": "Planning", "meeting_type": "Regular" }`
- **Zoning/Land Use**: `{ "application_id": "12345", "status": "Pending" }`
- **Press Releases**: `{ "author": "Town Clerk", "department": "Communications" }`

## 4. Contracts (Backend <-> Presentation)

### 4.1 Response Format: The Partial Pattern
To support HTMX, the backend must adhere to the following response contract:
- **Content-Type**: `text/html`.
- **Payload**: An HTML fragment representing one or more `ActivityCard` components.
- **Empty State**: If no results are found for a filter/search, return a partial containing an `<div class="empty-state">No activities found.</div>` message.

### 4.2 Component: ActivityCard (HTML Template)
The backend is responsible for rendering this component using Jinja2 templates.

```html
<div class="activity-card border p-4 rounded shadow" id="card-{{ item.id }}">
    <span class="badge badge-{{ item.type|lower }}">{{ item/item.type }}</span>
    <span class="text-sm text-gray-500">{{ item.timestamp|relativedelta }}</span>
    <h3 class="font-bold text-lg">{{ item.title }}</h3>
    {% if item.address %}
    <p class="text-sm">Address: {{ item.address }}</p>
    {% endif %}
    <p class="summary">{{ item.summary }}</p>
    <a href="{{ item.source_url }}" target="_blank" class="btn-source">
        View Official Source ({{ item.source_type|default('PDF') }})
    </a>
</div>
```

### 4.3 Loading States
The backend must support the `htmx-indicator` pattern. When a request is in flight, the frontend will show a spinner. The backend must ensure that partials are returned quickly to prevent perceived latency, or provide error-handling fragments if a service (like the Search index) is unavailable.

## 5. Infrastructure & Security
- **Authentication**: Initially session-based (Cookie) for simplicity and compatibility with HTMX.
- **Database Access**: Use an asynchronous SQLAlchemy driver (`asyncpg`) to interact with PostgreSQL.
- **Search Implementation**: For the initial version, use PostgreSQL `tsvector` for full-text search on `title`, `summary`, and `address`. Prepare for Phase 3 integration with `pgvector`.
