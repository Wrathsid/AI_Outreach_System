<div align="center">
  <h1>❄️ Cold Email Discovery Engine</h1>
  <p>
    <strong>The "Apple-style" Command Center for high-precision outreach.</strong>
  </p>
  <p>
    Find leads, verify emails, and draft personalized sequences—all in one calm, focused interface.
  </p>

  <!-- Badges -->
  <p>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License" /></a>
    <img src="https://img.shields.io/badge/Frontend-Next.js_14-black?logo=next.js" alt="Frontend" />
    <img src="https://img.shields.io/badge/Backend-FastAPI-teal?logo=fastapi" alt="Backend" />
    <img src="https://img.shields.io/badge/AI-Google_Gemini-purple?logo=google" alt="AI" />
    <img src="https://img.shields.io/badge/Database-Supabase-green?logo=supabase" alt="Database" />
  </p>
</div>

---

## 📖 Table of Contents

- [About the Project](#-about-the-project)
- [Key Features](#-key-features)
- [Tech Stack](#️-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Configuration](#️-configuration)
- [Usage](#-usage)
- [License](#-license)

## 🎯 About the Project

The **Cold Email Discovery Engine** is a specialized tool built to move beyond basic, spray-and-pray email lists. It provides a highly focused workspace to discover relevant professionals, strictly verify their contact information to ensure zero false positives, and leverage AI to draft personalized outreach emails.

Built with a "Calm Command Center" philosophy, the UI minimizes overwhelm with glassmorphism aesthetics, soft interactions, and full keyboard-centric navigation.

## ✨ Key Features

- **🔍 Deep Web Discovery**: Scans multiple sources (LinkedIn, GitHub, and niche communities) to find high-relevance leads that others miss.
  - _Role-based Search_: Type "DevOps Engineer" or "Growth Marketer" and get instant results.
  - _Real-time Streaming_: Results stream in instantly via Server-Sent Events (SSE).
  - _Broad vs. Precision Mode_: Toggle between wide-net scanning and laser-focused targeting.

- **✅ Triple-Layer Verification**: Every email goes through a rigorous check.
  - _Syntax Validation_: Checks format and domain structure.
  - _DNS Lookup_: Verifies domain records and MX server existence.
  - _SMTP Handshake_: Pings the actual mail server to confirm the user exists.

- **🧠 AI-Powered Context**: Don't just say "Hi". The engine analyzes summaries, companies, and roles to:
  - _Draft Personalized Openers_: Uses **Google Gemini** for high-speed, human-like intros.
  - _Match Scoring_: Auto-calculates fit based on resume analysis.

- **📋 Kanban Pipeline**: Manage outreach without spreadsheet chaos.
  - _One-Click Add_: Move verified leads from Search to Pipeline instantly.
  - _Status Tracking_: Visual pipeline for `New`, `Contacted`, and `Replied` leads.

## 🛠️ Tech Stack

**Frontend**

- [Next.js 14](https://nextjs.org/) (App Router)
- [Tailwind CSS](https://tailwindcss.com/)
- [Framer Motion](https://www.framer.com/motion/) (Micro-interactions)
- [Lucide React](https://lucide.dev/)

**Backend**

- [FastAPI](https://fastapi.tiangolo.com/) (Python)
- `asyncio` & Server-Sent Events (SSE)
- Custom Async Scraping Pipeline
- Testing: `pytest` & `pytest-asyncio`

**Infrastructure**

- **Database / Auth**: [Supabase](https://supabase.com/) (PostgreSQL)
- **AI Models**: Google Gemini API (1.5 / 2.0 Flash)

## 🚀 Getting Started

Follow these instructions to set up the project locally.

### Prerequisites

- **Node.js**: `v18.x` or higher
- **Python**: `3.10` or higher
- **Git**

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/Wrathsid/cold_email.git
cd cold_email
```

#### 2. Backend Setup

Navigate to the backend directory and set up the Python environment:

```bash
cd backend
python -m venv venv

# Activate the virtual environment:
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

#### 3. Frontend Setup

Navigate to the frontend directory and install Node dependencies:

```bash
cd ../frontend
npm install
```

## ⚙️ Configuration

Create a `.env` file in the `backend/` directory referencing your keys:

```text
# backend/.env
SUPABASE_URL="your_supabase_project_url"
SUPABASE_KEY="your_supabase_anon_key"

GEMINI_API_KEY="your_google_gemini_api_key"
```

## 💻 Usage

1. **Start the Backend Server**:
   ```bash
   cd backend
   python main.py
   # API available at http://localhost:8000
   ```
2. **Start the Frontend Server**:
   ```bash
   cd frontend
   npm run dev
   # UI available at http://localhost:3000
   ```
3. **Discover Leads**:
   Open `http://localhost:3000` in your browser. Use the central search bar and follow the intuitive UI flow to search, add, and generate drafts for your prospects!

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">
  <i>Built with focus and precision.</i>
</div>
