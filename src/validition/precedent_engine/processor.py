#processor.py
from collections import Counter
import re


STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "was", "were", "are",
    "be", "been", "being", "have", "had", "has", "do", "did", "does",
    "will", "would", "could", "should", "may", "might", "its", "their",
    "they", "it", "this", "that", "which", "who", "how", "what",
    "when", "where", "due", "after", "before", "than", "more", "also",
    "not", "no", "as", "into", "through", "over", "then", "there",
    "source", "case", "study", "article", "according", "document",
    "mentioned", "described", "examined", "further", "pursued",
    "expanded", "company", "business", "stores", "operations"
}


def analyze(cases):
    total = len(cases)
    success = sum(1 for c in cases if c.get("outcome") == "Success")
    failure = sum(1 for c in cases if c.get("outcome") == "Failure")
    partial = sum(1 for c in cases if c.get("outcome") == "Partial")
    return total, success, failure, partial


def extract_bigrams(text: str):
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    words = [w for w in words if w not in STOPWORDS and len(w) > 3]
    return [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]


def clean_text(case: dict) -> str:
    reason = re.sub(r'Source\s*\d+', '', case.get("reason", ""), flags=re.IGNORECASE)
    reason = re.sub(r'\(.*?\)', '', reason)
    reason = re.sub(r'".*?"', '', reason)
    return f"{case.get('what_happened', '')} {reason}"


def extract_patterns(cases):
    success_cases = [c for c in cases if c.get("outcome") == "Success"]
    failure_cases = [c for c in cases if c.get("outcome") in ["Failure", "Partial"]]

    def top_patterns(case_list, top_n=5):
        if not case_list:
            return []
        all_bigrams = []
        for c in case_list:
            all_bigrams.extend(extract_bigrams(clean_text(c)))
        if not all_bigrams:
            all_words = []
            for c in case_list:
                words = re.findall(r'\b[a-zA-Z]+\b', clean_text(c).lower())
                all_words.extend([w for w in words if w not in STOPWORDS and len(w) > 5])
            return [w for w, _ in Counter(all_words).most_common(top_n)]
        return [p for p, _ in Counter(all_bigrams).most_common(top_n)]

    return {
        "worked": top_patterns(success_cases),
        "failed": top_patterns(failure_cases)
    }


def calculate_confidence(cases):
    if not cases:
        return 0

    scores = []
    for c in cases:
        if not isinstance(c, dict):
            continue
        outcome = c.get("outcome", "")
        reason = c.get("reason", "")
        company = c.get("company", "")
        if outcome not in ["Success", "Failure", "Partial"]:
            continue

        length_score = min(len(reason) / 150, 1.0)
        word_score = min(len(reason.split()) / 15, 1.0)
        source_penalty = min(
            len(re.findall(r'source|case study|article|document', reason, re.IGNORECASE)) * 0.2,
            0.6
        )
        company_bonus = 0.2 if company and len(company) > 1 else 0
        diversity_bonus = 0.1 if outcome in ["Failure", "Partial"] else 0

        score = (length_score * 0.35) + (word_score * 0.35) + company_bonus + diversity_bonus - source_penalty
        scores.append(max(0, min(score, 1.0)))

    if not scores:
        return 0

    outcomes = [c.get("outcome") for c in cases]
    diversity_bonus = 5 if len(set(outcomes)) > 1 else 0
    avg = (sum(scores) / len(scores)) * 100
    return round(min(avg + diversity_bonus, 100), 2)


def build_output(cases):
    total, success, failure, partial = analyze(cases)
    patterns = extract_patterns(cases)
    confidence = calculate_confidence(cases)

    level = "High" if confidence > 70 else "Medium" if confidence > 40 else "Low"

    success_factors = [c.get("reason", "") for c in cases if c.get("outcome") == "Success"]
    failure_factors = [c.get("reason", "") for c in cases if c.get("outcome") in ["Failure", "Partial"]]

    return {
        "precedent_summary": {
            "precedent_exists": total > 0,
            "cases_analyzed": total,
            "context_match_level": level,
            "confidence_score": confidence
        },
        "outcomes": {
            "success": success,
            "partial_success": partial,
            "failure": failure
        },
        "what_worked": patterns["worked"],
        "what_failed": patterns["failed"],
        "key_insights": {
            "success_factors": success_factors,
            "failure_factors": failure_factors
        },
        "cases": cases
    }