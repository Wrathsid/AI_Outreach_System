-- UX Improvements: Database Schema Updates
-- Run this in Supabase SQL Editor

-- 1. Add pipeline tracking columns
ALTER TABLE candidates 
ADD COLUMN IF NOT EXISTS added_to_pipeline BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS added_at TIMESTAMPTZ;

-- 2. Add email validity status
ALTER TABLE candidates 
ADD COLUMN IF NOT EXISTS email_status TEXT CHECK (email_status IN ('verified', 'risky', 'invalid', 'unknown')) DEFAULT 'unknown';

-- 3. Add sent tracking columns
ALTER TABLE candidates 
ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS reply_received BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS reply_at TIMESTAMPTZ;

-- 4. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_candidates_pipeline ON candidates(added_to_pipeline) WHERE added_to_pipeline = TRUE;
CREATE INDEX IF NOT EXISTS idx_candidates_sent ON candidates(sent_at DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_candidates_replied ON candidates(reply_received) WHERE reply_received = TRUE;

-- 5. Backfill email_status based on existing email_confidence
UPDATE candidates 
SET email_status = CASE 
    WHEN email_confidence >= 80 THEN 'verified'
    WHEN email_confidence >= 50 THEN 'risky'
    WHEN email_confidence IS NOT NULL AND email_confidence < 50 THEN 'invalid'
    ELSE 'unknown'
END
WHERE email_status = 'unknown' OR email_status IS NULL;
