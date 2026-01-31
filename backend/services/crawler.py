import json
import time
import random
from typing import List, Generator, Dict
from ddgs import DDGS

class Crawler:
    """
    Handles safe searching using DuckDuckGo with rate limiting and robust error handling.
    """
    
    def __init__(self):
        self.seen_urls = set()

    def get_queries_for_role(self, role: str) -> List[str]:
        """
        Generate specialized dorks based on the role category.
        """
        role_lower = role.lower()
        
        # 1. Tech Roles
        tech_keywords = ['eng', 'dev', 'soft', 'data', 'cloud', 'security', 'full stack', 'qa', 'sre']
        is_tech = any(k in role_lower for k in tech_keywords)
        
        # 2. Creative Roles
        creative_keywords = ['writer', 'content', 'copy', 'design', 'art', 'creative', 'ux', 'ui']
        is_creative = any(k in role_lower for k in creative_keywords)
        
        if is_tech:
            return [
                # GitHub & StackOverflow
                f'site:github.com "{role}" "gmail.com"',
                f'site:github.com "{role}" "email" -site:github.com/orgs',
                f'site:stackoverflow.com/users "{role}" "gmail.com"',
                f'site:gitlab.com "{role}" "gmail.com"',
                f'site:dev.to "{role}" "gmail.com"',
                
                # Hiring Posts
                f'site:linkedin.com/posts "hiring" "{role}" "email me"',
                f'site:linkedin.com/feed "lookign for" "{role}" "send resume"',
                
                # Job Boards
                f'site:lever.co "{role}"',
                f'site:greenhouse.io "{role}"',
            ]
        elif is_creative:
            return [
                # Portfolio Sites
                f'site:medium.com "{role}" "gmail.com"',
                f'site:behance.net "{role}" "gmail.com"',
                f'site:dribbble.com "{role}" "email"',
                f'site:contently.com "{role}" "email"',
                
                # Social
                f'site:twitter.com "hiring" "{role}" "dm me"',
            ]
        else:
            # General
            return [
                f'site:linkedin.com/in/ "{role}" "email"',
                f'site:linkedin.com/posts "hiring" "{role}" "email me"',
                f'site:reddit.com "hiring" "{role}" "email"',
                f'site:x.com "hiring" "{role}" "email"',
            ]

    def get_broad_queries(self, role: str) -> List[str]:
        """
        Broad Reach Mode: High volume, lower precision.
        Directly searches for email patterns associated with the role across the entire web.
        """
        return [
            f'"{role}" "@gmail.com" -intitle:jobs -intitle:hiring',
            f'"{role}" "@outlook.com" -intitle:jobs',
            f'"{role}" "email me at" -site:linkedin.com',
            f'"{role}" "contact me" "@gmail.com"',
            f'"{role}" "resume" "@gmail.com" filetype:pdf',
        ]

    async def crawl_stream(self, role: str, limit: int = 20, broad_mode: bool = False) -> Generator[Dict, None, None]:
        """
        Async Generator: Yields raw search results (title, body, url).
        """
        import asyncio 

        if broad_mode:
            queries = self.get_broad_queries(role)
        else:
            queries = self.get_queries_for_role(role)
            # Add universal queries for normal mode
            queries += [
                f'site:linkedin.com/in/ "Talent Acquisition" "{role}" "email"',
                f'site:linkedin.com/posts "vacancy" "{role}" "send resume"',
            ]

        count = 0
        
        mode_text = "Broad Mode" if broad_mode else "Precision Mode"
        yield {"type": "status", "data": f"Initializing {mode_text} crawl for {len(queries)} potential sources..."}

        # We can't use 'with DDGS()' easily in async unless we wrap it carefully or it supports it.
        # DDGS context manager is sync. 
        # Safer to instantiate inside the thread or just use simple instantiation if possible.
        # DDGS() usage: it initializes session.
        
        for q in queries:
            if count >= limit: break
            
            yield {"type": "status", "data": f"Query: {q[:40]}..."}
            
            # Non-blocking delay
            await asyncio.sleep(random.uniform(1.8, 3.2))
            
            try:
                # Run blocking DDGS call in a separate thread
                # We define a helper to run inside the thread
                def _run_search(query):
                    with DDGS() as ddgs:
                        return list(ddgs.text(query, max_results=15))

                results = await asyncio.to_thread(_run_search, q)
                
                if not results: continue
                
                for r in results:
                    if count >= limit: break
                    
                    url = r.get('href', '')
                    if not url or url in self.seen_urls: continue
                    
                    self.seen_urls.add(url)
                    count += 1
                    
                    yield {
                        "type": "raw_result",
                        "data": {
                            "title": r.get('title', ''),
                            "body": r.get('body', ''),
                            "url": url
                        }
                    }
                    
            except Exception as e:
                print(f"Crawl error for {q}: {e}")
                continue
    
        yield {"type": "status", "data": "Crawl finished."}
