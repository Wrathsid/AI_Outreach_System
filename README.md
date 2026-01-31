# ❄️ Cold Email Discovery Engine

> **The "Apple-style" Command Center for high-precision outreach.**  
> Find leads, verify emails, and draft personalized sequences—all in one calm, focused interface.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Frontend](https://img.shields.io/badge/frontend-Next.js_14-black)
![Backend](https://img.shields.io/badge/backend-FastAPI-teal)
![AI](https://img.shields.io/badge/AI-Llama_3-purple)

---

## ✨ Features

### 🔍 Deep Web Discovery

Move beyond basic lists. Our **Discovery Engine** scans multiple sources (LinkedIn, GitHub, and niche communities) to find high-relevance leads that others miss.

- **Role-based Search**: Just type "DevOps Engineer" or "Growth Marketer".
- **Real-time Streaming**: Results appear instantly as they are found.
- **Broad vs. Precision Mode**: Toggle between wide-net scanning and laser-focused targeting.

### ✅ Triple-Layer Verification

Stop bouncing. Every email goes through a rigorous **Zero False Positive** check:

1.  **Syntax Validation**: Checks format and domain structure.
2.  **DNS Lookup**: Verifies domain records and MX server existence.
3.  **SMTP Handshake**: Pings the actual mail server (safely) to confirm the user exists.

### 🧠 AI-Powered Context

Don't just say "Hi". The engine analyzes the lead's summary, company, and role to:

- **Draft Personalized Openers**: Uses Llama-3 to write human-like intros.
- **Match Scoring**: Auto-calculates how well a candidate fits your goals.

### 📋 Kanban Pipeline

Manage your outreach without the spreadsheet chaos.

- **One-Click Add**: Move verified leads from Search to Pipeline instantly.
- **Status Tracking**: New $\rightarrow$ Contacted $\rightarrow$ Replied.
- **Soft UI**: A "Calm Command Center" designed to reduce overwhelm.

---

## 🛠️ Tech Stack

- **Frontend**: Next.js 14, Tailwind CSS, Framer Motion (Glassmorphism & Micro-interactions).
- **Backend**: FastAPI (Python), Asyncio, SSE (Server-Sent Events).
- **Database**: Supabase (PostgreSQL).
- **AI**: Groq API (Llama-3-70b).

---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/Wrathsid/cold_email.git
cd cold_email
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Environment Variables

Create a `.env` file in `backend/` with:

```env
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
GROQ_API_KEY=your_groq_key
```

---

_Built with focus and precision._
