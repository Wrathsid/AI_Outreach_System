<div align="center">
  <img src="https://raw.githubusercontent.com/Wrathsid/AI_Outreach_System/main/public/logo.png" alt="Cold Email Discovery Engine Logo" width="150" height="150" style="border-radius: 20%;">
  
  # ❄️ Cold Email Discovery Engine
  
  **The "Apple-style" Command Center for high-precision outreach.**  
  *Find leads, verify emails, and draft personalized sequences—all in one calm, focused interface.*

  <p>
    <a href="#-features"><img src="https://img.shields.io/badge/Features-Explore-blue?style=for-the-badge&logo=rocket" alt="Features"></a>
    <a href="#-technology-stack"><img src="https://img.shields.io/badge/Stack-Tech-black?style=for-the-badge&logo=code" alt="Tech"></a>
    <a href="#-getting-started"><img src="https://img.shields.io/badge/Install-Get_Started-green?style=for-the-badge&logo=terminal" alt="Getting Started"></a>
    <img src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge" alt="License">
  </p>
</div>

---

## ✨ Features

### 🔍 Deep Web Discovery

- **Role-Based Precision Search:** Enter any job title (e.g., "Senior React Developer") to instantly scrape high-intent hiring managers & recruiters actively posting jobs right now.
- **Dynamic Crawler Fallbacks:** Uses robust automated Bing & DuckDuckGo Search APIs to silently and smoothly crawl the open web for LinkedIn profiles and data endpoints without getting blocked.
- **Smart Filtering:** Ignore spam, focus purely on genuine leads.

### 🤖 Generative AI Email Pipeline

- **Smart Draft Generation:** Employs the cutting-edge **Gemini Pro/Flash LLM** to dissect a prospect's public footprint and construct a highly tailored, non-robot sounding introduction.
- **Built-In Batch AI Queueing:** Advanced backend task queuing (10 contacts/minute chunking) respects LLM provider rate limits, ensuring you can import 100+ candidates at once without throwing API errors.
- **Tone Customization:** Direct, humorous, or formal—choose your angle.
- **Automatic Fallback Templates:** Generates a reliable templated outline formatted beautifully when candidate data is too sparse.

### 🛡️ Pre-Delivery Verification

- **Real-Time SMTP Ping Verification:** Ensures "100% Delivery Confidence." The backend actively tests the MX records and pings identical SMTP mail servers in real-time to catch bounces before they happen.
- **Catch-All Detection:** Evaluates domains to stop generic info@ spam routing.

### 💅 Premium Glassmorphic UI

- **Lightning-Fast Next.js 14 Frontend:** Keyboard-navigable UI with Spotlight hover effects, translucent Apple-vision aesthetics, and buttery smooth animations driven by TailwindCSS and Framer Motion.

---

## 💻 Technology Stack

<div align="center">

| Area         | Technologies                                                     |
| :----------- | :--------------------------------------------------------------- |
| **Frontend** | ⚡ **Next.js 14** (App Router), React, TailwindCSS, Lucide Icons |
| **Backend**  | 🚀 **FastAPI** (Python 3.11+), Pydantic, Asyncio BackgroundTasks |
| **AI / NLP** | 🧠 Google **Gemini GenAI**, SentenceTransformers                 |
| **Database** | 🗄️ **Supabase** (PostgreSQL)                                     |
| **Scraping** | 🕷️ SerpAPI, DuckDuckGo Search                                    |

</div>

---

## 🚀 Getting Started

To get a local instance of the application up and running smoothly, follow these concise steps.

### Prerequisites

Ensure you have the following installed on your machine:

- [Node.js](https://nodejs.org/) (v18 or higher)
- [Python](https://www.python.org/downloads/) (3.11 or higher)
- [Git](https://git-scm.com/)

### 1. Clone the Repository

```bash
git clone https://github.com/Wrathsid/AI_Outreach_System.git
cd AI_Outreach_System
```

### 2. Configure Backend Setup (FastAPI Pipeline)

The backend handles AI generation, scraping, and email verification.

```bash
cd backend
python -m venv venv

# Activate the virtual environment:
# Windows:
.\\venv\\Scripts\\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:

```env
SUPABASE_URL="your-supabase-url"
SUPABASE_KEY="your-supabase-anon-key"
GEMINI_API_KEY="your-google-gemini-key"
SERPAPI_KEY="your-serpapi-api-key"
```

Start the backend application:

```bash
python -m backend.main
```

The backend API will run on `http://localhost:8000`.

### 3. Configure Frontend Setup (Next.js Application)

In a new terminal window, initialize the stunning UI component.

```bash
cd frontend
npm install
```

Create a `.env.local` file in the `frontend/` directory connecting to the same Supabase instance:

```env
NEXT_PUBLIC_SUPABASE_URL="your-supabase-url"
NEXT_PUBLIC_SUPABASE_ANON_KEY="your-supabase-anon-key"
```

Start the development web server:

```bash
npm run dev
```

Navigate to `http://localhost:3000` to dive into the Discovery Engine.

---

## 📁 Repository Architecture

```
AI_Outreach_System/
├── backend/
│   ├── routers/       # API interface endpoints (Drafts, Search, Testing)
│   ├── services/      # Core logic (AI Queues, Crawlers, SMTP verifiers)
│   ├── models/        # Pydantic schemas mapping
│   ├── requirements.txt
│   └── main.py        # FastAPI Application Entry
├── frontend/
│   ├── src/
│   │   ├── app/       # Next.js 14 App Router pages
│   │   ├── components/# React UI Components (Spotlight, Dialogs, Cards)
│   │   └── lib/       # API connectivity and Supabase integrations
│   ├── public/        # Static assets
│   ├── tailwind.config.ts
│   └── package.json
└── README.md
```

## 🤝 Contributing

Contributions are always welcome. Please ensure that backend modifications pass standard linting tests and new frontend capabilities preserve the minimalist, glassmorphism design parameters.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

<p align="center">Built with elegance and optimization in mind. Designed by Siddharth.</p>
