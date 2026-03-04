<div align="center">
  <img src="https://raw.githubusercontent.com/Wrathsid/AI_Outreach_System/main/public/logo.png" alt="AI Outreach System Logo" width="140" height="140" style="border-radius: 20%;">

# ❄️ AI Outreach System

**The "Apple-style" Command Center for high-precision outreach.**
_Discover leads, verify emails, generate AI-personalized messages, and send — all from one calm, focused interface._

  <p>
    <a href="#-features"><img src="https://img.shields.io/badge/Features-Explore-blue?style=for-the-badge&logo=rocket" alt="Features"></a>
    <a href="#-technology-stack"><img src="https://img.shields.io/badge/Stack-Tech-black?style=for-the-badge&logo=code" alt="Tech"></a>
    <a href="#-getting-started"><img src="https://img.shields.io/badge/Install-Get_Started-green?style=for-the-badge&logo=terminal" alt="Getting Started"></a>
    <img src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge" alt="License">
  </p>
</div>

---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND                                   │
│        Next.js 14 (App Router) · TailwindCSS · Framer Motion       │
│   ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐  │
│   │Dashboard│ │  Search  │ │Candidates│ │  Drafts  │ │Settings │  │
│   └────┬────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬────┘  │
│        └────────────┴────────────┴─────────────┴────────────┘      │
│                       fetchWithAuth (JWT)                           │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ Bearer Token
┌───────────────────────────────▼─────────────────────────────────────┐
│                           BACKEND                                   │
│              FastAPI · Python 3.11+ · Pydantic · Uvicorn            │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  8 Routers: candidates · drafts · discovery · emails ·      │  │
│   │             stats · settings · auth · automation             │  │
│   ├──────────────────────────────────────────────────────────────┤  │
│   │  13 Services: crawler · email_generator · email_verifier ·   │  │
│   │    email_sender · gmail_oauth · throttle · embeddings ·      │  │
│   │    hr_extractor · browser_automation · confidence · ...      │  │
│   └──────────────────────────────────────────────────────────────┘  │
└─────┬──────────┬──────────┬──────────┬──────────┬───────────────────┘
      │          │          │          │          │
┌─────▼────┐ ┌──▼───┐ ┌───▼────┐ ┌───▼───┐ ┌───▼──────────────────┐
│ Supabase │ │Gemini│ │SerpAPI │ │Hunter │ │    Temporal           │
│(Postgres)│ │Qubrid│ │  DDG   │ │  .io  │ │ (Workflow Engine)    │
└──────────┘ └──────┘ └────────┘ └───────┘ └──────────────────────┘
```

### End-to-End Flow

```
User enters role → Crawler scrapes LinkedIn (SerpAPI/DDG) → AI polishes leads (Gemini)
→ Email patterns predicted → Emails verified (Hunter.io/MX) → Saved to Supabase
→ AI generates personalized drafts (Gemini + Cortex) → Scored & validated
→ Sent via Gmail OAuth / SendGrid → Activity logged → Analytics updated
```

---

## ✨ Features

### 🔍 Deep Web Discovery

- **Role-Based Precision Search** — Enter any job title to instantly scrape hiring managers & recruiters from LinkedIn.
- **Dual Crawler Fallback** — SerpAPI (Google) primary with DuckDuckGo fallback. Never blocked.
- **AI Data Polish** — Gemini cleans messy search snippets into structured profiles (name, title, company, summary).
- **Temporal Orchestration** — Discovery runs as a durable workflow with automatic retries.

### 🤖 AI-Powered Email Pipeline

- **"Cortex" Personalization** — Upload your resume. The AI writes as _you_, grounded in your actual skills and experience.
- **Dual LLM Support** — Google Gemini (primary) with Qubrid Llama-3.3-70B (fallback for rate limits).
- **Smart Draft Scoring** — Every draft is scored 0-100 for reply probability (length, questions, CTA quality).
- **Post-Generation Guards** — Structural validation, hedging removal, length normalization, semantic deduplication.
- **Batch Queueing** — Import 100+ candidates; AI generates drafts at 5/sec with rate-limit respect.
- **Tone Customization** — Formality, detail level, emoji usage — all configurable per user.

### 🛡️ Pre-Delivery Verification

- **Hunter.io Integration** — SMTP ping verification with deliverability scoring.
- **MX Fallback** — When no API key, checks domain MX records for basic validation.
- **Email Pattern Prediction** — Guesses `first.last@domain.com` style patterns from name + company.
- **Catch-All Detection** — Evaluates domains to stop generic routing.

### 📬 Multi-Channel Sending

- **Gmail OAuth** — Send directly from your own Gmail account (full OAuth2 flow).
- **SendGrid SMTP** — Programmatic email delivery with tracking.
- **LinkedIn Automation** — Playwright-based browser automation to paste messages on LinkedIn (local only).

### 📊 Analytics & Safety

- **Conversion Funnel** — Found → Contacted → Replied with real-time conversion rates.
- **Account Health Score** — Rolling 0-100 score based on bounces, errors, and rate limits.
- **Adaptive Throttling** — Auto-reduces sending limits when health drops. Working hours enforcement (9AM-6PM).
- **Human-Like Delays** — Random 30-120s pauses between sends.

### 💅 Premium Glassmorphic UI

- **Apple-Vision Aesthetics** — Translucent panels, noise textures, spotlight hover effects.
- **Command Palette** — ⌘K for instant navigation.
- **Buttery Animations** — Framer Motion throughout.
- **Skeleton Loaders** — Premium loading states.

---

## 💻 Technology Stack

<div align="center">

| Layer              | Technologies                                                                                                  |
| :----------------- | :------------------------------------------------------------------------------------------------------------ |
| **Frontend**       | ⚡ Next.js 14 (App Router), React 19, TypeScript, TailwindCSS v4, Framer Motion, Recharts, Lucide Icons, cmdk |
| **Backend**        | 🚀 FastAPI (Python 3.11+), Pydantic, Uvicorn, AsyncIO                                                         |
| **AI / NLP**       | 🧠 Google Gemini (2.5-flash / 2.0-flash), Qubrid (Llama-3.3-70B), SentenceTransformers                        |
| **Database**       | 🗄️ Supabase (PostgreSQL)                                                                                      |
| **Orchestration**  | ⏱️ Temporal (durable workflows with automatic retries)                                                        |
| **Scraping**       | 🕷️ SerpAPI (Google), DuckDuckGo Search                                                                        |
| **Email**          | ✉️ SendGrid, Gmail API (OAuth2), Hunter.io (verification)                                                     |
| **Automation**     | 🤖 Playwright (LinkedIn browser automation)                                                                   |
| **Infrastructure** | 🐳 Docker Compose, Vercel (FE), Railway (BE)                                                                  |

</div>

---

## 🚀 Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) v18+
- [Python](https://www.python.org/downloads/) 3.11+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for Temporal)
- [Git](https://git-scm.com/)

### 1. Clone

```bash
git clone https://github.com/Wrathsid/AI_Outreach_System.git
cd AI_Outreach_System
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Activate:
# Windows:  .\venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env`:

```env
# Required
SUPABASE_URL="your-supabase-url"
SUPABASE_KEY="your-supabase-anon-key"
GEMINI_API_KEY="your-google-gemini-key"
SERPAPI_KEY="your-serpapi-key"

# Optional (enhanced features)
QUBRID_API_KEY="your-qubrid-key"           # Alternative LLM
SENDGRID_API_KEY="your-sendgrid-key"       # Email sending
FROM_EMAIL="your-email@domain.com"
HUNTER_API_KEY="your-hunter-key"           # Email verification
GOOGLE_CLIENT_ID="your-oauth-client-id"    # Gmail integration
GOOGLE_CLIENT_SECRET="your-oauth-secret"
GOOGLE_REDIRECT_URI="http://localhost:8000/auth/google/callback"
```

Start the backend:

```bash
python -m backend.main
```

API runs at `http://localhost:8000`

### 3. Temporal Setup (for durable workflows)

```bash
# From project root
docker-compose up -d
```

This starts 4 containers:
| Container | Port | Purpose |
|-----------|------|---------|
| `temporal` | 7233 | Workflow engine |
| `temporal-ui` | 8233 | Web dashboard |
| `postgresql` | 5432 | Temporal's database |
| `elasticsearch` | 9200 | Temporal's search index |

Start the worker (separate terminal):

```bash
python -m backend.temporal.worker
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL="your-supabase-url"
NEXT_PUBLIC_SUPABASE_ANON_KEY="your-supabase-anon-key"
NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"
```

Start the app:

```bash
npm run dev
```

UI runs at `http://localhost:3000`

---

## 📁 Project Structure

```
AI_Outreach_System/
├── backend/                         # FastAPI Backend
│   ├── main.py                      # App entry, router registration, rate limiting
│   ├── config.py                    # Supabase, Gemini, Qubrid client init
│   ├── dependencies.py              # JWT auth middleware
│   ├── models/
│   │   └── schemas.py               # Pydantic models (Candidate, Draft, Email, etc.)
│   ├── routers/
│   │   ├── candidates.py            # Lead CRUD, pipeline management
│   │   ├── drafts.py                # AI generation engine (1900+ lines)
│   │   ├── discovery.py             # Temporal lead discovery
│   │   ├── emails.py                # Email guessing, verification, sending
│   │   ├── stats.py                 # Dashboard analytics
│   │   ├── settings.py              # Profile, Cortex/Brain, resume upload
│   │   ├── auth.py                  # Gmail OAuth flow
│   │   └── automation.py            # LinkedIn browser automation
│   ├── services/
│   │   ├── crawler.py               # SerpAPI + DuckDuckGo web scraping
│   │   ├── email_generator.py       # Email pattern prediction
│   │   ├── email_verifier.py        # Hunter.io + MX verification
│   │   ├── email_sender.py          # SendGrid delivery
│   │   ├── gmail_oauth.py           # Gmail API integration
│   │   ├── throttle.py              # Adaptive rate limiting + health score
│   │   ├── embeddings.py            # Semantic similarity (SentenceTransformers)
│   │   ├── hr_extractor.py          # AI opportunity extraction
│   │   ├── browser_automation.py    # Playwright LinkedIn messaging
│   │   └── ...                      # confidence, recommendation, verifier
│   ├── temporal/
│   │   ├── workflows.py             # DiscoveryWorkflow (crawl → polish → verify)
│   │   ├── activities.py            # Crawl, polish, email guess, verify activities
│   │   ├── draft_workflows.py       # BatchDraftWorkflow
│   │   ├── draft_activities.py      # Draft generation activity
│   │   └── worker.py                # Worker entry (2 task queues)
│   ├── tests/                       # pytest test suite
│   ├── Dockerfile                   # API container
│   ├── Dockerfile.worker            # Worker container
│   └── requirements.txt
├── frontend/                        # Next.js 14 Frontend
│   ├── src/
│   │   ├── app/                     # App Router pages
│   │   │   ├── layout.tsx           # Root layout (Sidebar, AuthGuard)
│   │   │   ├── globals.css          # Global styles + glassmorphism
│   │   │   ├── dashboard/           # Stats, charts, activity feed
│   │   │   ├── search/              # Lead discovery UI
│   │   │   ├── candidates/          # Pipeline management
│   │   │   ├── drafts/              # AI draft review/edit
│   │   │   ├── sent/                # Sent message history
│   │   │   ├── settings/            # Profile + Cortex config
│   │   │   ├── analytics/           # Conversion funnel
│   │   │   ├── brain/               # AI personality setup
│   │   │   ├── login/ & signup/     # Auth pages
│   │   │   └── template.tsx         # Page transition animations
│   │   ├── components/              # Reusable React components
│   │   │   ├── Dashboard.tsx        # Main dashboard with stat cards
│   │   │   ├── Sidebar.tsx          # Navigation sidebar
│   │   │   ├── CommandPalette.tsx   # ⌘K command palette
│   │   │   ├── AuthGuard.tsx        # Client-side auth wrapper
│   │   │   ├── NeuralBackground.tsx # Animated background effect
│   │   │   └── ...                  # Animations, FileUpload, Skeletons
│   │   ├── lib/
│   │   │   ├── api.ts               # Centralized API client (568 lines)
│   │   │   └── supabase.ts          # Supabase browser client
│   │   ├── context/                 # React Contexts (Toast, Template)
│   │   └── middleware.ts            # Supabase SSR auth guard
│   ├── package.json
│   └── vercel.json
├── docker-compose.yml               # Temporal + PostgreSQL + Elasticsearch
├── scripts/                         # Utility scripts
└── README.md
```

---

## 🗄️ Database Schema

All data lives in **Supabase (PostgreSQL)**:

| Table             | Key Columns                                                                                             | Purpose                      |
| ----------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------- |
| `candidates`      | id, name, title, company, email, email_confidence, linkedin_url, match_score, status, sent_at, reply_at | Lead/prospect storage        |
| `drafts`          | id, candidate_id, subject, body, status, intent, temperature, variant_id, generation_params (JSON)      | AI messages with audit trail |
| `sent_emails`     | id, candidate_id, subject, body, sent_at, message_id                                                    | Delivery records             |
| `activity_log`    | id, action_type, title, description, candidate_id                                                       | User action audit trail      |
| `user_settings`   | full_name, company, role, avatar_url                                                                    | User profile                 |
| `brain_context`   | formality, detail_level, use_emojis, resume_url, extracted_skills[]                                     | AI personality (Cortex)      |
| `gmail_tokens`    | user_id, access_token, refresh_token, email, expires_at                                                 | OAuth credentials            |
| `dashboard_stats` | stat_date, emails_sent, linkedin_sent                                                                   | Daily send counts            |

**Candidate Status Flow:** `new` → `contacted` → `replied` → `snoozed`

---

## 🔌 API Reference

### Candidates (`/candidates`)

| Method | Endpoint                        | Description                     |
| ------ | ------------------------------- | ------------------------------- |
| GET    | `/candidates`                   | List all candidates             |
| GET    | `/candidates/{id}`              | Get single candidate            |
| POST   | `/candidates`                   | Create candidate (deduplicates) |
| POST   | `/candidates/bulk-add`          | Bulk add to pipeline            |
| PATCH  | `/candidates/{id}/status`       | Update status                   |
| PATCH  | `/candidates/{id}/mark-sent`    | Mark as sent                    |
| PATCH  | `/candidates/{id}/mark-replied` | Mark as replied                 |
| DELETE | `/candidates/{id}`              | Delete candidate                |
| DELETE | `/candidates/all/delete`        | Delete all                      |

### Drafts (`/drafts`)

| Method | Endpoint                         | Description                        |
| ------ | -------------------------------- | ---------------------------------- |
| GET    | `/drafts`                        | List all drafts                    |
| POST   | `/drafts/generate/{id}`          | Generate AI draft for candidate    |
| POST   | `/drafts/generate-batch`         | Batch generate (Temporal or async) |
| POST   | `/drafts/polish`                 | AI-polish existing text            |
| GET    | `/drafts/batch/{task_id}/status` | Check batch progress               |
| DELETE | `/drafts`                        | Delete all drafts                  |

### Discovery (`/discover`)

| Method | Endpoint                                  | Description                       |
| ------ | ----------------------------------------- | --------------------------------- |
| POST   | `/discover/temporal-discover`             | Start Temporal discovery workflow |
| GET    | `/discover/temporal-discover/{job_id}`    | Poll workflow status              |
| WS     | `/discover/ws/temporal-discover/{job_id}` | WebSocket status stream           |

### Emails (`/emails`)

| Method | Endpoint                  | Description                |
| ------ | ------------------------- | -------------------------- |
| POST   | `/emails/guess`           | Generate email patterns    |
| POST   | `/emails/guess/{id}`      | Guess + save for candidate |
| POST   | `/emails/verify`          | Verify single email        |
| POST   | `/emails/verify-batch`    | Verify batch (max 25)      |
| POST   | `/emails/send`            | Send via SendGrid          |
| POST   | `/emails/send-draft/{id}` | Send specific draft        |

### Stats (`/stats`)

| Method | Endpoint          | Description               |
| ------ | ----------------- | ------------------------- |
| GET    | `/stats`          | Dashboard stats           |
| GET    | `/stats/funnel`   | Conversion funnel metrics |
| GET    | `/stats/activity` | Recent activity log       |

### Settings (`/settings`)

| Method      | Endpoint                 | Description          |
| ----------- | ------------------------ | -------------------- |
| GET         | `/settings`              | Get user settings    |
| PUT         | `/settings`              | Update settings      |
| POST/DELETE | `/settings/avatar`       | Upload/remove avatar |
| GET         | `/settings/brain`        | Get Cortex config    |
| PUT         | `/settings/brain`        | Update Cortex config |
| PUT         | `/settings/brain/skills` | Update skills        |
| POST        | `/settings/upload`       | Upload resume (PDF)  |
| DELETE      | `/settings/account`      | Delete all user data |

### Auth (`/auth`)

| Method | Endpoint                      | Description            |
| ------ | ----------------------------- | ---------------------- |
| GET    | `/auth/google`                | Start Gmail OAuth flow |
| GET    | `/auth/google/callback`       | OAuth callback handler |
| GET    | `/auth/gmail/status`          | Check Gmail connection |
| POST   | `/auth/gmail/send`            | Send via Gmail         |
| POST   | `/auth/gmail/send-draft/{id}` | Send draft via Gmail   |

### Automation (`/automation`)

| Method | Endpoint                  | Description                        |
| ------ | ------------------------- | ---------------------------------- |
| POST   | `/automation/launch/{id}` | Launch LinkedIn browser automation |

---

## 🔒 Security

| Area                  | Implementation                                                           |
| --------------------- | ------------------------------------------------------------------------ |
| **Authentication**    | Supabase JWT — validated on every protected endpoint                     |
| **Frontend Guard**    | Next.js middleware redirects unauthenticated users to `/login`           |
| **API Rate Limiting** | 10 req/min per IP on AI generation, discovery, and verification          |
| **Prompt Injection**  | `sanitize_scraped_content()` strips URLs, emails, and special characters |
| **Send Throttling**   | Adaptive health-based limits + working hours enforcement                 |
| **Secrets**           | Environment variables via `.env` (gitignored)                            |

---

## 🚢 Deployment

| Component           | Platform         | Config                             |
| ------------------- | ---------------- | ---------------------------------- |
| **Frontend**        | Vercel           | `vercel.json` — serverless Next.js |
| **Backend API**     | Railway          | `railway.toml` + `Dockerfile`      |
| **Temporal Worker** | Railway / Docker | `Dockerfile.worker`                |
| **Temporal Server** | Docker Compose   | `docker-compose.yml`               |
| **Database**        | Supabase Cloud   | Managed PostgreSQL                 |

---

## 🤝 Contributing

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

> Please ensure backend changes pass linting tests and frontend changes preserve the glassmorphism design language.

---

<p align="center">Built with elegance and precision. Designed by <strong>Siddharth</strong>.</p>
