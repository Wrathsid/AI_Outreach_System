import os
import asyncio
import random
from typing import List, Generator, Dict
from dotenv import load_dotenv

load_dotenv()

class Crawler:
    """
    Handles searching using SerpAPI (Google) for reliable, production-grade results.
    Falls back to DuckDuckGo if SerpAPI fails.
    """
    
    def __init__(self):
        self.seen_urls = set()
        self.serpapi_key = os.getenv("SERPAPI_KEY")

    def get_queries_for_role(self, role: str) -> List[str]:
        """
        Generate specialized search queries targeting HR/recruiters hiring for this role.
        Focus on people POSTING jobs, not people looking for jobs.
        """
        role_lower = role.lower()
        
        # Tech Roles - Target tech recruiters and hiring managers
        tech_keywords = ['eng', 'dev', 'soft', 'data', 'cloud', 'security', 'full stack', 'qa', 'sre', 'devops', 'ml', 'ai']
        is_tech = any(k in role_lower for k in tech_keywords)
        
        # Creative Roles - Target creative recruiters
        creative_keywords = ['writer', 'content', 'copy', 'design', 'art', 'creative', 'ux', 'ui']
        is_creative = any(k in role_lower for k in creative_keywords)
        
        if is_tech:
            return [
                # LinkedIn posts from recruiters hiring for this role
                f'site:linkedin.com/posts \"hiring\" \"{role}\" recruiter',
                f'site:linkedin.com \"we are hiring\" \"{role}\" HR',
                f'site:linkedin.com \"looking for\" \"{role}\" talent acquisition',
                # Recruiters specializing in tech
                f'site:linkedin.com/in \"technical recruiter\" \"{role}\"',
                f'site:linkedin.com/in \"talent acquisition\" \"technology\"',
            ]
        elif is_creative:
            return [
                f'site:linkedin.com/posts \"hiring\" \"{role}\" recruiter',
                f'site:linkedin.com \"we are hiring\" \"{role}\" HR',
                f'site:linkedin.com/in \"creative recruiter\" \"{role}\"',
            ]
        else:
            return [
                # General recruiters and hiring managers
                f'site:linkedin.com/posts \"hiring\" \"{role}\"',
                f'site:linkedin.com \"we are hiring\" \"{role}\"',
                f'site:linkedin.com/in \"recruiter\" \"{role}\"',
            ]

    def get_broad_queries(self, role: str) -> List[str]:
        """
        Broad Reach Mode: High volume queries targeting hiring posts.
        """
        return [
            f'site:linkedin.com/posts \"hiring {role}\"',
            f'site:linkedin.com \"we\'re hiring\" \"{role}\"',
            f'\"hiring manager\" \"{role}\" email',
            f'\"talent acquisition\" \"{role}\" contact',
            f'\"recruiter\" \"{role}\" hiring',
        ]

    async def crawl_stream(self, role: str, limit: int = 20, broad_mode: bool = False) -> Generator[Dict, None, None]:
        """
        Async Generator: Yields raw search results using SerpAPI.
        """
        if broad_mode:
            queries = self.get_broad_queries(role)
        else:
            queries = self.get_queries_for_role(role)

        count = 0
        mode_text = "Broad Mode" if broad_mode else "Precision Mode"
        yield {"type": "status", "data": f"Starting {mode_text} search for '{role}'..."}

        for q in queries:
            if count >= limit:
                break
            
            yield {"type": "status", "data": f"Searching: {q[:50]}..."}
            await asyncio.sleep(random.uniform(0.5, 1.5))  # Small delay between queries

            results = []

            # Primary: SerpAPI (Google)
            if self.serpapi_key:
                try:
                    def _serpapi_search(query, api_key):
                        from serpapi import GoogleSearch
                        params = {
                            "q": query,
                            "api_key": api_key,
                            "num": 10,
                            "engine": "google"
                        }
                        search = GoogleSearch(params)
                        data = search.get_dict()
                        organic = data.get("organic_results", [])
                        return [
                            {
                                "title": r.get("title", ""),
                                "body": r.get("snippet", ""),
                                "href": r.get("link", "")
                            }
                            for r in organic
                        ]
                    
                    results = await asyncio.to_thread(_serpapi_search, q, self.serpapi_key)
                    if results:
                        yield {"type": "status", "data": f"Found {len(results)} results via SerpAPI"}
                except Exception as e:
                    yield {"type": "status", "data": f"SerpAPI error: {str(e)[:50]}"}

            # Fallback: DuckDuckGo (if SerpAPI fails or no key)
            if not results:
                yield {"type": "status", "data": "Trying DuckDuckGo fallback..."}
                try:
                    def _ddg_search(query):
                        from ddgs import DDGS
                        with DDGS() as ddgs:
                            try:
                                return list(ddgs.text(query, max_results=10))
                            except:
                                return []
                    
                    ddg_results = await asyncio.to_thread(_ddg_search, q)
                    if ddg_results:
                        results = [
                            {
                                "title": r.get("title", ""),
                                "body": r.get("body", ""),
                                "href": r.get("href", "")
                            }
                            for r in ddg_results
                        ]
                except Exception:
                    pass

            if not results:
                yield {"type": "status", "data": "No results for this query."}

            for r in results:
                if count >= limit:
                    break
                url = r.get("href", "")
                if not url or url in self.seen_urls:
                    continue
                self.seen_urls.add(url)
                count += 1
                
                yield {
                    "type": "raw_result",
                    "data": {
                        "title": r.get("title", "Unknown"),
                        "body": r.get("body", ""),
                        "url": url
                    }
                }

        yield {"type": "status", "data": f"Crawl complete. Found {count} results."}
