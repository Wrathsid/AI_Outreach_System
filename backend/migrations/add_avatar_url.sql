-- Migration: Add avatar_url column to user_settings table
-- Run this against your Supabase database before using the avatar feature

ALTER TABLE user_settings 
ADD COLUMN IF NOT EXISTS avatar_url TEXT DEFAULT NULL;

-- Create storage bucket for avatars (run via Supabase Dashboard or SQL)
-- INSERT INTO storage.buckets (id, name, public) 
-- VALUES ('avatars', 'avatars', true)
-- ON CONFLICT (id) DO NOTHING;
