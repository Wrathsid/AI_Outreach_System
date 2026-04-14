"""
Configuration and shared resources for the Cold Emailing backend.
Initializes Supabase, Groq, and other shared clients.
"""

import os
import sys
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("backend")

# Load environment variables
# Cloud platforms (Railway, Render) inject env vars directly — no .env file needed.
# For local development, we check the project root .env and backend/.env as fallbacks.
from pathlib import Path  # noqa: E402

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent

# Try project root .env first, then backend-specific .env
for env_candidate in [project_root / ".env", backend_dir / ".env"]:
    if env_candidate.exists():
        load_dotenv(dotenv_path=env_candidate)
        break

# ============================================================
# ENV VAR VALIDATION — Fail-fast on missing critical vars
# ============================================================
REQUIRED_ENV_VARS = ["SUPABASE_URL", "SUPABASE_KEY"]
OPTIONAL_ENV_VARS = [
    "GEMINI_API_KEY", "QUBRID_API_KEY", "SERPAPI_KEY",
    "HUNTER_API_KEY", "TAVILY_API_KEY", "GROQ_API_KEY",
]

_missing_required = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
_missing_optional = [v for v in OPTIONAL_ENV_VARS if not os.getenv(v)]

if _missing_required:
    logger.warning(
        f"Missing REQUIRED env vars: {_missing_required}. "
        "Some features will not work. Set these in your .env file."
    )
if _missing_optional:
    logger.info(f"Missing optional env vars: {_missing_optional}")

# Environment Variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

import threading

# Use thread-local storage for instances that use synchronous httpx clients 
# to prevent WinError 10035 non-blocking socket issues across FastAPI threadpool workers.
_thread_local = threading.local()

def get_supabase():
    """Get the Supabase client instance with thread-local lazy initialization."""
    if hasattr(_thread_local, 'supabase') and _thread_local.supabase is not None:
        return _thread_local.supabase

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client

            client = create_client(SUPABASE_URL, SUPABASE_KEY)
            _thread_local.supabase = client
            return client
        except ImportError as e:
            logger.error(f"Supabase package not installed: {e}")
        except (ValueError, ConnectionError) as e:
            logger.error(f"Supabase connection failed: {e}")
        except Exception as e:
            logger.error(f"Supabase not connected: {e}")
    else:
        logger.warning("Supabase credentials not found - using local storage")
    return None

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
        except ImportError as e:
            logger.error(f"Google GenAI package not installed: {e}")
        except (ValueError, ConnectionError) as e:
            logger.error(f"Gemini API connection error: {e}")
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
    else:
        logger.warning("GEMINI_API_KEY not found - AI features disabled")
    return None


# Initialize it on module load if not in testing
if "pytest" not in sys.modules:
    get_gemini_model()

# ============================================================
# ============================================================
# Initialize Groq OpenAI Client
# ============================================================
_groq_client = None


def get_groq_client():
    """Get the Groq AsyncOpenAI client instance."""
    global _groq_client
    if _groq_client is not None:
        return _groq_client

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if GROQ_API_KEY:
        try:
            from openai import AsyncOpenAI

            _groq_client = AsyncOpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=GROQ_API_KEY,
            )
            logger.info("Groq API configured (Client initialized)")
            return _groq_client
        except ImportError as e:
            logger.error(f"OpenAI package not installed: {e}")
        except (ValueError, ConnectionError) as e:
            logger.error(f"Groq API connection error: {e}")
        except Exception as e:
            logger.error(f"Groq API error: {e}")
    else:
        logger.warning("GROQ_API_KEY not found - Groq features disabled")
    return None


if "pytest" not in sys.modules:
    get_groq_client()


async def generate_with_gemini(
    prompt: str,
    temperature: float = 0.5,
    max_tokens: int = 1500,
    system_prompt: Optional[str] = None,
) -> Optional[str]:
    """Generate text using Gemini API with Model Fallback."""
    client = get_gemini_model()
    if not client:
        return None

    try:
        # Async generation with retry logic
        import asyncio
        import random
        from google.genai import types

        max_retries = 2
        base_delay = 1.5

        # Models to try (fast first, then fallback)
        models_to_try = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]

        for model_name in models_to_try:

            for attempt in range(max_retries):
                try:
                    # R4: Wrap in timeout to prevent hanging requests
                    response = await asyncio.wait_for(
                        client.aio.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=temperature,
                                system_instruction=system_prompt,
                                max_output_tokens=max_tokens,
                            ),
                        ),
                        timeout=15.0,
                    )
                    return response.text

                except asyncio.TimeoutError:
                    print(
                        f"[WARN] Gemini {model_name} timed out on attempt {attempt+1}"
                    )
                    if attempt < max_retries - 1:
                        sleep_time = (base_delay * (2**attempt)) + (
                            random.random() * 0.5
                        )
                        await asyncio.sleep(sleep_time)
                        continue
                    break  # Try next model

                except Exception as e:
                    if "429" in str(e) or "Resource has been exhausted" in str(e):
                        if attempt < max_retries - 1:
                            sleep_time = (base_delay * (2**attempt)) + (
                                random.random() * 0.5
                            )
                            if "retryDelay" in str(e):
                                try:
                                    err_str = (
                                        str(e).replace('"', '\\"').replace("'", '"')
                                    )
                                    # Very rough extraction since error might be weirdly formatted
                                    import re

                                    match = re.search(
                                        r'"retryDelay":\s*"(\d+)s"', err_str
                                    )
                                    if match:
                                        sleep_time = int(match.group(1))
                                except Exception:
                                    pass

                            sleep_time = min(sleep_time, 5)  # DEBUG: cap wait to 5s
                            logger.warning(
                                f"Gemini {model_name} 429 Hit. Retrying in {sleep_time:.2f}s..."
                            )
                            await asyncio.sleep(sleep_time)
                            continue

                    print(f"[ERR] Gemini {model_name} Attempt {attempt+1} failed: {e}")
                    if attempt == max_retries - 1:
                        break  # Try next model

            print(f"[INFO] Switching to fallback model after {model_name} failure...")

        return None

    except Exception as e:
        print(f"Gemini API Critical Error: {e}")
        return None


async def generate_with_groq(
    prompt: str,
    temperature: float = 0.5,
    max_tokens: int = 1500,
    system_prompt: Optional[str] = None,
) -> Optional[str]:
    """Generate text using Groq via OpenAI SDK."""
    client = get_groq_client()
    if not client:
        return None

    messages = []
    combined_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    messages.append({"role": "user", "content": combined_prompt})

    try:
        import asyncio
        import random

        max_retries = 2
        base_delay = 1.5

        # We recommend Llama-3.3-70B for highly detailed and structurally complex instructions
        model_name = "llama-3.3-70b-versatile"

        for attempt in range(max_retries):
            try:
                # Wrap in timeout
                response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=1,
                    ),
                    timeout=15.0,
                )
                if response.choices and response.choices[0].message:
                    return response.choices[0].message.content
                return None

            except asyncio.TimeoutError:
                print(f"[WARN] Groq {model_name} timed out on attempt {attempt+1}")
                if attempt < max_retries - 1:
                    sleep_time = (base_delay * (2**attempt)) + (random.random() * 0.5)
                    await asyncio.sleep(sleep_time)
                    continue
                break

            except Exception as e:
                print(f"[ERR] Groq {model_name} Attempt {attempt+1} failed: {e}")
                if "429" in str(e) or "Too Many Requests" in str(e):
                    if attempt < max_retries - 1:
                        sleep_time = (base_delay * (2**attempt)) + (random.random() * 0.5)
                        logger.warning(
                            f"Groq {model_name} 429 Hit. Retrying in {sleep_time:.2f}s..."
                        )
                        await asyncio.sleep(sleep_time)
                        continue
                if attempt == max_retries - 1:
                    break

        return None

    except Exception as e:
        logger.error(f"Groq API Critical Error: {e}")
        return None


def setup_cors(app: FastAPI):
    """Configure CORS middleware for the FastAPI app."""
    # Read allowed origins from env, or use secure defaults
    raw_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://192.168.0.234:3000,http://192.168.0.234:8000",
    )
    allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


