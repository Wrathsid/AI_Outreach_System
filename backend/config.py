"""
Configuration and shared resources for the Cold Emailing backend.
Initializes Supabase, Groq, and other shared clients.
"""
import os
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("backend")

# Load environment variables
import os
from pathlib import Path

# Get the backend directory
backend_dir = Path(__file__).resolve().parent
# Navigate to project root (parent of backend)
project_root = backend_dir.parent
env_path = project_root / ".env"

load_dotenv(dotenv_path=env_path)

# Environment Variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# OpenAI API Key - REMOVED (Migrated to Gemini)
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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

# Initialize Gemini client
import google.generativeai as genai
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-2.0-flash') # Updated to 2.0 Flash for 2026 era
        print("[OK] Gemini API configured")
    except Exception as e:
        print(f"[ERR] Gemini API error: {e}")
else:
    print("[WARN] GEMINI_API_KEY not found - AI features disabled")


async def generate_with_openai(prompt: str, temperature: float = 0.5, max_tokens: int = 300, system_prompt: str = None) -> str:
    """Generate text using Gemini API.
    
    Note: Function name kept as 'generate_with_openai' to minimize refactoring in other files,
    but implementation is Swapped to Gemini.
    """
    if not gemini_model:
        return None
    
    # Gemini distinct system prompt handling
    # We prepend system prompt to user prompt for simpler models or use key if supported
    # gemini-1.5-flash supports system_instruction at model init, but here we keep it simple per request
    
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\nUSER REQUEST:\n{prompt}"
    
    try:
        # Gemini temperature is distinct
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        # Async generation with retry logic (Optimization 70)
        # Gemini Free Tier has aggressive rate limits (15 RPM)
        import asyncio
        import random
        
        max_retries = 3
        base_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                response = await gemini_model.generate_content_async(
                    full_prompt,
                    generation_config=generation_config
                )
                return response.text
                
            except Exception as e:
                # Check for 429 Resource Exhausted
                if "429" in str(e) or "Resource has been exhausted" in str(e):
                    if attempt < max_retries - 1:
                        sleep_time = (base_delay * (2 ** attempt)) + (random.random() * 0.5)
                        print(f"[WARN] Gemini 429 Hit. Retrying in {sleep_time:.2f}s...")
                        await asyncio.sleep(sleep_time)
                        continue
                
                # If other error or max retries reached
                print(f"[ERR] Gemini API Attempt {attempt+1} failed: {e}")
                if attempt == max_retries - 1:
                    return None
        return None
    except Exception as e:
        print(f"Gemini API Critical Error: {e}")
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



