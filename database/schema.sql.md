# Supabase Database Schema

Run this in your Supabase SQL Editor to create all required tables.

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Candidates table (people you want to reach out to)
CREATE TABLE candidates (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  title VARCHAR(255),
  company VARCHAR(255),
  location VARCHAR(255),
  email VARCHAR(255),
  linkedin_url VARCHAR(500),
  twitter_url VARCHAR(500),
  website_url VARCHAR(500),
  avatar_url TEXT,
  match_score INTEGER DEFAULT 0,
  summary TEXT,
  tags TEXT[], -- Array of tags like ['SaaS Recruiting', 'Python Specialist']
  last_active TIMESTAMP WITH TIME ZONE,
  status VARCHAR(50) DEFAULT 'new', -- new, contacted, replied, snoozed
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Drafts table (AI-generated email drafts)
CREATE TABLE drafts (
  id SERIAL PRIMARY KEY,
  candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
  subject VARCHAR(500) NOT NULL,
  body TEXT NOT NULL,
  status VARCHAR(50) DEFAULT 'draft', -- draft, sent, scheduled
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  sent_at TIMESTAMP WITH TIME ZONE
);

-- Sent emails log
CREATE TABLE sent_emails (
  id SERIAL PRIMARY KEY,
  candidate_id INTEGER REFERENCES candidates(id) ON DELETE SET NULL,
  to_email VARCHAR(255) NOT NULL,
  subject VARCHAR(500) NOT NULL,
  body TEXT NOT NULL,
  sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Brain context (user's professional info + Cortex Skills Engine)
CREATE TABLE brain_context (
  id SERIAL PRIMARY KEY,
  user_id UUID DEFAULT uuid_generate_v4(),
  resume_url TEXT,
  resume_text TEXT,
  linkedin_url VARCHAR(500),
  portfolio_url VARCHAR(500),
  anecdotes TEXT[],
  extracted_skills TEXT[] DEFAULT '{}',
  portfolio_summary TEXT,
  preferred_tone VARCHAR(100),
  formality INTEGER DEFAULT 75,
  detail_level INTEGER DEFAULT 30,
  use_emojis BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User settings (profile info)
CREATE TABLE user_settings (
  id SERIAL PRIMARY KEY,
  full_name VARCHAR(255) DEFAULT '',
  company VARCHAR(255) DEFAULT '',
  role VARCHAR(255) DEFAULT '',
  avatar_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sent openers for deduplication
CREATE TABLE sent_openers (
  id SERIAL PRIMARY KEY,
  opener_hash VARCHAR(64) NOT NULL,
  opener_text TEXT,
  embedding VECTOR(768),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Activity log for dashboard
CREATE TABLE activity_log (
  id SERIAL PRIMARY KEY,
  candidate_id INTEGER REFERENCES candidates(id) ON DELETE SET NULL,
  action_type VARCHAR(100) NOT NULL, -- 'draft_created', 'email_sent', 'profile_analyzed', 'lead_found'
  title VARCHAR(255) NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Stats for dashboard
CREATE TABLE dashboard_stats (
  id SERIAL PRIMARY KEY,
  stat_date DATE DEFAULT CURRENT_DATE,
  weekly_goal_percent INTEGER DEFAULT 0,
  people_found INTEGER DEFAULT 0,
  emails_sent INTEGER DEFAULT 0,
  replies_received INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert sample data for testing
INSERT INTO candidates (name, title, company, location, email, match_score, summary, tags, avatar_url, status) VALUES
('Sarah Jenkins', 'Senior Talent Acquisition', 'Google', 'San Francisco, CA', 'sarah.jenkins@google.com', 92, 
 'Sarah has actively hired for Backend roles in the last 3 months. She recently posted about "Scaling engineering teams" which aligns with your product offering.', 
 ARRAY['SaaS Recruiting', 'Python Specialist', 'Remote Friendly', 'Ex-Stripe'],
 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200', 'new'),
('John Smith', 'Engineering Manager', 'Meta', 'New York, NY', 'john.smith@meta.com', 87,
 'John leads a team of 15 engineers and is expanding the backend infrastructure team.',
 ARRAY['Backend', 'Distributed Systems', 'Leadership'],
 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200', 'new'),
('Emily Chen', 'Head of Recruiting', 'Stripe', 'San Francisco, CA', 'emily.chen@stripe.com', 85,
 'Emily is building out the engineering org and looking for senior talent.',
 ARRAY['Fintech', 'Engineering Recruiting', 'Startup'],
 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200', 'new');

INSERT INTO drafts (candidate_id, subject, body) VALUES
(1, 'Regarding your search for Backend leads...', 'Hi Sarah, saw your post about scaling the python team at Google. I think our tool could help automate the initial screening...'),
(2, 'Quick question about your team growth', 'Hi John, I noticed your team is expanding and thought you might be interested in...'),
(3, 'Connecting on Python development', 'Hi Emily, your recent post about distributed systems caught my attention...');

INSERT INTO activity_log (candidate_id, action_type, title, description) VALUES
(1, 'draft_created', 'Drafted email to Sarah Jenkins', 'AI generated based on LinkedIn profile'),
(NULL, 'lead_found', 'Found 3 new design leads', 'San Francisco Area • Senior Level');

INSERT INTO dashboard_stats (weekly_goal_percent, people_found, emails_sent) VALUES
(82, 14, 5);

-- Create Row Level Security policies (optional but recommended)
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE sent_emails ENABLE ROW LEVEL SECURITY;

-- Create indexes for performance
CREATE INDEX idx_candidates_status ON candidates(status);
CREATE INDEX idx_drafts_candidate ON drafts(candidate_id);
CREATE INDEX idx_activity_created ON activity_log(created_at DESC);
```

## Environment Variables

Add these to your `.env` file:

```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_key (optional, for AI drafts)
```

Get these from:
1. Go to https://supabase.com
2. Create a project (or use existing)
3. Go to Settings → API
4. Copy the Project URL and anon/public key
