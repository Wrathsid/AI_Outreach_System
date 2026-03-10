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
  
  const fetchOptions = { ...options, headers };
  if (!fetchOptions.cache && !fetchOptions.next) {
    fetchOptions.cache = 'no-store';
  }
  
  return fetch(url, fetchOptions);
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


export interface FunnelStats {
  funnel: { stage: string; count: number; percent: number }[];
  conversions: { found_to_contacted: number };
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
      if (res.ok && typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('candidates_updated'));
      }
      return res.ok;
    } catch {
      return false;
    }
  },

  async deleteCandidate(id: number): Promise<boolean> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/candidates/${id}`, { method: 'DELETE' });
      if (res.ok && typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('candidates_updated'));
      return res.ok;
    } catch {
      return false;
    }
  },

  async deleteAllCandidates(): Promise<boolean> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/candidates/all/delete`, { method: 'DELETE' });
      if (res.ok && typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('candidates_updated'));
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
      if (res.ok && typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('candidates_updated'));
      return res.ok;
    } catch {
      return false;
    }
  },

  // Drafts


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

  async getStats(): Promise<DashboardStats> {
    try {
      const res = await fetchWithAuth(`${API_BASE}/stats`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return { weekly_goal_percent: 0, people_found: 0, emails_sent: 0, account_health: 100, is_safe: true, recent_leads: [], top_industries: [] };
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

  // RAG / Tone Learning
  async saveDraftEdit(candidateId: number, originalText: string, editedText: string, contactType: string): Promise<void> {
    const response = await fetch(`${API_BASE}/drafts/edits`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        candidate_id: candidateId,
        original_text: originalText,
        edited_text: editedText,
        contact_type: contactType
      }),
    });
    if (!response.ok) {
      console.error('Failed to save draft edit for RAG feedback');
    }
  }
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
