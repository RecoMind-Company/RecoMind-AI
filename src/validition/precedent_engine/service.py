# service.py
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from crewai import Crew
from precedent_engine.tasks import query_task, precedent_task
from precedent_engine.search_tool import (
    search_all, deduplicate, filter_and_rank,
    enrich_with_wikipedia, build_context
)
from precedent_engine.processor import build_output

MIN_CASES = 3

VAGUE_PHRASES = [
    "source does not", "not indicated", "not quantified", "no evidence",
    "outcome uncertain", "unclear", "not provided", "does not specify",
    "cannot determine", "not mentioned", "no information", "no data",
    "not clear", "hard to say", "difficult to determine", "insufficient information"
] 


# =========================
# SAFE JSON PARSER
# =========================

def safe_json_load(raw: str):
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        pass

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        cleaned = parts[1] if len(parts) > 1 else cleaned
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    fixed = re.sub(r',\s*}', '}', cleaned)
    fixed = re.sub(r',\s*]', ']', fixed)
    try:
        return json.loads(fixed)
    except Exception:
        pass

    match = re.search(r'\[.*\]', fixed, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    print("  ❌ JSON repair failed")
    return []


# =========================
# CASE VALIDATOR
# =========================

def validate_cases(cases) -> list:
    if not isinstance(cases, list):
        return []

    required_keys = {"company", "outcome", "reason", "what_happened"}
    valid = []

    for c in cases:
        if not isinstance(c, dict):
            continue
        if not required_keys.issubset(c.keys()):
            print(f"  ⚠️ Missing keys: {required_keys - c.keys()}")
            continue
        if any(not isinstance(c[k], str) for k in required_keys):
            print(f"  ⚠️ Non-string: {c.get('company', '?')}")
            continue
        if c["outcome"] not in ["Success", "Failure", "Partial"]:
            continue
        if len(c["what_happened"].strip()) < 10:
            continue
        if len(c["reason"].strip()) < 25:
            continue
        if any(p in c["reason"].lower() for p in VAGUE_PHRASES):
            print(f"  ⚠️ Vague skipped: {c['company']}")
            continue
        valid.append(c)

    return valid


# =========================
# CONCURRENT SEARCH + WIKI PIPELINE
# ✅ بيشغل الـ search والـ Wikipedia enrichment في نفس الوقت
# =========================

def _run_search_pipeline(queries: list) -> list:
    """
    Search + Wikipedia concurrent في نفس الـ try-catch
    """
    all_results = []

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            # بدأ الـ search
            search_future = executor.submit(search_all, queries)

            # في نفس الوقت بنجيب نتايج مبدئية للـ Wikipedia
            # (هنستخدمهم بعد الـ search)
            search_results = search_future.result()
            all_results.extend(search_results)

            # دلوقتي نعمل Wikipedia enrichment concurrent
            wiki_future = executor.submit(enrich_with_wikipedia, list(all_results))
            enriched = wiki_future.result()
            all_results = enriched

    except Exception as e:
        print(f"  ❌ Pipeline error: {e}")
        # fallback: sequential
        all_results = search_all(queries)
        all_results = enrich_with_wikipedia(all_results)

    all_results = deduplicate(all_results)
    all_results = filter_and_rank(all_results)
    return all_results


# =========================
# RETRY LOGIC
# =========================

def _needs_retry(valid_cases: list) -> tuple:
    count = len(valid_cases)
    has_success = any(c["outcome"] == "Success" for c in valid_cases)
    has_failure = any(c["outcome"] in ["Failure", "Partial"] for c in valid_cases)

    missing = []
    if not has_success:
        missing.append("success")
    if not has_failure:
        missing.append("failure")

    should_retry = (count < MIN_CASES) or bool(missing)
    return should_retry, missing


def _build_followup_queries(input_data: dict, missing: list) -> list:
    industry = input_data.get("company_context", {}).get("industry", "retail")
    action = input_data.get("primary_action", {}).get("action_type", "expansion")
    location = input_data.get("primary_action", {}).get("details", {}).get("location", "")

    queries = []
    if "success" in missing or not missing:
        queries += [
            f"{industry} {action} success case study site:hbr.org OR site:mckinsey.com",
            f"successful {industry} store opening profitable growth site:forbes.com",
            f"{industry} branch expansion wins growth story real example",
        ]
    if "failure" in missing or not missing:
        queries += [
            f"{industry} expansion failure lessons learned site:hbr.org OR site:reuters.com",
            f"{industry} store opening failed what went wrong closed site:bloomberg.com",
        ]
    if location:
        queries.append(f"{industry} expansion {location} success failure case study results")

    return queries[:5]


# =========================
# MAIN ENGINE
# =========================

def run_precedent_engine(input_data: dict) -> dict:

    # 1. Generate Queries
    print("\n🧠 Step 1: Generating queries...")
    crew1 = Crew(tasks=[query_task], verbose=False)
    q_result = crew1.kickoff(inputs={"input": input_data})

    queries = safe_json_load(q_result.raw)
    if not isinstance(queries, list) or not queries:
        return _empty_result()

    queries = [q for q in queries if isinstance(q, str) and len(q) > 5][:10]
    print(f"  ✅ {len(queries)} queries ready")

    # 2. Concurrent Search + Wikipedia
    print("\n🔍 Step 2: Concurrent search + Wikipedia...")
    results = _run_search_pipeline(queries)
    print(f"  ✅ {len(results)} ranked results")

    if not results:
        return _empty_result()

    context = build_context(results, top_n=10)

    # 3. Extract Round 1
    print("\n🤖 Step 3: Extracting cases (round 1)...")
    crew2 = Crew(tasks=[precedent_task], verbose=False)
    p_result = crew2.kickoff(inputs={"input": input_data, "context": context})
    print("\n🔎 Raw LLM output:", p_result.raw[:500])
    valid_cases = validate_cases(safe_json_load(p_result.raw))
    print(f"  ✅ {len(valid_cases)} valid cases")

    # 4. Retry if needed
    should_retry, missing = _needs_retry(valid_cases)

    if should_retry:
        reason_str = f"count={len(valid_cases)}/{MIN_CASES}"
        if missing:
            reason_str += f", missing={missing}"
        print(f"\n🔄 Step 4: Retry ({reason_str})...")

        followup = _build_followup_queries(input_data, missing)
        print(f"  → {len(followup)} follow-up queries")

        extra_results = _run_search_pipeline(followup)
        merged = deduplicate(results + extra_results)
        merged = filter_and_rank(merged)
        context2 = build_context(merged, top_n=12)

        crew3 = Crew(tasks=[precedent_task], verbose=False)
        p_result2 = crew3.kickoff(inputs={"input": input_data, "context": context2})

        extra_cases = validate_cases(safe_json_load(p_result2.raw))

        existing = {c["company"].lower() for c in valid_cases}
        for c in extra_cases:
            if c["company"].lower() not in existing:
                valid_cases.append(c)
                existing.add(c["company"].lower())

        print(f"  ✅ After retry: {len(valid_cases)} cases")

    print(f"\n🎯 Final: {len(valid_cases)} cases")
    return build_output(valid_cases)


def _empty_result() -> dict:
    return {
        "precedent_summary": {
            "precedent_exists": False,
            "cases_analyzed": 0,
            "context_match_level": "Low",
            "confidence_score": 0
        },
        "outcomes": {"success": 0, "partial_success": 0, "failure": 0},
        "strategic_verdict": {"what_worked": [], "what_failed": []},
        "cases": []
    }