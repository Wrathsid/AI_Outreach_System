"""
Configuration and shared resources for the Cold Emailing backend.
Initializes Supabase, Groq, and other shared clients.
"""
import os
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv(dotenv_path="../.env")

# Environment Variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Supabase client
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[OK] Supabase connected")
    except Exception as e:
        print(f"[ERR] Supabase not connected: {e}")
else:
    print("[WARN] Supabase credentials not found - using local storage")

# Initialize Groq client
groq_client = None
if GROQ_API_KEY:
    try:
        from groq import Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("[OK] Groq API configured")
    except ImportError:
        print("[WARN] Groq library not installed")
else:
    print("[WARN] GROQ_API_KEY not found - AI features disabled")


async def generate_with_groq(prompt: str) -> str:
    """Generate text using Groq API (Llama 3.3 70B)."""
    if not GROQ_API_KEY:
        return None
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are an expert at writing personalized cold outreach emails that get responses. Keep emails short, personal, and compelling."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            print(f"Groq API error: {response.status_code} - {response.text}")
            return None


def setup_cors(app: FastAPI):
    """Configure CORS middleware for the FastAPI app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def get_supabase():
    """Get the Supabase client instance."""
    return supabase


def get_groq_client():
    """Get the Groq client instance."""
    return groq_client
