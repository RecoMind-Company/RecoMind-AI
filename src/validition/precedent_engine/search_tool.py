# search_tool.py
import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

# =========================
# SEARCH CACHE
# =========================

SEARCH_CACHE = {}

# =========================
# CONFIG
# =========================

HIGH_VALUE_KEYWORDS = [
    "case study",
    "business case",
    "expansion strategy",
    "branch opening",
    "market entry",
    "retail expansion",
    "company failed",
    "business failure",
    "lessons learned",
    "what went wrong",
    "success story",
    "growth strategy",
    "opened stores",
    "store network",
    "physical retail",
    "strategic pitfalls",
    "market exit",
    "profitable expansion"
]

MEDIUM_VALUE_KEYWORDS = [
    "business",
    "company",
    "startup",
    "retail",
    "expansion",
    "strategy",
    "revenue",
    "growth",
    "market",
    "competition",
    "launch",
    "branch"
]

BLOCKED_DOMAINS = [
    "facebook.com",
    "linkedin.com",
    "instagram.com",
    "twitter.com",
    "reddit.com",
    "quora.com",
    "pinterest.com",
    "tiktok.com",
    "youtube.com"
]

HIGH_AUTHORITY_DOMAINS = [
    "hbr.org",
    "mckinsey.com",
    "bain.com",
    "bcg.com",
    "forbes.com",
    "reuters.com",
    "bloomberg.com",
    "ft.com",
    "economist.com",
    "businessinsider.com",
    "harvard.edu",
    "wharton.upenn.edu",
    "wsj.com"
]

SKIP_WORDS = {
    "The",
    "How",
    "Why",
    "When",
    "What",
    "Case",
    "Study",
    "Business",
    "Company",
    "Market",
    "Egypt",
    "Cairo",
    "Africa",
    "Middle",
    "East",
    "Global",
    "Local",
    "New",
    "Old",
    "Top",
    "Best",
    "Worst",
    "Lessons",
    "More",
    "Multi",
    "Canada",
    "Asia",
    "Europe",
    "America",
    "Source",
    "Retail",
    "Store",
    "Branch",
    "Success",
    "Failure",
    "Strategy",
    "Spatial",
    "Egyptian",
    "Breakingviews",
    "Person",
    "International",
    "Analysis",
    "Report",
    "Review",
    "Inside",
    "Behind",
    "Growth",
    "Opening",
    "Expansion",
    "Physical",
    "Digital",
    "Online",
    "Offline"
}

# =========================
# WIKIPEDIA HEADERS
# =========================

WIKI_HEADERS = {
    "User-Agent": "RecoMindAI/1.0 (business-research-tool; contact@recomind.ai)",
    "Accept": "application/json"
}

# =========================
# OUTCOME DETECTION
# =========================

FAILURE_PATTERNS = [
    "loss",
    "losses",
    "failed",
    "failure",
    "bankruptcy",
    "market exit",
    "closed",
    "shutdown",
    "decline",
    "stockouts"
]

SUCCESS_PATTERNS = [
    "growth",
    "profitable",
    "profitability",
    "success",
    "successful",
    "expanded",
    "market leader",
    "revenue increase",
    "scaling",
    "strong demand"
]


def detect_outcome(text: str):

    text = text.lower()

    for word in FAILURE_PATTERNS:
        if word in text:
            return "Failure"

    for word in SUCCESS_PATTERNS:
        if word in text:
            return "Success"

    return "Partial"

# =========================
# DETERMINISTIC QUERY BUILDER
# =========================


def build_queries(input_data: dict) -> list:

    company = input_data.get("company_context", {})
    action = input_data.get("primary_action", {})

    industry = company.get("industry", "retail")
    action_type = action.get("action_type", "expansion")

    location = action.get("details", {}).get("location", "")

    queries = [
        f"{industry} {action_type} success case study site:hbr.org",
        f"{industry} {action_type} failure lessons site:reuters.com",
        f"{industry} expansion profitable growth Forbes",
        f"{industry} failed expansion what went wrong",
        f"{industry} branch expansion Bloomberg case study",
        f"{industry} market entry success story",
        f"{industry} store expansion failure",
        f"{industry} scaling operational issues",
    ]

    if location:
        queries.append(
            f"{industry} {location} expansion success failure"
        )

    return queries[:10]

# =========================
# TOOL 1: SERPER WEB
# =========================


def serper_search(query: str, num: int = 6) -> List[Dict]:

    api_key = os.getenv("SERPER_API_KEY")

    if not api_key:
        print("  ❌ Missing SERPER_API_KEY")
        return []

    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            },
            json={
                "q": query,
                "num": num,
                "gl": "us",
                "hl": "en"
            },
            timeout=10
        )

        response.raise_for_status()

        results = []

        for item in response.json().get("organic", []):

            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", ""),
                "source_tool": "serper"
            })

        return results

    except Exception as e:
        print(f"  ❌ Serper error: {e}")
        return []

# =========================
# TOOL 2: SERPER NEWS
# =========================


def serper_news_search(query: str, num: int = 4) -> List[Dict]:

    api_key = os.getenv("SERPER_API_KEY")

    if not api_key:
        return []

    try:
        response = requests.post(
            "https://google.serper.dev/news",
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            },
            json={
                "q": query,
                "num": num,
                "gl": "us",
                "hl": "en"
            },
            timeout=10
        )

        response.raise_for_status()

        results = []

        for item in response.json().get("news", []):

            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", ""),
                "source_tool": "serper_news"
            })

        return results

    except Exception as e:
        print(f"  ❌ Serper News error: {e}")
        return []

# =========================
# TOOL 3: DUCKDUCKGO
# =========================


def duckduckgo_search(query: str, num: int = 5) -> List[Dict]:

    try:

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        resp = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": query},
            headers=headers,
            timeout=10
        )

        titles = re.findall(
            r'class="result__a"[^>]*>(.*?)</a>',
            resp.text,
            re.DOTALL
        )

        snippets = re.findall(
            r'class="result__snippet"[^>]*>(.*?)</span>',
            resp.text,
            re.DOTALL
        )

        links = re.findall(
            r'<a rel="nofollow" class="result__a" href="(.*?)"',
            resp.text
        )

        results = []

        for i in range(min(num, len(links))):

            title = re.sub(
                r'<[^>]+>',
                '',
                titles[i]
            ).strip() if i < len(titles) else ""

            snippet = re.sub(
                r'<[^>]+>',
                '',
                snippets[i]
            ).strip() if i < len(snippets) else ""

            if not title and not snippet:
                continue

            results.append({
                "title": title,
                "snippet": snippet,
                "link": links[i],
                "source_tool": "duckduckgo"
            })

        return results

    except Exception as e:
        print(f"  ❌ DuckDuckGo error: {e}")
        return []

# =========================
# TOOL 4: WIKIPEDIA
# =========================


def extract_company_names(results: List[Dict]) -> List[str]:

    patterns = [
        r'(?:case study of|success of|failure of|expansion of|collapse of)\s+([A-Z][a-zA-Z&]{2,15})',
        r'\b([A-Z]{2,8})\s+(?:expansion|strategy|case|failure|success|retail|exit)',
        r'\b([A-Z][a-zA-Z]{3,12})\s+(?:Egypt|Canada|Germany|France|UK|USA|market)',
    ]

    company_names = set()

    for r in results:

        title = r.get("title", "")

        for pattern in patterns:

            matches = re.findall(pattern, title)

            for match in matches:

                name = match.strip()

                if (
                    name
                    and name not in SKIP_WORDS
                    and 3 <= len(name) <= 15
                ):
                    company_names.add(name)

    return sorted(list(company_names))[:5]


def wikipedia_search(topic: str) -> Dict:

    try:

        search_resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": topic,
                "format": "json",
                "srlimit": 2
            },
            headers=WIKI_HEADERS,
            timeout=8
        )

        search_resp.raise_for_status()

        hits = search_resp.json().get("query", {}).get("search", [])

        if not hits:
            return {}

        page_title = hits[0]["title"]

        summary_resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "titles": page_title,
                "format": "json"
            },
            headers=WIKI_HEADERS,
            timeout=8
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
            "source_tool": "wikipedia"
        }

    except Exception as e:
        print(f"  ❌ Wikipedia error for '{topic}': {e}")
        return {}

# =========================
# CONCURRENT SEARCH
# =========================


def search_all_concurrent(queries: List[str]) -> List[Dict]:

    cache_key = "|".join(sorted(queries))

    if cache_key in SEARCH_CACHE:
        print("  ⚡ Using cached results")
        return SEARCH_CACHE[cache_key]

    all_results = []

    def run_query(q):

        results = []

        results.extend(serper_search(q, num=5))

        if any(
            w in q.lower()
            for w in [
                "success",
                "profitable",
                "hbr",
                "mckinsey"
            ]
        ):
            results.extend(duckduckgo_search(q, num=3))

        if any(
            w in q.lower()
            for w in [
                "fail",
                "wrong",
                "lesson",
                "mistake",
                "exit",
                "pitfall"
            ]
        ):
            results.extend(serper_news_search(q, num=3))

        return results

    with ThreadPoolExecutor(max_workers=4) as executor:

        futures = {
            executor.submit(run_query, q): q
            for q in queries
        }

        for future in as_completed(futures):

            q = futures[future]

            try:
                results = future.result()

                all_results.extend(results)

                print(f"  ✅ Done: {q[:55]}")

            except Exception as e:
                print(f"  ❌ Failed: {q[:55]} → {e}")

    SEARCH_CACHE[cache_key] = all_results

    return all_results


def enrich_with_wikipedia_concurrent(results: List[Dict]) -> List[Dict]:

    company_names = extract_company_names(results)

    if not company_names:
        return results

    print(f"  📚 Wikipedia lookup: {company_names}")

    with ThreadPoolExecutor(max_workers=3) as executor:

        futures = {
            executor.submit(wikipedia_search, name): name
            for name in company_names
        }

        for future in as_completed(futures):

            name = futures[future]

            try:
                result = future.result()

                if result:
                    results.append(result)

            except Exception as e:
                print(f"  ❌ Wiki failed for '{name}': {e}")

    return results

# =========================
# BACKWARD COMPAT
# =========================


def search_all(queries: List[str]) -> List[Dict]:
    return search_all_concurrent(queries)


def enrich_with_wikipedia(results: List[Dict]) -> List[Dict]:
    return enrich_with_wikipedia_concurrent(results)

# =========================
# SCORING
# =========================


def score_result(result: Dict) -> int:

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

    for kw in HIGH_VALUE_KEYWORDS:

        if kw in title:
            score += 3

        if kw in snippet:
            score += 2

    for kw in MEDIUM_VALUE_KEYWORDS:

        if kw in title:
            score += 1

        if kw in snippet:
            score += 1

    if len(snippet) > 200:
        score += 1

    return score

# =========================
# DEDUPLICATION
# =========================


def deduplicate(results: List[Dict]) -> List[Dict]:

    seen = set()
    unique = []

    for r in results:

        link = r.get("link", "")

        if link and link not in seen:

            seen.add(link)
            unique.append(r)

    return unique

# =========================
# FILTER + RANK
# =========================


def filter_and_rank(results: List[Dict]) -> List[Dict]:

    scored = [(score_result(r), r) for r in results]

    scored = [(s, r) for s, r in scored if s > -999]

    scored.sort(key=lambda x: x[0], reverse=True)

    return [r for _, r in scored]

# =========================
# BUILD CONTEXT
# =========================


def build_context(results: List[Dict], top_n: int = 10) -> str:

    authority = [
        r for r in results
        if any(
            d in r.get("link", "")
            for d in HIGH_AUTHORITY_DOMAINS
        )
    ][:3]

    web = [
        r for r in results
        if r.get("source_tool") in ("serper", "duckduckgo")
        and r not in authority
    ][:3]

    news = [
        r for r in results
        if r.get("source_tool") == "serper_news"
    ][:2]

    wiki = [
        r for r in results
        if r.get("source_tool") == "wikipedia"
    ][:2]

    ordered = authority + web + news + wiki

    remaining = [
        r for r in results
        if r not in ordered
    ]

    ordered = (ordered + remaining)[:top_n]

    texts = []

    for i, r in enumerate(ordered):

        label = {
            "serper": "WEB",
            "duckduckgo": "WEB",
            "serper_news": "NEWS",
            "wikipedia": "WIKIPEDIA"
        }.get(r.get("source_tool", ""), "WEB")

        if any(
            d in r.get("link", "")
            for d in HIGH_AUTHORITY_DOMAINS
        ):
            label = "AUTHORITY"

        block = (
            f"--- SOURCE {i+1} [{label}] ---\n"
            f"Title: {r.get('title', '')}\n"
            f"Predicted Outcome: {detect_outcome(r.get('snippet', ''))}\n"
            f"Summary: {r.get('snippet', '')}\n"
            f"URL: {r.get('link', '')}\n"
        )

        texts.append(block)

    return "\n".join(texts)[:7000]