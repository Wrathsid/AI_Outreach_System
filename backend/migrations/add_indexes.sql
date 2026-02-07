-- Database indexes for performance optimization (Priority 5)
-- Run this SQL in your Supabase SQL editor

-- Index on drafts.candidate_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_drafts_candidate_id ON drafts(candidate_id);

-- Index on candidates.status for filtering
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);

-- Composite index on activity_log for time-based queries
CREATE INDEX IF NOT EXISTS idx_activity_log_candidate_timestamp ON activity_log(candidate_id, timestamp DESC);

-- Add reply_timestamp column for analytics (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'candidates' AND column_name = 'reply_timestamp'
    ) THEN
        ALTER TABLE candidates ADD COLUMN reply_timestamp TIMESTAMPTZ;
    END IF;
END $$;
