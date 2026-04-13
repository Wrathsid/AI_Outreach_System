-- Seed brain_context row (id=1) if missing
-- This MUST exist for draft generation to work
INSERT INTO brain_context (id, extracted_skills, resume_text, formality, detail_level, use_emojis)
VALUES (1, ARRAY[]::TEXT[], '', 75, 30, false)
ON CONFLICT (id) DO NOTHING;

-- Add columns that may be missing from older schema versions
ALTER TABLE brain_context ADD COLUMN IF NOT EXISTS portfolio_summary TEXT;
ALTER TABLE brain_context ADD COLUMN IF NOT EXISTS preferred_tone TEXT;

-- Seed user_settings row (id=1) if missing
INSERT INTO user_settings (id, full_name, company, role)
VALUES (1, '', '', '')
ON CONFLICT (id) DO NOTHING;

-- Seed dashboard_stats if empty
INSERT INTO dashboard_stats (weekly_goal_percent, people_found, emails_sent, replies_received)
SELECT 0, 0, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dashboard_stats LIMIT 1);
