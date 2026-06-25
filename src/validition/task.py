#task.py
from crewai import Task, Crew
from agents import strategy_structuring_agent
from schemas import StrategyOutput   
import json
from pydantic import ValidationError


# =========================
# 1️⃣ Task Definition
# =========================

structuring_task = Task(
    description=(
        "RAW INPUT:\n"
        "{user_plan}\n\n"

        "You are a deterministic strategy structuring engine.\n\n"

        "Your job:\n"
        "1) Read the raw input text.\n"
        "2) Extract all actions and intentions.\n"
        "3) Fill the schema fields using semantic understanding.\n\n"

        "SCHEMA FIELD DEFINITIONS:\n\n"

        "precedent_engine_input:\n"
        "  - strategy_type: The high-level category of the overall strategy.\n"
        "  - decision_category: The business outcome this strategy targets.\n"
        "  - primary_action.action_type: A short normalized label for the main action.\n"
        "  - primary_action.details.location: Physical location if mentioned.\n"
        "  - primary_action.details.channel: Communication or distribution channel if mentioned.\n\n"

        "resource_simulator_input:\n"
        "  - all_actions: Every action found in the input as a normalized label.\n"
        "  - resource_requirements.financial: Costs logically required by these actions.\n"
        "  - resource_requirements.human: Roles logically required by these actions.\n"
        "  - resource_requirements.operational: Assets or processes logically required.\n"
        "  - time_horizon: Estimated execution timeframe based on scope.\n\n"

        "market_trend_engine_input:\n"
        "  - strategy_type: Same as above.\n"
        "  - target_market.location: Geographic market if mentioned.\n\n"

        "RULES:\n"
        "- Infer only what the text logically implies.\n"
        "- Do NOT invent numbers or statistics.\n"
        "- action_type must be Title Case with spaces, not snake_case.\n"
        "- time_horizon must be qualitative only: Short Term / Medium Term / Long Term / Short to Medium Term.\n"
        "- all_actions details must not be null if the same action appears in primary_action.\n"
        "- Return ONLY valid JSON. No explanation."
    ),
    expected_output="Strict structured JSON",
    agent=strategy_structuring_agent,
    output_json=StrategyOutput
)

# =========================
# 2️⃣ Crew Setup
# =========================

crew = Crew(
    agents=[strategy_structuring_agent],
    tasks=[structuring_task],
    verbose=False
)

# =========================
# 3️⃣ Run
# =========================

raw_input = "We want to open a new physical branch in Cairo for our retail business and hire a sales team."

result = crew.kickoff(inputs={"user_plan": raw_input})

print("\n--- Final Structured Output ---")

# =========================
# 4️⃣ Validation Layer
# =========================

try:
    structured = StrategyOutput.model_validate_json(result.raw)
    print(json.dumps(structured.model_dump(), indent=4, ensure_ascii=False))
    import os
    data = structured.model_dump()


    os.makedirs("agent_outputs/precedent", exist_ok=True)
    os.makedirs("agent_outputs/resource", exist_ok=True)
    os.makedirs("agent_outputs/market", exist_ok=True)
 
    precedent_data = data["precedent_engine_input"]
    resource_data = data["resource_simulator_input"]
    market_data = data["market_trend_engine_input"]


    with open("agent_outputs/precedent/input.json", "w") as f:
        json.dump(precedent_data, f, indent=4, ensure_ascii=False)

    with open("agent_outputs/resource/input.json", "w") as f:
       json.dump(resource_data, f, indent=4, ensure_ascii=False)

    with open("agent_outputs/market/input.json", "w") as f:
       json.dump(market_data, f, indent=4, ensure_ascii=False)

    print("\n✅ Agent files created successfully!")
except ValidationError as e:
    print("❌ Schema validation failed:")
    print(e)
    print("\nRaw Output:\n")
    print(result.raw)





    
