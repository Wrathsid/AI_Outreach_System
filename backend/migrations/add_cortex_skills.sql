-- Add Cortex skills support and sent_openers deduplication table
-- Run this in the Supabase SQL Editor

-- sent_openers: tracks opener hashes to avoid repetition
CREATE TABLE IF NOT EXISTS sent_openers (
    id SERIAL PRIMARY KEY,
    opener_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sent_openers_hash ON sent_openers(opener_hash);
CREATE INDEX IF NOT EXISTS idx_sent_openers_created ON sent_openers(created_at DESC);
