# Models package
from .schemas import (
    Candidate, CandidateCreate,
    Draft, DraftCreate,
    SendEmailRequest, SendEmailDirectRequest, GmailSendRequest,
    ActivityLog, DashboardStats, UserSettings,
    ExtractionRequest, CrawlRequest, PatternRequest,
    EmailGuessRequest, EmailVerifyRequest, EmailVerifyBatchRequest
)

__all__ = [
    "Candidate", "CandidateCreate",
    "Draft", "DraftCreate", 
    "SendEmailRequest", "SendEmailDirectRequest", "GmailSendRequest",
    "ActivityLog", "DashboardStats", "UserSettings",
    "ExtractionRequest", "CrawlRequest", "PatternRequest",
    "EmailGuessRequest", "EmailVerifyRequest", "EmailVerifyBatchRequest"
]
