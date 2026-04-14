import os
import asyncio
import logging
import time
import re
from typing import Any, AsyncGenerator, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def is_recent_post(url: str, snippet: str, max_days: int = 30) -> bool:
    """Check LinkedIn Activity ID timestamp to enforce recency.
    Uses 30-day window to maximize lead volume while staying relevant.
    Text-based snippet check removed — snippets contain profile bios with
    unrelated experience mentions (e.g. '5 years experience') that falsely rejected leads.
    """
    match = re.search(r"activity-(\d{19})", url)
    if match:
        activity_id = int(match.group(1))
        # LinkedIn activity ID embeds the unix epoch in ms shifted by 22 bits
        timestamp_ms = activity_id >> 22
        current_time_ms = int(time.time() * 1000)
        age_days = (current_time_ms - timestamp_ms) / (1000 * 60 * 60 * 24)
        if age_days > max_days:
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
        self._ddg_rate_limited = False  # Circuit breaker for DDG

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
            f'site:linkedin.com/posts "{role}" "opportunity" "hiring"',
            f'site:linkedin.com/posts "{role}" "open position"',
            f'site:linkedin.com/feed "hiring" "{role}"',
            # LinkedIn job listings for wider coverage
            f'site:linkedin.com/jobs "{role}"',
            f'site:linkedin.com/jobs "{role}" "apply"',
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
        """Run a single Tavily search with a 10s timeout."""
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

        return await asyncio.wait_for(
            asyncio.to_thread(_tavily_search, query, self.tavily_key),
            timeout=10.0,
        )

    async def _search_serpapi(self, query: str) -> List[Dict[str, str]]:
        """Run a single SerpAPI (Google) search using the new serpapi.Client."""
        def _serpapi_search(q, api_key):
            import serpapi
            client = serpapi.Client(api_key=api_key)
            data = client.search({
                "q": q,
                "num": 20,
                "engine": "google",
                "tbs": "qdr:w",  # Restrict to Past Week
            })
            organic = data.get("organic_results", [])
            return [
                {
                    "title": r.get("title", ""),
                    "body": r.get("snippet", ""),
                    "href": r.get("link", ""),
                }
                for r in organic
            ]

        return await asyncio.wait_for(
            asyncio.to_thread(_serpapi_search, query, self.serpapi_key),
            timeout=10.0,
        )

    async def _search_ddg(self, query: str) -> List[Dict[str, str]]:
        """Run a single DuckDuckGo search with fast-fail on rate limit."""
        # Circuit breaker: skip DDG entirely if already rate-limited this session
        if self._ddg_rate_limited:
            return []

        def _ddg_search(q):
            from duckduckgo_search import DDGS
            from duckduckgo_search.exceptions import RatelimitException

            try:
                return list(DDGS().text(q, max_results=15, timelimit="w"))
            except RatelimitException:
                logger.warning("DDG rate limited — activating circuit breaker")
                return "RATE_LIMITED"
            except (asyncio.TimeoutError, KeyError) as e:
                logger.error(f"DDG data/timeout error: {e}")
                return []
            except Exception as e:
                logger.error(f"DDG search error: {e}")
                return []

        ddg_results = await asyncio.wait_for(
            asyncio.to_thread(_ddg_search, query),
            timeout=10.0,
        )

        # If rate limited, set circuit breaker so we don't retry on remaining queries
        if ddg_results == "RATE_LIMITED":
            self._ddg_rate_limited = True
            return []

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
        Quality gate: LinkedIn posts, profiles, and activity pages only.
        Rejects job board listings and company pages.
        """
        url_lower = url.lower()

        # Must be a LinkedIn URL
        if not url or "linkedin.com" not in url_lower:
            return False

        # Reject news, story, and generic search pages
        bad_paths = ["/news/", "/story/"]
        if any(bad in url_lower for bad in bad_paths):
            return False

        # Reject bare company pages, but allow company posts
        if "linkedin.com/company/" in url_lower and "/posts/" not in url_lower:
            return False

        # Reject LinkedIn job SEARCH pages (keep only individual job listings)
        if "/jobs/search" in url_lower or url_lower.endswith("/jobs"):
            return False

        # Accept: posts, feed, pulse articles, individual job listings (/jobs/view/)
        if not any(path in url_lower for path in ["/posts/", "/feed/", "/pulse/", "activity-", "/jobs/view/"]):
            return False

        # Enforce 30-day recency (uses activity ID if available, skipped for job listings)
        if "/jobs/view/" not in url_lower:
            if not is_recent_post(url, body, max_days=30):
                return False

        return True

    async def _run_single_query(self, q: str) -> List[Dict[str, str]]:
        """Run a single query through Tavily → SerpAPI → DDG chain."""
        results: List[Dict[str, str]] = []

        if self.tavily_key:
            try:
                results = await self._search_tavily(q)
            except Exception as e:
                logging.error(f"Tavily error for '{q[:40]}': {e}")

        if self.serpapi_key and not results:
            try:
                results = await self._search_serpapi(q)
            except Exception as e:
                logging.error(f"SerpAPI error for '{q[:40]}': {e}")

        if not results and not self._ddg_rate_limited:
            try:
                results = await self._search_ddg(q)
            except Exception as e:
                logging.error(f"DDG error for '{q[:40]}': {e}")

        return results

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
        Runs queries in PARALLEL batches for maximum speed and coverage.
        """
        queries = self._get_all_queries(role, company_size, revenue, tech)

        # Use up to 20 queries but run them in parallel batches of 6
        max_queries = 20
        queries = queries[:max_queries]
        batch_size = 6  # Run 6 Tavily queries simultaneously

        count = 0
        self.seen_urls = set()
        self._ddg_rate_limited = False

        yield {"type": "status", "data": f"Starting parallel search for '{role}' ({len(queries)} queries)..."}

        # Process queries in parallel batches
        for batch_start in range(0, len(queries), batch_size):
            if count >= limit:
                break

            batch = queries[batch_start:batch_start + batch_size]
            yield {"type": "status", "data": f"Running {len(batch)} searches in parallel..."}

            # Run all queries in this batch simultaneously
            batch_results = await asyncio.gather(
                *[self._run_single_query(q) for q in batch],
                return_exceptions=True,
            )

            # Collect and filter all results from this batch
            batch_hits = 0
            for query_results in batch_results:
                if isinstance(query_results, Exception):
                    continue
                if not query_results:
                    continue

                for r in query_results:
                    if count >= limit:
                        break
                    url = r.get("href", "")
                    body = r.get("body", "")

                    if url in self.seen_urls:
                        continue

                    if not self._is_valid_linkedin_post(url, body):
                        continue

                    self.seen_urls.add(url)
                    count += 1
                    batch_hits += 1

                    yield {
                        "type": "raw_result",
                        "data": {
                            "title": r.get("title", "Unknown"),
                            "body": r.get("body", ""),
                            "url": url,
                        },
                    }

            yield {"type": "status", "data": f"Batch complete: +{batch_hits} leads (total: {count})"}

            # Stop early if we have enough
            if count >= limit:
                break

        yield {"type": "status", "data": f"Crawl complete. Found {count} qualified leads."}
