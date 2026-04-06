"""
Pydantic schemas/models for the Cold Emailing API.
All request/response models are defined here for centralized management.
"""

from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class IntentType(str, Enum):
    """Intent buckets for outreach categorization."""

    CURIOUS = "curious"  # Default for LinkedIn
    PEER = "peer"  # Default for Email
    SOFT = "soft"  # Opportunity hint
    DIRECT = "direct"  # Direct ask (rare)
    OPPORTUNITY = "opportunity"  # For Recruiters


class GenerationReason(str, Enum):
    """H5: Reason codes for draft generation source."""

    FRESH_GENERATION = "FRESH_GENERATION"
    IDEMPOTENT_RETURN = "IDEMPOTENT_RETURN"
    RETRY_GENERATION = "RETRY_GENERATION"
    FALLBACK_TEMPLATE = "FALLBACK_TEMPLATE"
    FAILED_PRECONDITION = "FAILED_PRECONDITION"


# ==================== CANDIDATE MODELS ====================


class Candidate(BaseModel):
    """Full candidate model with all fields."""

    id: int
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    generated_email: Optional[str] = None
    email_confidence: Optional[int] = None
    linkedin_url: Optional[str] = None
    avatar_url: Optional[str] = None
    match_score: int = 0
    summary: Optional[str] = None
    tags: Optional[List[str]] = []
    status: Optional[str] = "new"
    email_source: Optional[str] = "none"
    sent_at: Optional[str] = None
    reply_received: Optional[bool] = False
    reply_at: Optional[str] = None


class CandidateCreate(BaseModel):
    """Model for creating a new candidate."""

    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    generated_email: Optional[str] = None
    email_confidence: Optional[int] = None
    linkedin_url: Optional[str] = None
    avatar_url: Optional[str] = None
    match_score: int = 0
    summary: Optional[str] = None
    tags: Optional[List[str]] = []
    status: Optional[str] = "new"


class BulkAddRequest(BaseModel):
    """Model for bulk adding candidates to pipeline (UX Improvement)."""

    candidate_ids: List[int]


# ==================== DRAFT MODELS ====================


class Draft(BaseModel):
    """Full draft model with candidate info."""

    id: int
    candidate_id: int
    subject: str
    body: str
    status: str = "draft"
    candidate_name: Optional[str] = None
    candidate_company: Optional[str] = None
    # Learning Loop Fields
    intent: Optional[str] = None
    temperature: Optional[float] = None
    signal_used: Optional[str] = None
    variant_id: Optional[str] = None
    reply_status: Optional[str] = "no_reply"
    generation_params: Optional[dict] = None
    # Optimization Fields
    time_to_read: Optional[int] = 0


class DraftCreate(BaseModel):
    """Model for creating a new draft."""

    candidate_id: int
    subject: str
    body: str
    # Learning Loop Fields
    intent: Optional[str] = None
    temperature: Optional[float] = None
    signal_used: Optional[str] = None
    variant_id: Optional[str] = None
    generation_params: Optional[dict] = None


class DraftEditCreate(BaseModel):
    """Model for recording manual template edits (RAG Feedback)."""

    candidate_id: int
    original_text: str
    edited_text: str
    contact_type: str



class EmailGuessRequest(BaseModel):
    """Request model for email guessing."""

    name: str
    company: str
    domain: Optional[str] = None


class EmailVerifyRequest(BaseModel):
    """Single email verification request."""

    email: str


class EmailVerifyBatchRequest(BaseModel):
    """Batch email verification request."""

    emails: List[str]


# ==================== ACTIVITY & STATS MODELS ====================


class ActivityLog(BaseModel):
    """Activity log entry model."""

    id: int
    action_type: str
    title: str
    description: Optional[str] = None
    created_at: str
    candidate_id: Optional[int] = None


class DashboardStats(BaseModel):
    """Dashboard statistics model."""

    weekly_goal_percent: int
    people_found: int
    emails_sent: int
    replies_received: int
    account_health: int = 100
    is_safe: bool = True
    safety_reason: Optional[str] = None
    recent_leads: List[dict] = []
    top_industries: List[dict] = []


# ==================== SETTINGS MODELS ====================


class UserSettings(BaseModel):
    """User settings/profile model."""

    full_name: str = ""
    company: str = ""
    role: str = ""
    avatar_url: Optional[str] = None


# ==================== DISCOVERY MODELS ====================


class ExtractionRequest(BaseModel):
    """Text extraction request for AI processing."""

    text: str


class CrawlRequest(BaseModel):
    """Domain crawling request."""

    domain: str


class PatternRequest(BaseModel):
    """Email pattern generation request."""

    first_name: str
    last_name: Optional[str] = ""
    domain: str


# ==================== PROMPT CONTRACT TYPING (D1) ====================


class PromptSection(BaseModel):
    """Typed prompt section for deterministic assembly (D1)."""

    system_identity: str
    user_bio: str
    candidate_context: str
    signal: Optional[str] = None
    memory_constraint: Optional[str] = None
    skills_grounding: Optional[str] = None
    structural_rules: str
    negative_constraints: str
    task_instruction: str


class GenerationParams(BaseModel):
    """Typed generation parameters for audit trail (D1)."""

    variant_id: str
    score: float
    opener_hash: Optional[str] = None
    embedding: Optional[list] = None
    model: str = "gemini-2.0-flash"
    temperature: float = 0.4
    context_band: str = "LOW"
    signal_type: Optional[str] = None
    is_fallback: Optional[bool] = False
    data_quality: Optional[int] = None
    # H1/H2/H5 Hardening Fields
    fingerprint: Optional[str] = None
    prompt_version: Optional[str] = None
    reason: Optional[GenerationReason] = None
    skill_count: Optional[int] = None


# ==================== RESPONSE MODELS ====================


class DraftGenerateResponse(BaseModel):
    """Response model for draft generation endpoints."""

    type: str  # "linkedin" or "email"
    message: Optional[str] = None  # LinkedIn
    subject: Optional[str] = None  # Email
    body: Optional[str] = None  # Email
    quality_score: float
    draft_id: int
    time_to_read: int
    variant_id: str
    is_fallback: bool = False


class BatchStatusResponse(BaseModel):
    """Response model for batch status endpoint."""

    task_id: str
    status: str
    completed: int
    total: int
    successful: int
    failed: int


class HealthResponse(BaseModel):
    """System health check response."""

    status: str
    supabase: str
