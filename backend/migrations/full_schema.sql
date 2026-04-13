-- ============================================================
-- AI Outreach System — Full Database Schema
-- Run this in Supabase SQL Editor for initial setup
-- ============================================================

-- ====================
-- 1. CANDIDATES TABLE
-- ====================
CREATE TABLE IF NOT EXISTS candidates (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    title TEXT,
    company TEXT,
    location TEXT,
    email TEXT,
    generated_email TEXT,
    email_confidence INTEGER,
    linkedin_url TEXT,
    avatar_url TEXT,
    match_score INTEGER DEFAULT 0,
    summary TEXT,
    tags TEXT[] DEFAULT '{}',
    status TEXT DEFAULT 'new',
    email_source TEXT DEFAULT 'none',
    sent_at TIMESTAMPTZ,
    reply_received BOOLEAN DEFAULT FALSE,
    reply_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================
-- 2. DRAFTS TABLE
-- ====================
CREATE TABLE IF NOT EXISTS drafts (
    id BIGSERIAL PRIMARY KEY,
    candidate_id BIGINT REFERENCES candidates(id) ON DELETE CASCADE,
    subject TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    status TEXT DEFAULT 'draft',
    candidate_name TEXT,
    candidate_company TEXT,
    intent TEXT,
    temperature DOUBLE PRECISION,
    signal_used TEXT,
    variant_id TEXT,
    reply_status TEXT DEFAULT 'no_reply',
    generation_params JSONB,
    time_to_read INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================
-- 3. DRAFT_EDITS TABLE (RAG Feedback)
-- ====================
CREATE TABLE IF NOT EXISTS draft_edits (
    id BIGSERIAL PRIMARY KEY,
    candidate_id BIGINT REFERENCES candidates(id) ON DELETE CASCADE,
    original_text TEXT NOT NULL,
    edited_text TEXT NOT NULL,
    contact_type TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================
-- 4. USER_SETTINGS TABLE
-- ====================
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    full_name TEXT DEFAULT '',
    company TEXT DEFAULT '',
    role TEXT DEFAULT '',
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================
-- 5. BRAIN_CONTEXT TABLE
-- ====================
CREATE TABLE IF NOT EXISTS brain_context (
    id INTEGER PRIMARY KEY DEFAULT 1,
    extracted_skills JSONB DEFAULT '[]'::jsonb,
    resume_text TEXT DEFAULT '',
    formality INTEGER DEFAULT 75,
    detail_level INTEGER DEFAULT 30,
    use_emojis BOOLEAN DEFAULT FALSE,
    portfolio_summary TEXT,
    preferred_tone TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================
-- 6. ACTIVITY_LOG TABLE
-- ====================
CREATE TABLE IF NOT EXISTS activity_log (
    id BIGSERIAL PRIMARY KEY,
    action_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    candidate_id BIGINT REFERENCES candidates(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================
-- 7. DASHBOARD_STATS TABLE
-- ====================
CREATE TABLE IF NOT EXISTS dashboard_stats (
    id BIGSERIAL PRIMARY KEY,
    weekly_goal_percent INTEGER DEFAULT 0,
    people_found INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    replies_received INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================
-- 8. SENT_OPENERS TABLE (Deduplication)
-- ====================
CREATE TABLE IF NOT EXISTS sent_openers (
    id BIGSERIAL PRIMARY KEY,
    opener_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================
-- INDEXES
-- ====================
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_company ON candidates(company);
CREATE INDEX IF NOT EXISTS idx_candidates_created ON candidates(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_drafts_candidate_id ON drafts(candidate_id);
CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status);
CREATE INDEX IF NOT EXISTS idx_drafts_variant_id ON drafts(variant_id);
CREATE INDEX IF NOT EXISTS idx_drafts_created ON drafts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_log_type ON activity_log(action_type);
CREATE INDEX IF NOT EXISTS idx_activity_log_created ON activity_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sent_openers_hash ON sent_openers(opener_hash);
CREATE INDEX IF NOT EXISTS idx_sent_openers_created ON sent_openers(created_at DESC);

-- ====================
-- SEED DATA
-- ====================
INSERT INTO brain_context (id, extracted_skills, resume_text, formality, detail_level, use_emojis)
VALUES (1, '[]'::jsonb, '', 75, 30, false)
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_settings (id, full_name, company, role)
VALUES (1, '', '', '')
ON CONFLICT (id) DO NOTHING;

INSERT INTO dashboard_stats (weekly_goal_percent, people_found, emails_sent, replies_received)
SELECT 0, 0, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dashboard_stats LIMIT 1);
