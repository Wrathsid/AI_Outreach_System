// API Client for Cold Emailing Backend
// export const API_BASE = 'http://localhost:8000'; // Hardcoded for now until env var logic is stricter
export const API_BASE = 'http://localhost:8000';

// Types
export interface Candidate {
  id: number;
  name: string;
  title?: string;
  company?: string;
  location?: string;
  email?: string;
  linkedin_url?: string;
  avatar_url?: string;
  match_score: number;
  summary?: string;
  tags?: string[];
  status?: string;
}

export interface Draft {
  id: number;
  candidate_id: number;
  subject: string;
  body: string;
  status: string;
  candidate_name?: string;
  candidate_company?: string;
}

export interface ActivityLog {
  id: number;
  action_type: string;
  title: string;
  description?: string;
  created_at: string;
  candidate_id?: number;
}

export interface DashboardStats {
  weekly_goal_percent: number;
  people_found: number;
  emails_sent: number;
  replies_received: number;
}

export interface UserSettings {
  full_name: string;
  company: string;
  role: string;
}

// API Functions
export const api = {
  // Health check
  async health() {
    const res = await fetch(`${API_BASE}/`);
    return res.json();
  },

  // Settings
  getSettings: async (): Promise<UserSettings> => {
    const res = await fetch(`${API_BASE}/settings`);
    return res.json();
  },
  
  updateSettings: async (settings: UserSettings): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  // Discovery
  discoverCandidates: async (role: string): Promise<unknown[]> => {
    try {
        const res = await fetch(`${API_BASE}/discover?role=${encodeURIComponent(role)}`);
        if (!res.ok) throw new Error('API error');
        return res.json();
    } catch {
        return [];
    }
  },

  crawlWebsite: async (url: string): Promise<unknown> => {
    const res = await fetch(`${API_BASE}/discovery/crawl`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ domain: url })
    });
    return res.json();
  },

  guessEmailPattern: async (firstName: string, lastName: string, domain: string): Promise<unknown> => {
    const res = await fetch(`${API_BASE}/discovery/pattern`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ first_name: firstName, last_name: lastName, domain })
    });
    return res.json();
  },

  // Candidates
  async pruneCandidates(days: number = 7): Promise<unknown> {
    const response = await fetch(`${API_BASE}/candidates/prune?days=${days}`, {
      method: "DELETE",
    });
    return response.json();
  },

  async getCandidates(): Promise<Candidate[]> {
    try {
      const res = await fetch(`${API_BASE}/candidates`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return [];
    }
  },

  async getCandidate(id: number): Promise<Candidate | null> {
    try {
      const res = await fetch(`${API_BASE}/candidates/${id}`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return null;
    }
  },

  async createCandidate(candidate: Omit<Candidate, 'id'>): Promise<Candidate | null> {
    try {
      const res = await fetch(`${API_BASE}/candidates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(candidate),
      });
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return null;
    }
  },

  async updateCandidateStatus(id: number, status: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/candidates/${id}/status?status=${status}`, {
        method: 'PATCH',
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  async deleteCandidate(id: number): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/candidates/${id}`, { method: 'DELETE' });
      return res.ok;
    } catch {
      return false;
    }
  },

  // Drafts
  async getDrafts(): Promise<Draft[]> {
    try {
      const res = await fetch(`${API_BASE}/drafts`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return [];
    }
  },

  async generateDraft(candidateId: number, context: string = ''): Promise<{ subject: string; body: string; draft_id?: number } | null> {
    try {
      const res = await fetch(`${API_BASE}/generate-draft?candidate_id=${candidateId}&context=${encodeURIComponent(context)}`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return null;
    }
  },

  async polishDraft(text: string): Promise<string | null> {
    try {
      const res = await fetch(`${API_BASE}/polish-draft`, {
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

  // Send Email
  async sendEmail(to: string, subject: string, body: string, candidateId?: number): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/send-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ to, subject, body, candidate_id: candidateId }),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  async getSentEmails(): Promise<{ emails: unknown[] }> {
    try {
      const res = await fetch(`${API_BASE}/sent-emails`);
      return res.json();
    } catch {
      return { emails: [] };
    }
  },

  // Activity & Stats
  async getActivity(): Promise<ActivityLog[]> {
    try {
      const res = await fetch(`${API_BASE}/activity`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return [];
    }
  },

  async getStats(): Promise<DashboardStats> {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return { weekly_goal_percent: 0, people_found: 0, emails_sent: 0, replies_received: 0 };
    }
  },

  // Brain Context
  async uploadResume(file: File): Promise<{ filename: string; status: string; extracted_skills: string[]; warning?: string } | null> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API_BASE}/brain/upload`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return null;
    }
  },

  async getBrainContext(): Promise<{ formality: number; detail_level: number; use_emojis: boolean; resume_url?: string; extracted_skills?: string[] }> {
    try {
      const res = await fetch(`${API_BASE}/brain`);
      if (!res.ok) throw new Error('API error');
      return res.json();
    } catch {
      return { formality: 75, detail_level: 30, use_emojis: false };
    }
  },

  async updateBrainContext(formality: number, detailLevel: number, useEmojis: boolean): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/brain?formality=${formality}&detail_level=${detailLevel}&use_emojis=${useEmojis}`, {
        method: 'PUT',
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  async verifyLinkedIn(url: string): Promise<{ valid: boolean; message: string }> {
    try {
      const res = await fetch(`${API_BASE}/verify-linkedin?url=${encodeURIComponent(url)}`, {
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
      const res = await fetch(`${API_BASE}/extract-opportunity`, {
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
