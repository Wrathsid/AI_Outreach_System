"""
Configuration and shared resources for the Cold Emailing backend.
Initializes Supabase, Groq, and other shared clients.
"""
import os

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
        # Default to 1.5 Flash for stability, but we can try 2.0 if needed
        gemini_model = genai.GenerativeModel('gemini-1.5-flash') 
        print("[OK] Gemini API configured (Model: gemini-1.5-flash)")
    except Exception as e:
        print(f"[ERR] Gemini API error: {e}")
else:
    print("[WARN] GEMINI_API_KEY not found - AI features disabled")


async def generate_with_gemini(prompt: str, temperature: float = 0.5, max_tokens: int = 300, system_prompt: str = None) -> str:
    """Generate text using Gemini API with Model Fallback."""
    if not gemini_model:
        return None
    
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\nUSER REQUEST:\n{prompt}"
    
    try:
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        # Async generation with retry logic
        import asyncio
        import random
        
        max_retries = 3
        base_delay = 2.0
        
        models_to_try = ['gemini-1.5-flash', 'gemini-2.0-flash']
        
        for model_name in models_to_try:
            current_model = genai.GenerativeModel(model_name)
            
            for attempt in range(max_retries):
                try:
                    # R4: Wrap in timeout to prevent hanging requests
                    response = await asyncio.wait_for(
                        current_model.generate_content_async(
                            full_prompt,
                            generation_config=generation_config
                        ),
                        timeout=15.0
                    )
                    return response.text
                
                except asyncio.TimeoutError:
                    print(f"[WARN] Gemini {model_name} timed out on attempt {attempt+1}")
                    if attempt < max_retries - 1:
                        sleep_time = (base_delay * (2 ** attempt)) + (random.random() * 0.5)
                        await asyncio.sleep(sleep_time)
                        continue
                    break  # Try next model
                    
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "Resource has been exhausted" in error_str:
                        if attempt < max_retries - 1:
                            sleep_time = (base_delay * (2 ** attempt)) + (random.random() * 0.5)
                            print(f"[WARN] Gemini {model_name} 429 Hit. Retrying in {sleep_time:.2f}s...")
                            await asyncio.sleep(sleep_time)
                            continue
                    
                    print(f"[ERR] Gemini {model_name} Attempt {attempt+1} failed: {e}")
                    if attempt == max_retries - 1:
                        break # Try next model
            
            print(f"[INFO] Switching to fallback model after {model_name} failure...")

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



