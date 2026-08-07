-- Migration 001: Initial Schema
-- Creates ingested_records and sources_registry tables with indexes and constraints

-- ingested_records table
CREATE TABLE IF NOT EXISTS ingested_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL,
    locality VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    ingestion_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_url TEXT NOT NULL,
    point_of_origin TEXT NOT NULL,
    payload JSONB NOT NULL,
    embedding VECTOR(1536),
    CONSTRAINT chk_payload_keys CHECK (
        payload ? 'title' AND
        payload ? 'content_summary' AND
        payload ? 'raw_text' AND
        payload ? 'metadata' AND
        payload ? 'related_resources'
    )
);

-- sources_registry table
CREATE TABLE IF NOT EXISTS sources_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    locality VARCHAR(100) NOT NULL,
    config JSONB NOT NULL,
    last_run TIMESTAMPTZ,
    status VARCHAR NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_ingested_upsert_key
    ON ingested_records (source_url, point_of_origin);

CREATE INDEX IF NOT EXISTS idx_ingested_source_type
    ON ingested_records (source_type);

CREATE INDEX IF NOT EXISTS idx_ingested_locality
    ON ingested_records (locality);

CREATE INDEX IF NOT EXISTS idx_ingested_timestamp
    ON ingested_records (timestamp);

CREATE INDEX IF NOT EXISTS idx_ingested_source_type_locality
    ON ingested_records (source_type, locality);

CREATE UNIQUE INDEX IF NOT EXISTS idx_sources_type
    ON sources_registry (source_type);

CREATE INDEX IF NOT EXISTS idx_sources_locality
    ON sources_registry (locality);

CREATE INDEX IF NOT EXISTS idx_sources_status
    ON sources_registry (status);

-- UPSERT helper function (enforces FR-006 UPSERT behavior)
CREATE OR REPLACE FUNCTION upsert_ingested_record(
    p_source_type VARCHAR,
    p_locality VARCHAR,
    p_timestamp TIMESTAMPTZ,
    p_source_url TEXT,
    p_point_of_origin TEXT,
    p_payload JSONB
) RETURNS VOID AS $$
BEGIN
    INSERT INTO ingested_records (
        source_type, locality, timestamp, source_url, point_of_origin, payload, ingestion_timestamp
    )
    VALUES (
        p_source_type, p_locality, p_timestamp, p_source_url, p_point_of_origin, p_payload, now()
    )
    ON CONFLICT (source_url, point_of_origin) DO UPDATE SET
        payload = EXCLUDED.payload,
        ingestion_timestamp = EXCLUDED.ingestion_timestamp,
        timestamp = EXCLUDED.timestamp;
END;
$$ LANGUAGE plpgsql;
