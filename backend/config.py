"""
Configuration and shared resources for the Cold Emailing backend.
Initializes Supabase, Groq, and other shared clients.
"""
import os
import sys

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
_supabase = None

def get_supabase():
    """Get the Supabase client instance with lazy initialization."""
    global _supabase
    if _supabase is not None:
        return _supabase
        
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Supabase connected")
            return _supabase
        except Exception as e:
            logger.error(f"Supabase not connected: {e}")
    else:
        logger.warning("Supabase credentials not found - using local storage")
    return None

# Initialize it on module load if not in testing
if "pytest" not in sys.modules:
    get_supabase()

# Initialize Gemini client
_gemini_model = None

def get_gemini_model():
    """Get the Gemini model instance with lazy initialization."""
    global _gemini_model
    if _gemini_model is not None:
        return _gemini_model
        
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        try:
            from google import genai
            _gemini_model = genai.Client(api_key=GEMINI_API_KEY)
            logger.info("Gemini API configured (Client initialized)")
            return _gemini_model
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
    else:
        logger.warning("GEMINI_API_KEY not found - AI features disabled")
    return None

# Initialize it on module load if not in testing
if "pytest" not in sys.modules:
    get_gemini_model()


async def generate_with_gemini(prompt: str, temperature: float = 0.5, max_tokens: int = 300, system_prompt: str = None) -> str:
    """Generate text using Gemini API with Model Fallback."""
    client = get_gemini_model()
    if not client:
        return None
    
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\nUSER REQUEST:\n{prompt}"
    
    try:
        # Async generation with retry logic
        import asyncio
        import random
        from google.genai import types
        
        max_retries = 3
        base_delay = 2.0
        
        # Models to try (using new SDK model names)
        models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]
        
        for model_name in models_to_try:
            
            for attempt in range(max_retries):
                try:
                    # R4: Wrap in timeout to prevent hanging requests
                    response = await asyncio.wait_for(
                        client.aio.models.generate_content(
                            model=model_name,
                            contents=full_prompt,
                            config=types.GenerateContentConfig(
                                temperature=temperature,
                                max_output_tokens=max_tokens
                            )
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
                            # Try to extract the requested retry delay
                            import re
                            retry_match = re.search(r'retry in ([\d\.]+)s', error_str)
                            if retry_match:
                                sleep_time = min(float(retry_match.group(1)) + 1.0, 60.0)
                            else:
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
    return _supabase



