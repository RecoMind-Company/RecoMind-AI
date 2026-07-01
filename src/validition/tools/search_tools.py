"""
Search Tools
=============
Shared async web search tools (Serper, DuckDuckGo, Wikipedia)
with scoring, ranking, and context building.
Used by both the Precedent Engine and the Market Trend Engine.
"""

import asyncio
import re
from typing import Any, Dict, List

import httpx
from loguru import logger

from core.config import settings


BLOCKED_DOMAINS = [
    "facebook.com", "linkedin.com", "instagram.com", "twitter.com",
    "reddit.com", "quora.com", "pinterest.com", "tiktok.com", "youtube.com",
]

HIGH_AUTHORITY_DOMAINS = [
    "hbr.org", "mckinsey.com", "bain.com", "bcg.com", "forbes.com",
    "reuters.com", "bloomberg.com", "ft.com", "economist.com",
    "businessinsider.com", "harvard.edu", "wharton.upenn.edu", "wsj.com",
]

WIKI_HEADERS = {
    "User-Agent": "RecoMindAI/1.0 (business-research-tool; contact@recomind.ai)",
    "Accept": "application/json",
}


class SearchTools:
    """Shared async web search tools with scoring and ranking."""

    def __init__(self):
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    async def search_all(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Execute all queries concurrently and return aggregated results."""
        cache_key = "|".join(sorted(queries))
        if cache_key in self._cache:
            logger.debug("Using cached search results")
            return self._cache[cache_key]

        tasks = [self._run_query(q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_results: List[Dict[str, Any]] = []
        for i, r in enumerate(results):
            if isinstance(r, list):
                all_results.extend(r)
                logger.debug(f"Query completed: {queries[i][:55]}")
            elif isinstance(r, Exception):
                logger.warning(f"Query failed: {queries[i][:55]} -> {r}")

        self._cache[cache_key] = all_results
        return all_results

    async def enrich_with_wikipedia(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich results with Wikipedia summaries for extracted company names."""
        company_names = self._extract_company_names(results)
        if not company_names:
            return results

        logger.info(f"Wikipedia lookup for: {company_names}")

        tasks = [self._wikipedia_search(name) for name in company_names]
        wiki_results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in wiki_results:
            if isinstance(r, dict) and r:
                results.append(r)

        return results

    @staticmethod
    def deduplicate(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results by URL."""
        seen = set()
        unique = []
        for r in results:
            link = r.get("link", "")
            if link and link not in seen:
                seen.add(link)
                unique.append(r)
        return unique

    @staticmethod
    def filter_and_rank(results: List[Dict[str, Any]], high_value_keywords: List[str] = None) -> List[Dict[str, Any]]:
        """Score, filter, and rank results by relevance."""
        hv = high_value_keywords or []
        scored = [(SearchTools._score_result(r, hv), r) for r in results]
        scored = [(s, r) for s, r in scored if s > -999]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored]

    @staticmethod
    def build_context(results: List[Dict[str, Any]], top_n: int = 10) -> str:
        """Build a text context from ranked search results for LLM input."""
        authority = [
            r for r in results
            if any(d in r.get("link", "") for d in HIGH_AUTHORITY_DOMAINS)
        ][:3]
        web = [
            r for r in results
            if r.get("source_tool") in ("serper", "duckduckgo") and r not in authority
        ][:3]
        news = [r for r in results if r.get("source_tool") == "serper_news"][:2]
        wiki = [r for r in results if r.get("source_tool") == "wikipedia"][:2]

        ordered = authority + web + news + wiki
        remaining = [r for r in results if r not in ordered]
        ordered = (ordered + remaining)[:top_n]

        texts = []
        for i, r in enumerate(ordered):
            label = {
                "serper": "WEB", "duckduckgo": "WEB",
                "serper_news": "NEWS", "wikipedia": "WIKIPEDIA",
            }.get(r.get("source_tool", ""), "WEB")

            if any(d in r.get("link", "") for d in HIGH_AUTHORITY_DOMAINS):
                label = "AUTHORITY"

            block = (
                f"--- SOURCE {i + 1} [{label}] ---\n"
                f"Title: {r.get('title', '')}\n"
                f"Summary: {r.get('snippet', '')}\n"
                f"URL: {r.get('link', '')}\n"
            )
            texts.append(block)

        return "\n".join(texts)[:7000]

    # ===========================================
    # Internal: Query Execution
    # ===========================================

    async def _run_query(self, query: str) -> List[Dict[str, Any]]:
        """Run a single query across relevant search sources."""
        results: List[Dict[str, Any]] = []
        results.extend(await self._serper_search(query))

        q_lower = query.lower()
        if any(w in q_lower for w in ["success", "profitable", "trend", "growth", "market"]):
            results.extend(await self._duckduckgo_search(query))
        if any(w in q_lower for w in ["fail", "wrong", "lesson", "mistake", "exit", "decline", "news"]):
            results.extend(await self._serper_news_search(query))

        return results

    # ===========================================
    # Internal: Search Providers
    # ===========================================

    async def _serper_search(self, query: str, num: int = 5) -> List[Dict[str, Any]]:
        if not settings.SERPER_API_KEY:
            return []
        try:
            async with httpx.AsyncClient(timeout=settings.SEARCH_TIMEOUT) as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": settings.SERPER_API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={"q": query, "num": num, "gl": "us", "hl": "en"},
                )
                response.raise_for_status()
                return [
                    {
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "link": item.get("link", ""),
                        "source_tool": "serper",
                    }
                    for item in response.json().get("organic", [])
                ]
        except Exception as e:
            logger.warning(f"Serper search error: {e}")
            return []

    async def _serper_news_search(self, query: str, num: int = 3) -> List[Dict[str, Any]]:
        if not settings.SERPER_API_KEY:
            return []
        try:
            async with httpx.AsyncClient(timeout=settings.SEARCH_TIMEOUT) as client:
                response = await client.post(
                    "https://google.serper.dev/news",
                    headers={
                        "X-API-KEY": settings.SERPER_API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={"q": query, "num": num, "gl": "us", "hl": "en"},
                )
                response.raise_for_status()
                return [
                    {
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "link": item.get("link", ""),
                        "source_tool": "serper_news",
                    }
                    for item in response.json().get("news", [])
                ]
        except Exception as e:
            logger.warning(f"Serper news search error: {e}")
            return []

    async def _duckduckgo_search(self, query: str, num: int = 3) -> List[Dict[str, Any]]:
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            async with httpx.AsyncClient(timeout=settings.SEARCH_TIMEOUT) as client:
                resp = await client.get(
                    "https://duckduckgo.com/html/", params={"q": query}, headers=headers
                )

            titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
            snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</span>', resp.text, re.DOTALL)
            links = re.findall(r'<a rel="nofollow" class="result__a" href="(.*?)"', resp.text)

            results = []
            for i in range(min(num, len(links))):
                title = re.sub(r"<[^>]+>", "", titles[i]).strip() if i < len(titles) else ""
                snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else ""
                if not title and not snippet:
                    continue
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "link": links[i],
                    "source_tool": "duckduckgo",
                })
            return results
        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}")
            return []

    async def _wikipedia_search(self, topic: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=settings.SEARCH_TIMEOUT) as client:
                search_resp = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query", "list": "search",
                        "srsearch": topic, "format": "json", "srlimit": 2,
                    },
                    headers=WIKI_HEADERS,
                )
                search_resp.raise_for_status()
                hits = search_resp.json().get("query", {}).get("search", [])
                if not hits:
                    return {}

                page_title = hits[0]["title"]
                summary_resp = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query", "prop": "extracts",
                        "exintro": True, "explaintext": True,
                        "titles": page_title, "format": "json",
                    },
                    headers=WIKI_HEADERS,
                )
                summary_resp.raise_for_status()
                pages = summary_resp.json().get("query", {}).get("pages", {})
                page = next(iter(pages.values()))
                extract = page.get("extract", "")[:900].strip()
                if not extract or len(extract) < 50:
                    return {}
                return {
                    "title": page_title,
                    "snippet": extract,
                    "link": f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}",
                    "source_tool": "wikipedia",
                }
        except Exception as e:
            logger.warning(f"Wikipedia search error for '{topic}': {e}")
            return {}

    # ===========================================
    # Internal: Scoring and Utilities
    # ===========================================

    @staticmethod
    def _score_result(result: Dict[str, Any], high_value_keywords: List[str]) -> int:
        score = 0
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        link = result.get("link", "").lower()

        if any(domain in link for domain in BLOCKED_DOMAINS):
            return -999
        if len(result.get("snippet", "")) < 50:
            score -= 2
        if any(domain in link for domain in HIGH_AUTHORITY_DOMAINS):
            score += 10
        if result.get("source_tool") == "wikipedia":
            score += 4
        if result.get("source_tool") == "serper_news":
            score += 2

        for kw in high_value_keywords:
            if kw in title:
                score += 3
            if kw in snippet:
                score += 2

        if len(snippet) > 200:
            score += 1

        return score

    @staticmethod
    def _extract_company_names(results: List[Dict[str, Any]]) -> List[str]:
        SKIP_WORDS = {
            "The", "How", "Why", "When", "What", "Case", "Study", "Business",
            "Company", "Market", "Egypt", "Cairo", "Africa", "Middle", "East",
            "Global", "Local", "New", "Old", "Top", "Best", "Worst", "Lessons",
            "More", "Multi", "Source", "Retail", "Store", "Branch", "Success",
            "Failure", "Strategy", "Growth", "Opening", "Expansion", "Physical",
            "Digital", "Online", "Offline", "International", "Analysis",
        }
        patterns = [
            r'(?:case study of|success of|failure of|expansion of|collapse of)\s+([A-Z][a-zA-Z&]{2,15})',
            r'\b([A-Z]{2,8})\s+(?:expansion|strategy|case|failure|success|retail|exit)',
            r'\b([A-Z][a-zA-Z]{3,12})\s+(?:Egypt|Canada|Germany|France|UK|USA|market)',
        ]
        company_names = set()
        for r in results:
            title = r.get("title", "")
            for pattern in patterns:
                for match in re.findall(pattern, title):
                    name = match.strip()
                    if name and name not in SKIP_WORDS and 3 <= len(name) <= 15:
                        company_names.add(name)
        return sorted(list(company_names))[:5]


# Singleton instance
search_tools = SearchTools()
