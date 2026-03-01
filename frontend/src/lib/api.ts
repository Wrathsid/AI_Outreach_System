// API Client for Intelligent Outreach Backend
import { createClient } from '@/lib/supabase';

// ── In-memory request cache ──────────────────────────────────────────
// Prevents duplicate fetches during navigation and page transitions.
// Each entry expires after its TTL (ms).
interface CacheEntry { data: unknown; timestamp: number; }
const apiCache = new Map<string, CacheEntry>();
const DEFAULT_CACHE_TTL = 30_000; // 30 seconds

export function getCached<T>(key: string): T | null {
  const entry = apiCache.get(key);
  if (!entry) return null;
  if (Date.now() - entry.timestamp > DEFAULT_CACHE_TTL) {
    apiCache.delete(key);
    return null;
  }
  return entry.data as T;
}

export function setCache(key: string, data: unknown, ttl = DEFAULT_CACHE_TTL) {
  apiCache.set(key, { data, timestamp: Date.now() });
  // Auto evict after TTL
  setTimeout(() => apiCache.delete(key), ttl);
}

export function invalidateCache(key?: string) {
  if (key) apiCache.delete(key);
  else apiCache.clear();
}
// ─────────────────────────────────────────────────────────────────────

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const supabase = createClient();
  const { data: { session } } = await supabase.auth.getSession();
  
  const headers = new Headers(options.headers || {});
  if (session?.access_token) {
    headers.set('Authorization', `Bearer ${session.access_token}`);
  }
  
  return fetch(url, { ...options, headers });
}

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// Types
export interface Candidate {
  id: number;
  name: string;
  title?: string;
  company?: string;
  location?: string;
  email?: string;
  generated_email?: string;  // AI-generated email
  email_confidence?: number;  // 0-100
  linkedin_url?: string;
  avatar_url?: string;
  match_score: number;
  summary?: string;
  tags?: string[];
  status?: string;
  email_source?: 'verified' | 'generated' | 'none';
  // UX Improvement fields
  email_status?: 'verified' | 'risky' | 'invalid' | 'unknown';
  added_to_pipeline?: boolean;
  sent_at?: string;
  reply_received?: boolean;
  reply_at?: string;
}

export interface Draft {
  id: number;
  candidate_id: number;
  subject: string;
  body: string;
  status: string;
  candidate_name?: string;
  candidate_company?: string;
  candidate_title?: string;
  candidate_email?: string;
  candidate_generated_email?: string;
  candidate_email_confidence?: number;
  email_source?: 'verified' | 'generated' | 'none';
  match_score?: number;
  created_at?: string;
  generation_params?: {
    fingerprint?: string;
    prompt_version?: string;
    reason?: string;
    skill_count?: number;
    [key: string]: unknown;
  };
}

export interface ActivityLog {
  id: number;
  action_type: string;
  title: string;
  description?: string;
  created_at: string;
  candidate_id?: number;
}

export interface FunnelStats {
  funnel: { stage: string; count: number; percent: number }[];
  conversions: { found_to_contacted: number; contacted_to_replied: number };
  total_candidates: number;
}

export interface DashboardStats {
  weekly_goal_percent: number;
  people_found: number;
  emails_sent: number;
  account_health: number;
  is_safe: boolean;
  safety_reason?: string;
  recent_leads: { date: string; count: number }[];
  top_industries: { name: string; value: number }[];
}

export interface UserSettings {
  full_name: string;
  company: string;
  role: string;
  avatar_url?: string | null;
}

// API Functions
export const api = {
  // Health check
  async health() {
    const res = await fetchWithAuth(`${API_BASE}/`);
    return res.json();
  },

  // Settings
  getSettings: async (): Promise<UserSettings> => {
    const res = await fetchWithAuth(`${API_BASE}/settings`);
    return res.json();
  },
  
  updateSettings: async (settings: UserSettings): Promise<boolean> => {
    try {
      const res = await fetchWithAuth(`${API_BASE}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  uploadAvatar: async (file: File): Promise<{ avatar_url: string; status: string } | null> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetchWithAuth(`${API_BASE}/settings/avatar`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Upload failed');
      return res.json();
    } catch {
      return null;
    }
  },

  removeAvatar: async (): Promise<boolean> => {
    try {
      const res = await fetchWithAuth(`${API_BASE}/settings/avatar`, { method: 'DELETE' });
      return res.ok;
    } catch {
      return false;
    }
  },

  // Discovery
  discoverCandidates: async (role: string): Promise<unknown[]> => {
    try {
        const res = await fetchWithAuth(`${API_BASE}/discover?role=${encodeURIComponent(role)}`);
        if (!res.ok) throw new Error('API error');
        return res.json();
    } catch {
        return [];
    }
  },

  crawlWebsite: async (url: string): Promise<unknown> => {
    const res = await fetchWithAuth(`${API_BASE}/discover/crawl`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ domain: url })
    });
    return res.json();
  },

  guessEmailPattern: async (firstName: string, lastName: string, domain: string): Promise<unknown> => {
    const res = await fetchWithAuth(`${API_BASE}/discover/pattern`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ first_name: firstName, last_name: lastName, domain })
    });
    return res.json();
  },

  // Candidates
  async pruneCandidates(days: number = 7): Promise<unknown> {
    const response = await fetchWithAuth(`${API_BASE}/candidates/prune?days=${days}`, {
      method: "DELETE",
    });
    return response.json();
  },

  async getCandidates(): Promise<Candidate[]> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/candidates`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return [];
    }
  },

  async getCandidate(id: number): Promise<Candidate | null> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/candidates/${id}`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return null;
    }
  },

  async createCandidate(candidate: Omit<Candidate, 'id'>): Promise<Candidate | null> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/candidates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(candidate),
      });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    } catch (e) {
      console.error("Failed to create candidate:", e);
      return null;
    }
  },

  async updateCandidateStatus(id: number, status: string): Promise<boolean> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/candidates/${id}/status?status=${status}`, {
        method: 'PATCH',
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  async deleteCandidate(id: number): Promise<boolean> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/candidates/${id}`, { method: 'DELETE' });
      return res.ok;
    } catch {
      return false;
    }
  },

  async deleteAllCandidates(): Promise<boolean> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/candidates/all/delete`, { method: 'DELETE' });
      return res.ok;
    } catch {
      return false;
    }
  },

  // UX Improvements: Bulk Operations & Sent Tracking
  async bulkAddToPipeline(candidateIds: number[]): Promise<boolean> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/candidates/bulk-add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_ids: candidateIds }),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  async getSentCandidates(): Promise<Candidate[]> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/candidates/sent`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return [];
    }
  },

  async markAsSent(candidateId: number): Promise<boolean> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/candidates/${candidateId}/mark-sent`, {
        method: 'PATCH',
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  async markAsReplied(candidateId: number): Promise<boolean> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/candidates/${candidateId}/mark-replied`, {
        method: 'PATCH',
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  // Drafts
  async getDrafts(): Promise<Draft[]> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/drafts`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return [];
    }
  },

  async deleteAllDrafts(): Promise<boolean> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/drafts`, { method: 'DELETE' });
      return res.ok;
    } catch {
      return false;
    }
  },

  async generateDraft(candidateId: number, context: string = '', contactType: 'auto' | 'email' | 'linkedin' = 'auto'): Promise<{ type: 'email' | 'linkedin'; subject?: string; body?: string; message?: string; char_count?: number; draft_id?: number } | null> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/drafts/generate/${candidateId}?context=${encodeURIComponent(context)}&contact_type=${contactType}`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return null;
    }
  },

  async generateDraftsBatch(candidateIds: number[], context: string = ''): Promise<{ message: string, task_id?: string } | null> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/drafts/generate-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_ids: candidateIds, context })
      });
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return null;
    }
  },

  async getBatchStatus(taskId: string): Promise<{ total: number, completed: number, failed: number, status: string } | null> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/drafts/batch/${taskId}/status`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return null;
    }
  },

  async polishDraft(text: string): Promise<string | null> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/drafts/polish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error('API error');
      const data = await res.json();
      return data.text;
    } catch {
      return null;
    }
  },



  async getSentEmails(): Promise<{ emails: unknown[] }> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/emails/sent`);
      return res.json();
    } catch {
      return { emails: [] };
    }
  },

  // Activity & Stats
  async getActivity(): Promise<ActivityLog[]> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/stats/activity`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return [];
    }
  },

  async getStats(): Promise<DashboardStats> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/stats`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return { weekly_goal_percent: 0, people_found: 0, emails_sent: 0, account_health: 100, is_safe: true, recent_leads: [], top_industries: [] };
    }
  },

  async getFunnelStats(): Promise<FunnelStats | null> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/stats/funnel`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return null;
    }
  },

  // Brain Context
  async updateSkills(skills: string[]): Promise<boolean> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/settings/brain/skills`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(skills),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  async getBrainContext(): Promise<{ formality: number; detail_level: number; use_emojis: boolean; resume_url?: string; extracted_skills?: string[] }> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/settings/brain`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return { formality: 75, detail_level: 30, use_emojis: false };
    }
  },

  async updateBrainContext(formality: number, detailLevel: number, useEmojis: boolean): Promise<boolean> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/settings/brain?formality=${formality}&detail_level=${detailLevel}&use_emojis=${useEmojis}`, {
        method: 'PUT',
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  async verifyLinkedIn(url: string): Promise<{ valid: boolean; message: string }> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/settings/verify-linkedin?url=${encodeURIComponent(url)}`, {
          method: 'POST'
      });
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return { valid: false, message: 'Verification failed' };
    }
  },

  // AI Extraction
  extractOpportunity: async (text: string): Promise<ExtractedOpportunity | null> => {
    try {
      const res = await fetchWithAuth(`${API_BASE}/settings/extract-opportunity`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch (e) {
      console.error(e);
      return null;
    }
  },

  // Gmail OAuth
  async getGmailStatus(userId: number = 1): Promise<{ connected: boolean; email?: string }> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/auth/gmail/status?user_id=${userId}`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return { connected: false };
    }
  },

  async getGmailAuthUrl(userId: number = 1): Promise<string | null> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/auth/google?user_id=${userId}`);
      if (!res.ok) throw new Error('API error');
      const data = await res.json();
      return data.auth_url;
    } catch {
      return null;
    }
  },
  // Automation
  async launchAutomation(candidateId: number): Promise<{ status: string; detail?: string }> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/automation/launch/${candidateId}`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return { status: 'error', detail: 'Failed to launch automation' };
    }
  },

  // Account Management
  async deleteAccount(): Promise<boolean> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/settings/account`, {
        method: 'DELETE',
      });
      return res.ok;
    } catch {
      return false;
    }
  },
};

export interface ExtractedOpportunity {
  is_opportunity: boolean;
  role: string;
  domain: string;
  opportunity_type: string;
  company_name: string;
  apply_method: string;
  apply_contact: string;
  location: string;
  skills_required: string[];
  urgency_level: string;
  source_text_confidence: number;
}
