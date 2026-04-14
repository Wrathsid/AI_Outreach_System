"""
AI generation, variant scoring, and memory/caching functions.

Contains the core generation pipeline: multi-variant generation,
reply-rate optimization via parameter biasing, opener deduplication,
and brain context caching.
Extracted from drafts.py for maintainability.
"""

import hashlib
import time

from typing import Any, Dict, List, Optional

from backend.config import (
    get_supabase,
    generate_with_gemini,
    generate_with_groq,
    get_groq_client,
    logger,
)
from backend.services.embeddings import embeddings_service
from backend.services.scoring import score_draft


# ============================================================
# P2: BRAIN CONTEXT CACHE (5-min TTL)
# ============================================================
_brain_cache: dict = {}
_BRAIN_CACHE_TTL = 300  # 5 minutes

_biased_params_cache: dict = {}
_BIASED_PARAMS_TTL = 900  # 15 minutes


def get_cached_brain_context(supabase) -> dict:
    """Fetch brain context with in-memory caching (P2)."""
    now = time.time()
    if (
        "_brain" in _brain_cache
        and (now - _brain_cache.get("_ts", 0)) < _BRAIN_CACHE_TTL
    ):
        return _brain_cache["_brain"]
    try:
        b_data = supabase.table("brain_context").select("*").eq("id", 1).execute().data
        brain = b_data[0] if b_data else {"extracted_skills": []}
    except Exception:
        brain = {"extracted_skills": []}
    _brain_cache["_brain"] = brain
    _brain_cache["_ts"] = now
    return brain


# ============================================================
# REPLY-RATE OPTIMIZATION FUNCTIONS
# ============================================================


def get_recent_opener_hashes(supabase, limit: int = 50) -> List[str]:
    """Fetch hashes of recently sent openers to avoid repetition (Optimization 13)."""
    try:
        res = (
            supabase.table("sent_openers")
            .select("opener_hash")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [d["opener_hash"] for d in res.data]
    except Exception as e:
        logger.error(f"Memory fetch (hashes) failed: {e}")
        return []


def get_semantically_similar_openers(
    supabase, embedding: List[float], threshold: float = 0.85
) -> List[Dict]:
    """Search for semantically similar openers in Supabase (Optimization Phase 2)."""
    try:
        res = supabase.rpc(
            "match_sent_openers",
            {
                "query_embedding": embedding,
                "match_threshold": threshold,
                "match_count": 5,
            },
        ).execute()
        return res.data
    except Exception as e:
        logger.error(f"Semantic memory fetch failed: {e}")
        return []


def get_recent_openers(supabase, limit: int = 5) -> List[str]:
    """Fetch recent openers for the prompt to avoid repetition (Optimization 13)."""
    try:
        res = (
            supabase.table("drafts")
            .select("body")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        openers = []
        for d in res.data:
            body = d.get("body", "")
            if body:
                first_line = body.split("\n")[0].strip()
                if first_line:
                    if "," in first_line and len(first_line.split(",")[0]) < 20:
                        parts = first_line.split(",", 1)
                        if len(parts) > 1:
                            openers.append(parts[1].strip()[:50])
                    else:
                        openers.append(first_line[:50])
        return list(set(openers))
    except Exception as e:
        logger.error(f"Memory fetch failed: {e}")
        return []


def get_biased_parameters(supabase) -> Dict:
    """Analyze which parameters led to replies (Optimization Phase 2) with caching."""
    now = time.time()
    if (
        "_params" in _biased_params_cache
        and (now - _biased_params_cache.get("_ts", 0)) < _BIASED_PARAMS_TTL
    ):
        return _biased_params_cache["_params"]

    try:
        res = (
            supabase.table("drafts")
            .select("generation_params")
            .eq("reply_status", "replied")
            .limit(100)
            .execute()
        )

        if not res.data:
            _biased_params_cache["_params"] = {}
            _biased_params_cache["_ts"] = now
            return {}

        params_list = [
            d["generation_params"] for d in res.data if d.get("generation_params")
        ]
        if not params_list:
            _biased_params_cache["_params"] = {}
            _biased_params_cache["_ts"] = now
            return {}

        temps = [p.get("temperature") for p in params_list if p.get("temperature")]
        avg_temp = sum(temps) / len(temps) if temps else None

        intents = [p.get("intent") for p in params_list if p.get("intent")]
        p_intent = max(set(intents), key=intents.count) if intents else None

        signals = [p.get("signal_type") for p in params_list if p.get("signal_type")]
        p_signal = max(set(signals), key=signals.count) if signals else None

        result = {
            "suggested_temperature": round(avg_temp, 2) if avg_temp else None,
            "best_intent": p_intent,
            "best_signal_type": p_signal,
            "sample_size": len(params_list),
        }
        _biased_params_cache["_params"] = result
        _biased_params_cache["_ts"] = now
        return result
    except Exception as e:
        logger.error(f"Parameter biasing retrieval failed: {e}")
        return {}


async def generate_with_scoring(
    prompt: str,
    contact_type: str,
    candidate_context: dict,
    num_variants: int = 3,
    suggested_temp: Optional[float] = None,
) -> Optional[Dict]:
    """Generate multiple variants and return the highest scoring one.

    This is the SECRET SAUCE for reply-rate optimization.
    User sees 1 draft, but we generated 3 and picked the best.
    """
    import asyncio

    sb_client = get_supabase()

    # System prompt (persona anchor)
    from backend.routers.drafts import SYSTEM_PROMPTS
    from backend.models.schemas import IntentType

    system_prompt = SYSTEM_PROMPTS.get(IntentType.OPPORTUNITY, "")

    base_temp = suggested_temp if suggested_temp is not None else 0.4

    # Generate variants with slightly different temperatures
    tasks = []
    # If Groq is available, use it as primary because it's much faster and reliable
    if get_groq_client():
        logger.info(f"Generating {num_variants} variants with Groq...")
        for i in range(num_variants):
            temp = base_temp + (i * 0.05)
            tasks.append(
                generate_with_groq(
                    prompt, temperature=temp, system_prompt=system_prompt
                )
            )
    else:
        logger.info(f"Generating {num_variants} variants with Gemini...")
        for i in range(num_variants):
            temp = base_temp + (i * 0.05)
            tasks.append(
                generate_with_gemini(
                    prompt, temperature=temp, system_prompt=system_prompt
                )
            )

    if not tasks:
        return None  # type: ignore[return-value]

    responses = await asyncio.gather(*tasks)

    # If Groq failed, fallback to Gemini
    if all(r is None for r in responses) and get_groq_client():
        logger.warning("Groq variants failed. Trying Gemini as fallback...")
        tasks = []
        for i in range(num_variants):
            temp = base_temp + (i * 0.05)
            tasks.append(
                generate_with_gemini(
                    prompt, temperature=temp, system_prompt=system_prompt
                )
            )
        responses = await asyncio.gather(*tasks)

    sent_hashes = get_recent_opener_hashes(sb_client)

    variants: List[Dict[str, Any]] = []
    for i, response_text in enumerate(responses):
        temp = base_temp + (i * 0.05)
        if response_text:
            opener = response_text.split("\n")[0].strip()
            if "," in opener and len(opener.split(",")[0]) < 20:
                opener = opener.split(",", 1)[1].strip()

            opener_hash = hashlib.md5(opener.lower().encode()).hexdigest()

            score = score_draft(response_text, contact_type, candidate_context)

            if opener_hash in sent_hashes:
                logger.warning(
                    f"Repeated opener detected (hash: {opener_hash[:8]}). Penalizing variant {i+1}."
                )
                score -= 80

            embedding = embeddings_service.generate_embedding(opener)
            if embedding:
                similar = get_semantically_similar_openers(sb_client, embedding)
            else:
                similar = []
            if similar:
                max_sim = max([s["similarity"] for s in similar])
                logger.warning(
                    f"Semantically similar opener detected (sim: {max_sim:.2f}). Penalizing variant {i+1}."
                )
                score -= 40 * max_sim

            variants.append(
                {
                    "text": response_text,
                    "score": score,
                    "temp": temp,
                    "opener_hash": opener_hash,
                    "embedding": embedding,
                }
            )
            logger.info(
                f"Variant {i+1}: score={score:.1f}, temp={temp}, hash={opener_hash[:8]}"
            )

    if variants:
        best = max(variants, key=lambda v: float(v["score"]))
        logger.info(f"SELECTED: score={best['score']:.1f}, temp={best['temp']}")
        return best

    return None
