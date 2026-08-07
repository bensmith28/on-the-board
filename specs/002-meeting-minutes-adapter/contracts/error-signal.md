# Contract: ErrorSignal (Adapter Error Output)

## Purpose

Defines the standardized error signaling contract that adapters use to communicate failure states to the orchestrator.

## Schema

### ErrorSignal

```json
{
  "status": "<success | transient_failure | permanent_failure>",
  "error_message": "<descriptive string or null>",
  "error_type": "<network_error | parsing_error | schema_inconsistency | null>"
}
```

## Field Definitions

| Field | Type | Required | Constraints |
|:---|:---|:---|:---|
| `status` | String | Yes | One of: `success`, `transient_failure`, `permanent_failure` |
| `error_message` | String \| null | Conditional | Required when `status` is `transient_failure` or `permanent_failure`; descriptive string for debugging |
| `error_type` | String \| null | Conditional | Required when `status` is `transient_failure` or `permanent_failure`; categorization of the error |

## Status Values

| Status | Meaning | Orchestrator Action |
|:---|:---|:---|
| `success` | Run completed; at least one record ingested | Update `last_run` in `sources_registry`; log run summary |
| `transient_failure` | Network or browser error; retryable | Retry with exponential backoff (up to 3 attempts); if all fail, trigger alert |
| `permanent_failure` | Parsing or schema error; not retryable | Skip the specific record; continue processing remaining records; log failure |

## Error Type Values

| Error Type | Meaning | Examples |
|:---|:---|:---|
| `network_error` | Network or browser execution failure | Timeout, connection refused, browser crash |
| `parsing_error` | PDF parsing failure | Corrupted PDF, unreadable text, unsupported format |
| `schema_inconsistency` | Output does not match IngestionResult contract | Missing required fields, invalid JSON in metadata |

## Retry Policy

For `transient_failure`:
1. Retry 1: Wait 1 second
2. Retry 2: Wait 2 seconds
3. Retry 3: Wait 4 seconds
4. After 3 failures: Mark run as failed; trigger persistent failure alert

## Persistent Failure Alert

If 3 consecutive runs fail for the same source, the adapter MUST trigger an alert via the Core Engine's error-handling system for manual investigation.
