# Cold Emailing System

AI-powered cold outreach with a calm, focused interface.

## Tech Stack

- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS, Framer Motion
- **Backend**: FastAPI, Python 3.12
- **Database**: Supabase (PostgreSQL)
- **AI**: Groq API (Llama 3.3 70B)

## Project Structure

```
cold-emailing/
├── frontend/                 # Next.js frontend
│   ├── src/
│   │   ├── app/             # App router pages
│   │   │   ├── brain/       # Personal AI settings
│   │   │   ├── candidates/  # Candidate profiles
│   │   │   ├── resources/   # Growth resources
│   │   │   ├── search/      # Search page
│   │   │   ├── success/     # Email sent success
│   │   │   └── waitlist/    # Waitlist page
│   │   ├── components/      # React components
│   │   │   ├── ui/          # Base UI components
│   │   │   └── ...          # Feature components
│   │   └── lib/             # Utilities & API client
│   └── public/              # Static assets
├── backend/                  # FastAPI backend
│   ├── main.py              # API endpoints
│   └── requirements.txt     # Python dependencies
├── database/                 # Database schema
│   └── schema.sql.md        # SQL for Supabase
└── .env                     # Environment variables (not committed)
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- Supabase account
- Groq API key

### Environment Variables

Create a `.env` file in the root:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_key
```

### Installation

1. **Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. **Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

3. **Database**
   - Go to Supabase SQL Editor
   - Run the SQL from `database/schema.sql.md`

### Development

- Frontend: http://localhost:3001
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Features

- 📊 **Dashboard** - Real-time stats and activity feed
- 🔍 **Search** - Find candidates in your pipeline
- 🧠 **Brain** - Configure AI personality and tone
- ✉️ **AI Drafts** - Generate personalized emails with Groq
- 📚 **Resources** - Curated outreach guides
- 🎨 **Premium UI** - Smooth animations, glassmorphism

## License

MIT
