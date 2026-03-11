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
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("backend")

# Load environment variables
# Cloud platforms (Railway, Render) inject env vars directly — no .env file needed.
# For local development, we check the project root .env and backend/.env as fallbacks.
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent

# Try project root .env first, then backend-specific .env
for env_candidate in [project_root / ".env", backend_dir / ".env"]:
    if env_candidate.exists():
        load_dotenv(dotenv_path=env_candidate)
        break


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

# ============================================================
# Initialize Qubrid OpenAI Client
# ============================================================
_qubrid_client = None


def get_qubrid_client():
    """Get the Qubrid AsyncOpenAI client instance."""
    global _qubrid_client
    if _qubrid_client is not None:
        return _qubrid_client

    QUBRID_API_KEY = os.getenv("QUBRID_API_KEY")
    if QUBRID_API_KEY:
        try:
            from openai import AsyncOpenAI

            _qubrid_client = AsyncOpenAI(
                base_url="https://platform.qubrid.com/v1",
                api_key=QUBRID_API_KEY,
            )
            logger.info("Qubrid API configured (Client initialized)")
            return _qubrid_client
        except Exception as e:
            logger.error(f"Qubrid API error: {e}")
    else:
        logger.warning("QUBRID_API_KEY not found - Qubrid features disabled")
    return None


if "pytest" not in sys.modules:
    get_qubrid_client()


async def generate_with_gemini(
    prompt: str,
    temperature: float = 0.5,
    max_tokens: int = 300,
    system_prompt: str = None,
) -> str:
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
                            config=types.GenerateContentConfig(temperature=temperature),
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


async def generate_with_qubrid(
    prompt: str,
    temperature: float = 0.5,
    max_tokens: int = 1500,
    system_prompt: str = None,
) -> str:
    """Generate text using Qubrid Platform via OpenAI SDK."""
    client = get_qubrid_client()
    if not client:
        return None

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    try:
        import asyncio
        import random

        max_retries = 3
        base_delay = 2.0

        # We recommend Llama-3.3-70B over Fara-7B for highly detailed and structurally complex instructions
        model_name = "meta-llama/Llama-3.3-70B-Instruct"

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
                    timeout=20.0,
                )
                if response and response.choices and len(response.choices) > 0:
                    return response.choices[0].message.content
                return None

            except asyncio.TimeoutError:
                logger.warning(f"Qubrid {model_name} timed out on attempt {attempt+1}")
                if attempt < max_retries - 1:
                    sleep_time = (base_delay * (2**attempt)) + (random.random() * 0.5)
                    await asyncio.sleep(sleep_time)
                    continue
                break

            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    if attempt < max_retries - 1:
                        sleep_time = (base_delay * (2**attempt)) + (
                            random.random() * 0.5
                        )
                        logger.warning(
                            f"Qubrid {model_name} 429 Hit. Retrying in {sleep_time:.2f}s..."
                        )
                        await asyncio.sleep(sleep_time)
                        continue
                logger.error(f"Qubrid {model_name} Attempt {attempt+1} failed: {e}")
                if attempt == max_retries - 1:
                    break

        return None

    except Exception as e:
        logger.error(f"Qubrid API Critical Error: {e}")
        return None


def setup_cors(app: FastAPI):
    """Configure CORS middleware for the FastAPI app."""
    # Read allowed origins from env, or use secure defaults
    raw_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
    )
    allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def get_supabase():
    """Get the Supabase client instance."""
    return _supabase
