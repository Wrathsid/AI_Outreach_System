import os
import asyncio
import logging
import time
import re
from typing import Any, AsyncGenerator, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


def is_recent_post(url: str, snippet: str, max_days: int = 7) -> bool:
    """Check LinkedIn Activity ID timestamp and snippet text to strictly enforce recency."""
    match = re.search(r"activity-(\d{19})", url)
    if match:
        activity_id = int(match.group(1))
        # LinkedIn activity ID embeds the unix epoch in ms shifted by 22 bits
        timestamp_ms = activity_id >> 22
        current_time_ms = int(time.time() * 1000)
        age_days = (current_time_ms - timestamp_ms) / (1000 * 60 * 60 * 24)
        if age_days > max_days:
            return False

    # Fallback text check: reject months/years
    snippet_lower = snippet.lower()
    bad_patterns = [
        r"\d+\s*mo\b",
        r"\d+\s*mos\b",
        r"\d+\s*month",
        r"\d+\s*yr\b",
        r"\d+\s*yrs\b",
        r"\d+\s*year",
    ]
    for pattern in bad_patterns:
        if re.search(pattern, snippet_lower):
            return False

    return True


class Crawler:
    """
    Handles searching using Tavily / SerpAPI / DuckDuckGo for reliable results.
    Runs BOTH precision AND broad queries for maximum coverage, then applies
    strict LinkedIn-post + recency filters.
    """

    def __init__(self):
        self.seen_urls: set = set()
        self.serpapi_key = os.getenv("SERPAPI_KEY")
        self.tavily_key = os.getenv("TAVILY_API_KEY")

    def get_queries_for_role(
        self, role: str, company_size: Optional[str] = None, revenue: Optional[str] = None, tech: Optional[str] = None
    ) -> List[str]:
        """
        Generate specialized search queries targeting explicitly the hiring announcements / job postings for this role.
        We strict match on phrases like "we are hiring", "apply", "resume", to filter out general chatter.
        """
        filter_str = ""
        if tech:
            filter_str += f' "{tech}"'
        if company_size:
            filter_str += f' "{company_size}"'
        if revenue:
            filter_str += f' "{revenue}"'

        posting_indicators = (
            '("apply" OR "send resume" OR "dm me" OR "job description" OR "link below")'
        )

        base_queries = [
            f'site:linkedin.com/posts "hiring" "{role}" {posting_indicators}',
            f'site:linkedin.com/posts "we are hiring" "{role}"',
            f'site:linkedin.com/posts "looking for a {role}"',
            f'site:linkedin.com/posts "hiring a {role}"',
            f'site:linkedin.com/posts "hiring" "{role}" "join our team"',
        ]

        # Prioritize locations: India first, then Remote, then Global (no filter)
        priority_locations = ['"India"', '"Remote"', ""]
        all_queries = []

        for loc in priority_locations:
            for q in base_queries:
                combined_query = f"{q} {loc}".strip()
                all_queries.append(combined_query + filter_str)

        return all_queries

    def get_broad_queries(
        self, role: str, company_size: Optional[str] = None, revenue: Optional[str] = None, tech: Optional[str] = None
    ) -> List[str]:
        """
        Broad Reach Mode: High volume queries targeting explicit hiring posts.
        """
        filter_str = ""
        if tech:
            filter_str += f' "{tech}"'
        if company_size:
            filter_str += f' "{company_size}"'
        if revenue:
            filter_str += f' "{revenue}"'

        posting_indicators = '("apply" OR "resume" OR "dm me" OR "link" OR "join")'

        base_queries = [
            f'site:linkedin.com/posts "hiring {role}"',
            f'site:linkedin.com/posts "we\'re hiring" "{role}"',
            f'site:linkedin.com/posts "looking to hire" "{role}"',
            f'site:linkedin.com/posts "{role}" "hiring" {posting_indicators}',
            # Additional broad queries for wider net
            f'site:linkedin.com/posts "{role}" "opportunity" "hiring"',
            f'site:linkedin.com/posts "{role}" "open position"',
            f'site:linkedin.com/feed "hiring" "{role}"',
        ]

        # Prioritize locations: India first, then Remote, then Global (no filter)
        priority_locations = ['"India"', '"Remote"', ""]
        all_queries = []

        for loc in priority_locations:
            for q in base_queries:
                combined_query = f"{q} {loc}".strip()
                all_queries.append(combined_query + filter_str)

        return all_queries

    def _get_all_queries(
        self, role: str, company_size: Optional[str] = None, revenue: Optional[str] = None, tech: Optional[str] = None
    ) -> List[str]:
        """
        Combine BOTH precision and broad queries, de-duplicated and interleaved
        for maximum coverage. Precision queries run first for quality, then broad
        queries fill in the gaps.
        """
        precision = self.get_queries_for_role(role, company_size, revenue, tech)
        broad = self.get_broad_queries(role, company_size, revenue, tech)

        seen = set()
        combined: List[str] = []

        # Precision first
        for q in precision:
            if q not in seen:
                seen.add(q)
                combined.append(q)

        # Then broad
        for q in broad:
            if q not in seen:
                seen.add(q)
                combined.append(q)

        return combined

    async def _search_tavily(self, query: str) -> List[Dict[str, str]]:
        """Run a single Tavily search."""
        def _tavily_search(q, api_key):
            from tavily import TavilyClient
            client = TavilyClient(api_key=api_key)
            response = client.search(
                query=q,
                search_depth="basic",
                max_results=20,
            )
            return [
                {
                    "title": r.get("title", ""),
                    "body": r.get("content", ""),
                    "href": r.get("url", ""),
                }
                for r in response.get("results", [])
            ]

        return await asyncio.to_thread(_tavily_search, query, self.tavily_key)

    async def _search_serpapi(self, query: str) -> List[Dict[str, str]]:
        """Run a single SerpAPI (Google) search."""
        def _serpapi_search(q, api_key):
            from serpapi import GoogleSearch
            params = {
                "q": q,
                "api_key": api_key,
                "num": 20,
                "engine": "google",
                "tbs": "qdr:w",  # Restrict to Past Week
            }
            search = GoogleSearch(params)
            data = search.get_dict()
            organic = data.get("organic_results", [])
            return [
                {
                    "title": r.get("title", ""),
                    "body": r.get("snippet", ""),
                    "href": r.get("link", ""),
                }
                for r in organic
            ]

        return await asyncio.to_thread(_serpapi_search, query, self.serpapi_key)

    async def _search_ddg(self, query: str) -> List[Dict[str, str]]:
        """Run a single DuckDuckGo search with retry logic."""
        def _ddg_search(q):
            from duckduckgo_search import DDGS
            from duckduckgo_search.exceptions import RatelimitException

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    return list(DDGS().text(q, max_results=15, timelimit="w"))
                except RatelimitException:
                    wait_time = 2 ** (attempt + 1)
                    logging.warning(
                        f"DDG rate limited (attempt {attempt + 1}/{max_retries}). "
                        f"Waiting {wait_time}s..."
                    )
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                    else:
                        logging.error("DDG rate limit: all retries exhausted")
                        return []
                except (asyncio.TimeoutError, KeyError) as e:
                    logging.error(f"DDG data/timeout error: {e}")
                    return []
                except Exception as e:
                    import requests
                    if isinstance(e, requests.RequestException):
                        logging.error(f"DDG request error: {e}")
                    else:
                        logging.error(f"DDG search error: {e}")
                    return []
            return []

        ddg_results = await asyncio.to_thread(_ddg_search, query)
        return [
            {
                "title": r.get("title", ""),
                "body": r.get("body", ""),
                "href": r.get("href", ""),
            }
            for r in ddg_results
        ]

    def _is_valid_linkedin_post(self, url: str, body: str) -> bool:
        """
        Apply strict filtering: LinkedIn posts only, no job listings, recent only.
        This is the quality gate — ALL results must pass through this.
        """
        url_lower = url.lower()

        # Must be a LinkedIn URL
        if not url or "linkedin.com" not in url_lower:
            return False

        # Reject obvious non-personal or news/job pages
        bad_paths = ["/jobs/", "/job/", "/news/", "/story/", "/company/", "linkedin.com/company/"]
        if any(bad in url_lower for bad in bad_paths):
            return False

        # Must be a post, feed activity, or pulse article
        if not any(path in url_lower for path in ["/posts/", "/feed/", "/pulse/", "activity-"]):
            return False

        # Enforce strict 1-week time restriction
        if not is_recent_post(url, body, max_days=7):
            return False

        return True

    async def crawl_stream(
        self,
        role: str,
        limit: int = 20,
        broad_mode: bool = True,
        company_size: Optional[str] = None,
        revenue: Optional[str] = None,
        tech: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Async Generator: Yields raw search results.
        Runs ALL queries (precision + broad) for maximum coverage.
        """
        # Always combine both precision + broad for widest net
        queries = self._get_all_queries(role, company_size, revenue, tech)

        count = 0
        self.seen_urls = set()  # Reset per-request
        yield {"type": "status", "data": f"Starting comprehensive search for '{role}' ({len(queries)} query variations)..."}

        for q in queries:
            if count >= limit:
                break

            yield {"type": "status", "data": f"Searching: {q[:60]}..."}
            await asyncio.sleep(0.05)  # Small delay between queries

            results: List[Dict[str, str]] = []

            # Primary: Tavily
            if self.tavily_key and not results:
                try:
                    results = await self._search_tavily(q)
                    if results:
                        yield {"type": "status", "data": f"Found {len(results)} results via Tavily"}
                except (asyncio.TimeoutError, KeyError) as e:
                    logging.error(f"Tavily data/timeout error: {e}")
                    yield {"type": "status", "data": f"Tavily data/timeout error: {str(e)[:50]}"}
                except Exception as e:
                    import requests
                    if isinstance(e, requests.RequestException):
                        logging.error(f"Tavily request error: {e}")
                    else:
                        logging.error(f"Tavily error: {e}", exc_info=True)
                    yield {"type": "status", "data": f"Tavily error: {str(e)[:50]}"}

            # Fallback 1: SerpAPI
            if self.serpapi_key and not results:
                try:
                    results = await self._search_serpapi(q)
                    if results:
                        yield {"type": "status", "data": f"Found {len(results)} results via SerpAPI"}
                except (asyncio.TimeoutError, KeyError) as e:
                    logging.error(f"SerpAPI data/timeout error: {e}")
                    yield {"type": "status", "data": f"SerpAPI data/timeout error: {str(e)[:50]}"}
                except Exception as e:
                    import requests
                    if isinstance(e, requests.RequestException):
                        logging.error(f"SerpAPI request error: {e}")
                    else:
                        logging.error(f"SerpAPI error: {e}", exc_info=True)
                    yield {"type": "status", "data": f"SerpAPI error: {str(e)[:50]}"}

            # Fallback 2: DuckDuckGo
            if not results:
                yield {"type": "status", "data": "Trying DuckDuckGo fallback..."}
                try:
                    results = await self._search_ddg(q)
                    if not results:
                        yield {"type": "status", "data": "DuckDuckGo returned no results (may be rate limited)."}
                except Exception as e:
                    logging.error(f"DDG fallback error: {e}")
                    yield {"type": "status", "data": f"Search error: {str(e)[:60]}"}

            if not results:
                yield {"type": "status", "data": "No results for this query, trying next..."}
                continue

            # Apply strict quality filters
            for r in results:
                if count >= limit:
                    break
                url = r.get("href", "")
                body = r.get("body", "")

                # Skip already-seen URLs
                if url in self.seen_urls:
                    continue

                # Apply strict LinkedIn post + recency filter
                if not self._is_valid_linkedin_post(url, body):
                    continue

                self.seen_urls.add(url)
                count += 1

                yield {
                    "type": "raw_result",
                    "data": {
                        "title": r.get("title", "Unknown"),
                        "body": r.get("body", ""),
                        "url": url,
                    },
                }

        yield {"type": "status", "data": f"Crawl complete. Found {count} results."}
