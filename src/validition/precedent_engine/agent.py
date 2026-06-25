
from crewai import Agent
from llm_config import llm

# =========================
# QUERY AGENT (IMPROVED)
# =========================
query_agent = Agent(
    role="Search Query Generator",
    goal="Generate 5-8 precise business case study search queries",

    backstory=(
        "You generate highly targeted search queries for real business case studies. "
        "Focus only on real companies, real industries, and real events. "
        "Always include both success and failure cases. "
        "Avoid generic or vague queries. "
        "Return ONLY a valid JSON list of strings."
    ),

    llm=llm,
    allow_delegation=False,
    temperature=0
)

# =========================
# PRECEDENT AGENT (CRITICAL FIX)
# =========================
precedent_agent = Agent(
    role="Business Case Extractor",
    goal="Extract real, evidence-based business cases from provided search results",

    backstory=(
        "You extract factual business cases from provided search snippets. "
        "A case is valid if the snippet mentions a real company name AND describes "
        "what happened AND gives a reason or outcome — even if partial. "
        "You ARE allowed to infer outcome from language: "
        "words like 'failed', 'closed', 'losses' → Failure. "
        "Words like 'growth', 'profitable', 'expanded successfully' → Success. "
        "If a snippet gives partial evidence, classify as Partial. "
        "Never invent facts. Never add numbers not in the text. "
        "Return strict JSON array only."
    ),

    llm=llm,
    allow_delegation=False,
    temperature=0
)