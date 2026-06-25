from crewai import Task
from precedent_engine.agent import query_agent, precedent_agent


# =========================
# Query Task — مع Search Operators
# =========================

query_task = Task(
    description=(
        "INPUT:\n{input}\n\n"

        "Generate exactly 10 HIGH-QUALITY search queries for real business case studies.\n\n"

        "REQUIRED DISTRIBUTION:\n"
        "- Queries 1-3: GLOBAL success stories\n"
        "  At least 2 must use site operators for authority sources:\n"
        "  e.g. 'retail branch expansion success case study site:hbr.org OR site:mckinsey.com'\n"
        "  e.g. 'physical store expansion profitable growth site:forbes.com OR site:bloomberg.com'\n"
        "- Queries 4-6: FAILURE / MISTAKE stories\n"
        "  At least 2 must use site operators:\n"
        "  e.g. 'retail expansion failure lessons learned site:hbr.org OR site:reuters.com'\n"
        "  e.g. 'store expansion strategic pitfalls what went wrong site:forbes.com'\n"
        "- Queries 7-8: EMERGING MARKETS / REGIONAL (Egypt / Middle East / Africa)\n"
        "  e.g. 'retail expansion Egypt Cairo branch opening results case study'\n"
        "  e.g. 'retail chain Middle East expansion failure lessons'\n"
        "- Queries 9-10: INDUSTRY-SPECIFIC LESSONS\n"
        "  e.g. 'retail physical store expansion lessons learned strategic pitfalls'\n"
        "  e.g. 'opening new branch emerging market challenges overcome'\n\n"

        "STRICT RULES:\n"
        "- Extract industry and action from the input and use them in every query\n"
        "- Each query must be 5-12 words\n"
        "- No vague queries like 'business expansion' or 'company growth'\n"
        "- Queries must target actionable, evidence-based content\n\n"

        "Return ONLY a raw JSON array of 10 strings.\n"
        "No markdown. No explanation. No trailing commas.\n"
        "Example: [\"query one\", \"query two\"]"
    ),
    expected_output="Raw JSON array of 10 targeted search query strings",
    agent=query_agent
)


# =========================
# Precedent Task — مع Chain of Thought + Cross-reference + Industry filter
# =========================
precedent_task = Task(
    description=(
        "INPUT (strategy being evaluated):\n{input}\n\n"
        "CONTEXT (search results — your ONLY source):\n{context}\n\n"

        "STEP 1 — IDENTIFY TARGET:\n"
        "From the input, extract: Industry and Action Type.\n"
        "Focus on cases related to this combination.\n"
        "Accept cases from adjacent industries if the action type matches.\n\n"

        "STEP 2 — EXTRACT CASES:\n"
        "For each SOURCE block in the context:\n"
        "- Read the Title and Summary carefully.\n"
        "- If a real company name appears AND an action is described → extract it.\n"
        "- Outcome: use the 'Predicted Outcome' field from the source block as a hint.\n"
        "- If outcome words exist (failed/closed/losses/exit → Failure, "
        "growth/profitable/expanded/success → Success, mixed → Partial) → use them.\n"
        "- what_happened: 1 sentence describing the specific action taken.\n"
        "- reason: 1-2 sentences explaining WHY it succeeded or failed.\n\n"

        "STEP 3 — QUALITY CHECK:\n"
        "Keep a case if ALL of these are true:\n"
        "✅ Company name is real and specific (not 'a company' or 'a retailer')\n"
        "✅ what_happened is at least 10 characters\n"
        "✅ reason is at least 20 characters\n"
        "✅ outcome is exactly 'Success', 'Failure', or 'Partial'\n\n"

        "REJECT only if:\n"
        "❌ No company name at all\n"
        "❌ reason is purely 'source does not mention' or 'unclear'\n\n"

        "DIVERSITY RULE:\n"
        "Try to return at least 1 Success and 1 Failure if context allows.\n"
        "Return minimum 3 cases if possible.\n\n"

        "OUTPUT:\n"
        "Return ONLY a raw JSON array. No markdown. No explanation.\n"
        "If truly nothing found → return []\n\n"

        "[{\"company\": \"Target\", \"outcome\": \"Failure\", "
        "\"what_happened\": \"Entered Canadian market opening 133 stores in 18 months\", "
        "\"reason\": \"Rushed timeline caused chronic stockouts and $2B in losses\"}]"
    ),
    expected_output="Raw JSON array of business cases",
    agent=precedent_agent
)