import os
import asyncio
import logging
import time
import re
from typing import List, Generator, Dict
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
    Handles searching using SerpAPI (Google) for reliable, production-grade results.
    Falls back to DuckDuckGo if SerpAPI fails.
    """

    def __init__(self):
        self.seen_urls = set()
        self.serpapi_key = os.getenv("SERPAPI_KEY")

    def get_queries_for_role(
        self, role: str, company_size: str = None, revenue: str = None, tech: str = None
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
        self, role: str, company_size: str = None, revenue: str = None, tech: str = None
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
        ]

        # Prioritize locations: India first, then Remote, then Global (no filter)
        priority_locations = ['"India"', '"Remote"', ""]
        all_queries = []

        for loc in priority_locations:
            for q in base_queries:
                combined_query = f"{q} {loc}".strip()
                all_queries.append(combined_query + filter_str)

        return all_queries

    async def crawl_stream(
        self,
        role: str,
        limit: int = 20,
        broad_mode: bool = False,
        company_size: str = None,
        revenue: str = None,
        tech: str = None,
    ) -> Generator[Dict, None, None]:
        """
        Async Generator: Yields raw search results using SerpAPI.
        """
        if broad_mode:
            queries = self.get_broad_queries(role, company_size, revenue, tech)
        else:
            queries = self.get_queries_for_role(role, company_size, revenue, tech)

        count = 0
        self.seen_urls = set()  # Reset per-request to avoid cross-search deduplication
        mode_text = "Broad Mode" if broad_mode else "Precision Mode"
        yield {"type": "status", "data": f"Starting {mode_text} search for '{role}'..."}

        for q in queries:
            if count >= limit:
                break

            yield {"type": "status", "data": f"Searching: {q[:50]}..."}
            await asyncio.sleep(0.1)  # Small delay between queries

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

                    results = await asyncio.to_thread(
                        _serpapi_search, q, self.serpapi_key
                    )
                    if results:
                        yield {
                            "type": "status",
                            "data": f"Found {len(results)} results via SerpAPI",
                        }
                except Exception as e:
                    logging.error(f"SerpAPI error: {e}", exc_info=True)
                    yield {"type": "status", "data": f"SerpAPI error: {str(e)[:50]}"}

            if not results:
                yield {"type": "status", "data": "Trying DuckDuckGo fallback..."}
                try:

                    def _ddg_search(query):
                        from ddgs import DDGS

                        try:
                            # 'w' = past week
                            return list(
                                DDGS().text(query, max_results=10, timelimit="w")
                            )
                        except Exception:
                            return []

                    ddg_results = await asyncio.to_thread(_ddg_search, q)
                    if ddg_results:
                        results = [
                            {
                                "title": r.get("title", ""),
                                "body": r.get("body", ""),
                                "href": r.get("href", ""),
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
                body = r.get("body", "")

                # Enforce strict LinkedIn-only domain filtering
                if (
                    not url
                    or url in self.seen_urls
                    or "linkedin.com" not in url.lower()
                ):
                    continue

                # Enforce strict 1-week time restriction parsing
                if not is_recent_post(url, body, max_days=7):
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
