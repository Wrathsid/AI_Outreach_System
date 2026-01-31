import json
import logging
from typing import Generator, List, Dict
from .crawler import Crawler
from .email_patterns import EmailPatterns
from .verifier import verify_email_deep
from .confidence import ConfidenceScorer
from .hr_extractor import extract_context_info, extract_hr_score, parse_linkedin_title

class DiscoveryOrchestrator:
    """
    Controller that coordinates the entire lead discovery pipeline:
    Crawler -> Extractor -> Verifier -> Scorer -> Output
    """

    def __init__(self):
        self.crawler = Crawler()
        self.scorer = ConfidenceScorer()

    async def discover_leads_stream(self, role: str, limit: int = 20, broad_mode: bool = False) -> Generator[str, None, None]:
        """
        Async Stream with Parallel Verification.
        Crawl runs -> Queue -> Workers (Threaded Verification) -> Output
        """
        import asyncio

        result_queue = asyncio.Queue()
        # Semaphore to limit concurrent verifications (avoid killing OS network)
        verify_permits = asyncio.Semaphore(10) 
        
        mode_text = "Broad Mode" if broad_mode else "Precision Mode"
        yield json.dumps({"type": "status", "data": f"Starting Parallel Discovery ({mode_text})..."}) + "\n"

        # Background Manager to drive the process
        async def _manager():
            tasks = []
            try:
                # Iterate Async Crawler
                async for raw in self.crawler.crawl_stream(role, limit, broad_mode):
                    if raw["type"] == "status":
                        await result_queue.put(json.dumps(raw) + "\n")
                    elif raw["type"] == "raw_result":
                        # Spawn a verification task for each result
                        task = asyncio.create_task(_worker(raw["data"]))
                        tasks.append(task)
                
                # Wait for all verification tasks to complete
                if tasks:
                    await asyncio.gather(*tasks)
            except Exception as e:
                logging.error(f"Manager Error: {e}")
            finally:
                # Signal done
                await result_queue.put(None)

        # Worker: runs the sensitive/slow logic
        async def _worker(data):
            async with verify_permits:
                try:
                    # Run CPU/Network heavy 'process_raw_result' in thread
                    # self._process_raw_result contains the Blocking Verifier
                    lead = await asyncio.to_thread(self._process_raw_result, data, role)
                    if lead:
                         await result_queue.put(json.dumps({"type": "result", "data": lead}) + "\n")
                except Exception as e:
                    logging.error(f"Worker Error: {e}")

        # Start Manager
        manager_task = asyncio.create_task(_manager())

        # Yield results as they come in
        while True:
            item = await result_queue.get()
            if item is None:
                break
            yield item
        
        yield json.dumps({"type": "done", "data": "Discovery Complete."}) + "\n"


    def _process_raw_result(self, data: Dict, search_role: str) -> Dict:
        """
        Core logic: Extract -> Verify -> Score
        """
        title = data.get("title", "")
        body = data.get("body", "")
        url = data.get("url", "")
        
        # A. Identity Extraction
        name = "Candidate"
        role = search_role
        company = "Unknown"
        
        if "linkedin.com/in" in url:
            parsed = parse_linkedin_title(title)
            name = parsed["name"]
            role = parsed["role"]
            company = parsed["company"]
        elif "github.com" in url:
             # Basic GitHub title parsing
            parts = title.split("-")[0].strip()
            name = parts.split("(")[0].strip() or "GitHub User"
            company = "GitHub"

        # B. Email Extraction (Strict Regex)
        # Try finding email in body first, then title
        email = EmailPatterns.extract(body) or EmailPatterns.extract(title)
        
        # C. Context Enrichment (if we have email but generic name/role)
        if email and name == "Candidate":
            # Scanning around the email text for better info
            context_info = extract_context_info(body, email)
            if context_info["role"]: role = context_info["role"]
            
        # D. Triple Verification (DNS/SMTP) - 0 False Positives
        if email:
            is_valid = verify_email_deep(email)
            if not is_valid:
                return None # Reject invalid emails
        
        # E. HR/Role Analysis
        hr_data = extract_hr_score(role)
        
        # F. Acceptance Criteria
        # Must have verified email OR be a high-value HR target (we can enrich later)
        if not email and not hr_data["is_hr"]:
            return None

        # G. Construct Lead Object
        lead = {
            "name": name,
            "title": role,
            "company": company,
            "email": email,
            "linkedin_url": url,
            "source": "web_scan",
            "summary": body[:200],
            "is_hr": hr_data["is_hr"],
            "hr_score": hr_data["score"]
        }
        
        # H. Confidence Scoring
        lead = self.scorer.score(lead)
        
        return lead
