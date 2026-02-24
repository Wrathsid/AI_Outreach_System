import json
import logging
from typing import Generator, List, Dict
from .crawler import Crawler
from .email_patterns import EmailPatterns
from .email_verifier import verify_email
from .confidence import ConfidenceScorer
from .hr_extractor import extract_context_info, extract_hr_score, parse_linkedin_title
from .email_generator import EmailGenerator
from .embeddings import embeddings_service

class DiscoveryOrchestrator:
    """
    Controller that coordinates the entire lead discovery pipeline:
    Crawler -> Extractor -> Verifier -> Scorer -> Output
    """

    def __init__(self):
        self.crawler = Crawler()
        self.scorer = ConfidenceScorer()

    async def discover_leads_stream(self, role: str, limit: int = 20, broad_mode: bool = False, icp_context: str = None, company_size: str = None, revenue: str = None, tech: str = None) -> Generator[str, None, None]:
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

        # Pre-calculate ICP embedding if context provided (Optimization)
        icp_emb = None
        if icp_context:
            try:
                icp_emb = embeddings_service.generate_embedding(icp_context)
                yield json.dumps({"type": "status", "data": "ICP Context Analyzed & Embedded."}) + "\n"
            except Exception as e:
                logging.error(f"ICP Embedding Error: {e}")


        # Background Manager to drive the process
        async def _manager():
            tasks = []
            try:
                # Iterate Async Crawler
                async for raw in self.crawler.crawl_stream(role, limit, broad_mode, company_size, revenue, tech):
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
                    # Run async 'process_raw_result' 
                    lead = await self._process_raw_result(data, role, icp_emb=icp_emb)
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


    async def _process_raw_result(self, data: Dict, search_role: str, icp_emb: List[float] = None) -> Dict:
        """
        Core logic: Extract -> Verify -> Score
        """
        title = data.get("title", "")
        body = data.get("body", "")
        url = data.get("url", "")
        
        # A. Identity Extraction
        name = ""  # Empty until we find a real name
        role = search_role
        company = "Unknown"
        
        if "linkedin.com/in" in url:
            parsed = parse_linkedin_title(title)
            name = parsed["name"]
            role = parsed["role"]
            company = parsed["company"]
        elif "linkedin.com/posts" in url or "linkedin.com/feed" in url:
            # LinkedIn post — extract poster name from title snippet first (most reliable)
            from backend.services.hr_extractor import (
                parse_linkedin_post_url, extract_poster_info_from_snippet, 
                extract_role_from_post_body
            )
            
            # Layer 1: Extract name from Google snippet title (most reliable for names)
            # e.g. "Ramiro Torres on LinkedIn: We are Hiring!!" → "Ramiro Torres"
            snippet_info = extract_poster_info_from_snippet(title, body)
            if snippet_info.get("name"):
                name = snippet_info["name"]
            
            # Layer 2: Fallback — extract from URL slug only if snippet didn't find a name
            if not name:
                url_info = parse_linkedin_post_url(url)
                if url_info.get("name"):
                    name = url_info["name"]
            
            # Layer 3: Extract company/title from snippet
            if snippet_info.get("company"):
                company = snippet_info["company"]
            if snippet_info.get("title"):
                role = snippet_info["title"]
            
            # Layer 4: Extract role being hired for from body
            post_role = extract_role_from_post_body(body)
            if post_role and role == search_role:
                role = post_role
            
            # Layer 4: Company extraction from body (fallback)
            if company == "Unknown":
                import re
                company_patterns = [
                    r'at\s+([A-Z][A-Za-z0-9\s&\.]+?)(?:\s+is|\s+are|\.|,|!)',
                    r'@\s*([A-Z][A-Za-z0-9\s&\.]+?)(?:\s+is|\s+are|\.|,|!)',
                    r'([A-Z][A-Za-z0-9\s&\.]+?)\s+is\s+hiring',
                    r'Join\s+([A-Z][A-Za-z0-9\s&\.]+?)(?:\s+as|\s+team|\.|,|!)',
                ]
                for pattern in company_patterns:
                    match = re.search(pattern, body)
                    if match:
                        potential_company = match.group(1).strip()
                        if len(potential_company) > 2 and potential_company.lower() not in ['the', 'our', 'we', 'this', 'that']:
                            company = potential_company
                            break
        elif "github.com" in url:
             # Basic GitHub title parsing
            parts = title.split("-")[0].strip()
            name = parts.split("(")[0].strip() or "GitHub User"
            company = "GitHub"

        # B. Entity Classification & Swap
        # "EXPANSIA" check - sometimes the "name" extracted is actually a company
        from backend.services.hr_extractor import classify_entity
        
        entity_type = classify_entity(name)
        if entity_type == "COMPANY":
            # The extracted 'name' is actually a company
            if company == "Unknown":
                company = name
            
            # We need to find the real person's name from the body using AI
            # The user specifically requested "AI should understand"
            try:
                from backend.config import generate_with_gemini
                
                prompt = (
                    f"Analyze this LinkedIn post/profile. The apparent author is '{name}', which looks like a company.\n"
                    f"Find the Name of the actual hiring manager or recruiter mentioned in the text.\n"
                    f"If no specific person is named, return 'Hiring Team'.\n"
                    f"Return ONLY the name. No quotes.\n\n"
                    f"Title: {title}\n"
                    f"Body: {body[:1000]}"
                )
                
                ai_name = await generate_with_gemini(prompt)
                if ai_name:
                    cleaned_name = ai_name.strip().strip('"').strip("'")
                    # If AI just returns the company name again, use Hiring Team
                    if cleaned_name.lower() == name.lower() or len(cleaned_name) < 2:
                        name = "Hiring Team"
                    else:
                        name = cleaned_name
                else:
                    name = "Hiring Team"
                    
            except Exception as e:
                logging.error(f"AI Name Extraction Failed: {e}")
                name = "Hiring Team"

        # C. Email Extraction (Strict Regex)
        email = EmailPatterns.extract(body) or EmailPatterns.extract(title)
        
        # C. Context Enrichment
        if email and not name:
            context_info = extract_context_info(body, email)
            if context_info["role"]: role = context_info["role"]
        
        # D. HR/Role Analysis
        hr_data = extract_hr_score(role)
            
        # E. Email Verification (if present)
        generated_email = None
        email_confidence = 0
        
        if email:
            verify_res = await verify_email(email)
            if verify_res.get("status") == "invalid": 
                email = None
        
        # F. Email Generation (DISABLED PER USER REQUEST - Feb 10)
        # RELAXED: Generate even with "Candidate" if we have company
        # should_generate = (
        #     not email and 
        #     company and 
        #     company not in ["Unknown", "N/A", ""] and
        #     len(company) > 2
        # )
        
        # if should_generate:
        #     # If name is still "Candidate", try to extract from title
        #     if name == "Candidate":
        #         # Try to extract a real name from the title
        #         import re
        #         # Pattern: "Name - Role" or "Name | Role" or just a capitalized name
        #         title_parts = re.split(r'[-|]', title)
        #         if title_parts:
        #             potential_name = title_parts[0].strip()
        #             # Check if it looks like a real name (has at least 2 words or is capitalized)
        #             if ' ' in potential_name or (potential_name and potential_name[0].isupper()):
        #                 name = potential_name
            
        #     # Generate email with whatever name we have
        #     generated = EmailGenerator.get_best_guess(name, company)
        #     if generated:
        #         generated_email = generated["email"]
        #         email_confidence = generated["confidence"]

        # G. Acceptance Criteria (RELAXED - return everything)
        # Only reject if literally no name AND no valid info
        # G. Acceptance Criteria - PRIORITIZE RECRUITERS & HIRING MANAGERS
        # Reject if literally no name AND no valid info
        if not name and not url:
             return None
        
        # CRITICAL: Filter out non-HR people
        # We want RECRUITERS and HIRING MANAGERS, not regular job seekers
        # Accept only if:
        # 1. High HR score (0.65+) - definitely a recruiter/HR
        # 2. OR posting contains hiring keywords in title/body
        
        hr_score = hr_data.get("score", 0)
        is_hr = hr_data.get("is_hr", False)
        
        # Check if this is a hiring post (not just a profile)
        hiring_keywords = ["we are hiring", "we're hiring", "join our team", "hiring for", 
                          "now hiring", "open position", "job opening", "looking for",
                          "apply now", "open role", "job opportunity", "career opportunity"]
        is_hiring_post = any(keyword in title.lower() for keyword in hiring_keywords)
        is_hiring_post = is_hiring_post or any(keyword in body.lower() for keyword in hiring_keywords)
        
        # Classify result type: "job_posting" vs "person"
        # A result is a job posting if:
        #   - It contains hiring keywords in title/body
        #   - OR the name is still empty (no identifiable person)
        #   - AND it passed our HR filter
        result_type = "job_posting" if is_hiring_post else "person"
        
        # Fix the name for job postings — never show empty or generic names
        if not name and result_type == "job_posting":
            name = "Hiring Team"
        elif not name:
            name = "Unknown"
        
        # FILTER: Reject if not HR and not a hiring post
        if hr_score < 0.50 and not is_hiring_post:
            # This is just a regular person's profile, not a recruiter
            return None

        # H. Construct Lead Object
        lead = {
            "name": name if name else "Unknown",
            "title": role if role else search_role,
            "company": company if company else "Unknown",
            "email": email,  # Real email (verified)
            "generated_email": generated_email,  # AI-generated email
            "email_confidence": email_confidence,  # Confidence in generated email
            "linkedin_url": url,
            "source": "web_scan",
            "summary": body[:1000] if body else "",
            "is_hr": is_hr,
            "hr_score": hr_score,
            "resonance_score": 0.0,
            "result_type": result_type,  # "job_posting" or "person"
        }
        
        # I. Resonance Ranking (Phase 3)
        if icp_emb and body:
            try:
                lead_text = f"{title} {body[:500]}"
                lead_emb = embeddings_service.generate_embedding(lead_text)
                # icp_emb is already computed
                similarity = embeddings_service.calculate_similarity(lead_emb, icp_emb)
                lead["resonance_score"] = round(float(similarity), 3)
            except Exception as e:
                logging.error(f"Resonance calculation failed: {e}")
        
        # J. Confidence Scoring
        lead = self.scorer.score(lead)
        
        return lead

