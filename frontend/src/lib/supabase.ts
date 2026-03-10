import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://ajqwtrpcjtwyzbuanzkj.supabase.co',
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFqcXd0cnBjanR3eXpidWFuemtqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkzMDUwNjIsImV4cCI6MjA4NDg4MTA2Mn0.rQns63gBPJbZc8-zw85A7dJIv6kCKJfX92kONg2LmrA'
  )
}
