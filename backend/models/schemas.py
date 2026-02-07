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
    PEER = "peer"        # Default for Email
    SOFT = "soft"        # Opportunity hint
    DIRECT = "direct"    # Direct ask (rare)



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


# ==================== EMAIL MODELS ====================

class SendEmailRequest(BaseModel):
    """Legacy send email request model."""
    candidate_id: Optional[int] = None
    to: str
    subject: str
    body: str


class SendEmailDirectRequest(BaseModel):
    """Direct email sending request (SMTP/SendGrid)."""
    to_email: str
    subject: str
    body: str
    reply_to: Optional[str] = None


class GmailSendRequest(BaseModel):
    """Gmail OAuth email sending request."""
    to: str
    subject: str
    body: str
    candidate_id: Optional[int] = None


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
    recent_leads: List[dict] = []
    top_industries: List[dict] = []


# ==================== SETTINGS MODELS ====================

class UserSettings(BaseModel):
    """User settings/profile model."""
    full_name: str = ""
    company: str = ""
    role: str = ""


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
