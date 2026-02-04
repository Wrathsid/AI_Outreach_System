"""
Discovery router - Lead discovery and search endpoints.
"""
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from config import get_groq_client, GROQ_API_KEY
from models.schemas import ExtractionRequest
from services.discovery_orchestrator import DiscoveryOrchestrator

router = APIRouter(tags=["Discovery"])

# Initialize Orchestrator
orchestrator = DiscoveryOrchestrator()


@router.post("/extract-opportunity")
def extract_opportunity(request: ExtractionRequest):
    """Extract key info from job description text."""
    client = get_groq_client()
    if not GROQ_API_KEY or not client:
        return {"opportunity": "AI not configured"}
        
    try:
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Extract the core value proposition and key requirement from this text. Summarize it in one concise sentence starting with 'Opportunity to...' or 'Seeking...'"
                },
                {"role": "user", "content": request.text}
            ],
            model="llama3-8b-8192"
        )
        return {"opportunity": completion.choices[0].message.content}
    except Exception as e:
        print(f"Extraction Error: {e}")
        return {"opportunity": "Could not extract context"}


@router.get("/hr-search")
async def discovery_hr_search(role: str = "Recruiter", company: str = "", broad_mode: bool = False):
    """Method 1 & 3: Advanced HR Search (V2 Architecture)."""
    query = f"{role} {company}".strip()
    return StreamingResponse(
        orchestrator.discover_leads_stream(query, limit=30, broad_mode=broad_mode),
        media_type="application/x-ndjson"
    )


@router.get("")
def discover_candidates(role: str):
    """Deep web scan for candidates (Legacy Wrapper)."""
    results = []
    for line in orchestrator.discover_leads_stream(role, limit=15):
        try:
            msg = json.loads(line)
            if msg['type'] == 'result':
                results.append(msg['data'])
        except:
            pass
    return results


@router.get("/stream")
def discover_candidates_stream(role: str):
    """Deep web scan with real-time updates."""
    return StreamingResponse(
        _search_leads_generator(role),
        media_type="application/x-ndjson"
    )


def _search_leads_generator(role: str):
    """Wrapper to inject AI correction before streaming."""
    corrected_role = role
    client = get_groq_client()
    
    try:
        if GROQ_API_KEY and client:
            yield json.dumps({"type": "status", "data": "AI checking spelling..."}) + "\n"
            completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a spell checker. Correct the job title or search term. Return ONLY the corrected term. No quotes, no explanation. If correct, return original."
                    },
                    {"role": "user", "content": role}
                ],
                model="llama-3.3-70b-versatile",
            )
            suggestion = completion.choices[0].message.content.strip()
            if len(suggestion) < 50 and suggestion.lower() != role.lower():
                yield json.dumps({"type": "status", "data": f"Auto-corrected: '{role}' -> '{suggestion}'"}) + "\n"
                corrected_role = suggestion
    except Exception as e:
        yield json.dumps({"type": "error", "data": f"AI Error: {str(e)}"}) + "\n"

    yield from orchestrator.discover_leads_stream(corrected_role)
