"""
Discovery router - Lead discovery and search endpoints.
"""
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.config import generate_with_gemini, logger
from backend.models.schemas import ExtractionRequest, CrawlRequest, PatternRequest
from backend.services.discovery_orchestrator import DiscoveryOrchestrator

router = APIRouter(tags=["Discovery"])

# Initialize Orchestrator
orchestrator = DiscoveryOrchestrator()


@router.post("/extract-opportunity")
async def extract_opportunity(request: ExtractionRequest):
    """Extract key info from job description text."""
    # generate_with_gemini handles missing model internally
    try:
        response = await generate_with_gemini(
            request.text, 
            system_prompt="Extract the core value proposition and key requirement from this text. Summarize it in one concise sentence starting with 'Opportunity to...' or 'Seeking...'"
        )
        return {"opportunity": response if response else "Could not extract context"}
    except Exception as e:
        logger.error(f"Extraction Error: {e}")
        return {"opportunity": "Could not extract context"}


@router.post("/crawl")
async def crawl_domain(request: CrawlRequest):
    """Crawl a domain to extract text content."""
    # Simple implementation using httpx for now
    import httpx
    from bs4 import BeautifulSoup
    
    try:
        url = request.domain
        if not url.startswith("http"):
            url = f"https://{url}"
            
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            resp = await client.get(url)
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        # Limit text length
        return {"text": text[:5000], "status": "success"}
    except Exception as e:
        return {"text": "", "status": "error", "message": str(e)}


@router.post("/pattern")
def predict_pattern(request: PatternRequest):
    """Predict email pattern for a person."""
    from backend.services.email_generator import EmailGenerator
    
    # Use EmailGenerator to guess pattern
    # It takes name and company. Domain in request is often company domain.
    # We can try to infer company from domain if pattern request has it.
    
    company = request.domain
    if "." in company:
        company = company.split(".")[0]
        
    name = f"{request.first_name} {request.last_name}".strip()
    
    guess = EmailGenerator.get_best_guess(name, company)
    
    if guess:
        return {"pattern": guess["pattern"], "email": guess["email"], "confidence": guess["confidence"]}
    else:
        return {"pattern": None, "email": None, "confidence": 0}


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
async def discover_candidates_stream(role: str):
    """Deep web scan with real-time updates."""
    return StreamingResponse(
        _search_leads_generator(role),
        media_type="application/x-ndjson"
    )


async def _search_leads_generator(role: str):
    """Wrapper to inject AI correction before streaming."""
    corrected_role = role
    
    try:
            suggestion = await generate_with_gemini(
                role,
                system_prompt="You are a spell checker. Correct the job title or search term. Return ONLY the corrected term. No quotes, no explanation. If correct, return original."
            )
            
            if suggestion and len(suggestion) < 50 and suggestion.lower() != role.lower():
                yield json.dumps({"type": "status", "data": f"Auto-corrected: '{role}' -> '{suggestion}'"}) + "\n"
                corrected_role = suggestion
    except Exception as e:
        yield json.dumps({"type": "error", "data": f"AI Error: {str(e)}"}) + "\n"

    for item in orchestrator.discover_leads_stream(corrected_role):
        yield item
