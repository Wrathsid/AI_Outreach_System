# Changelog

All notable changes to the AI Outreach System are documented here.

## [1.0.0] — 2025-03-04

### 🚀 Initial Release

#### Discovery Engine

- Role-based LinkedIn lead discovery via SerpAPI + DuckDuckGo fallback
- AI-powered lead polishing (Gemini cleans messy search snippets into structured profiles)
- Temporal workflow orchestration for durable, retriable discovery pipelines
- Email pattern prediction and Hunter.io verification with MX fallback

#### AI Draft Generation

- Dual LLM support: Google Gemini (primary) + Qubrid Llama-3.3-70B (fallback)
- "Cortex" personalization engine — generates messages grounded in user's resume and skills
- Deterministic prompt assembly with structural validation, hedging removal, and length normalization
- Draft scoring (0-100 reply probability) with semantic deduplication
- Batch generation via Temporal with 5 activities/sec rate limiting

#### Email Delivery

- Gmail OAuth2 integration — send from user's own account
- SendGrid SMTP delivery
- Adaptive throttling with health score (0-100) and working hours enforcement
- Human-like delays (30-120s) between sends

#### Frontend

- Next.js 14 App Router with TypeScript
- Glassmorphic "Apple Vision" UI with TailwindCSS v4 + Framer Motion
- Command palette (⌘K), skeleton loaders, animated backgrounds
- Supabase SSR authentication with middleware guard
- Dashboard analytics with conversion funnel (Recharts)

#### Infrastructure

- FastAPI backend with rate-limiting middleware
- Temporal workflow engine (Docker Compose setup)
- Supabase PostgreSQL database
- Vercel (frontend) + Railway (backend) deployment configs
- Docker containerization for API and worker
