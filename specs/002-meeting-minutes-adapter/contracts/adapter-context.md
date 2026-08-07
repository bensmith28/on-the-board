# Contract: Adapter Context (Adapter Input)

## Purpose

Defines the standardized input contract that the orchestrator passes to every adapter execution.

## Schema

### AdapterContext

```json
{
  "locality": "<string>",
  "config": {
    "base_url": "<valid URL>",
    "boards": ["<string>", ...],
    "selectors": {
      "year_dropdown": "<CSS selector>",
      "document_links": "<CSS selector>",
      "board_indicator": "<CSS selector>"
    },
    "max_days_back": "<integer, default: 365>",
    "consecutive_skip_threshold": "<integer, default: 5>"
  },
  "last_run_timestamp": "<ISO 8601 timestamp or null>"
}
```

## Field Definitions

| Field | Type | Required | Description |
|:---|:---|:---|:---|
| `locality` | String | Yes | Municipality/entity name (e.g., `Victor, NY`) |
| `config.base_url` | String | Yes | Base URL of the Agenda Center (e.g., `https://www.townofvictorny.gov/AgendaCenter`) |
| `config.boards` | Array[String] | Yes | List of board names to scan (e.g., `["Town Board", "Planning Board", "ZBA"]`) |
| `config.selectors` | Object | Yes | CSS selectors for DOM elements in the Agenda Center |
| `config.max_days_back` | Integer | No | Maximum days to scan into the past (default: 365) |
| `config.consecutive_skip_threshold` | Integer | No | Number of consecutive already-recorded documents to stop scanning (default: 5) |
| `last_run_timestamp` | String \| null | Yes | ISO 8601 timestamp of the previous successful run; `null` for first run |

## Source Registry Configuration

The `config` is stored in the `sources_registry.config` column. Initial configuration for Town of Victor:

```json
{
  "base_url": "https://www.townofvictorny.gov/AgendaCenter",
  "boards": ["Town Board", "Planning Board", "ZBA"],
  "selectors": {
    "year_dropdown": "#year-select",
    "document_links": ".document-list a",
    "board_indicator": ".board-name"
  },
  "max_days_back": 365,
  "consecutive_skip_threshold": 5
}
```
