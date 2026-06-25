# pipeline.py
import json
import sys
import os
from pathlib import Path

# ── Fix imports من الـ root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Import الجزء الأول (structuring)
from task import crew
from schemas import StrategyOutput
from pydantic import ValidationError

# ── Import الجزء التاني (precedent_engine)
from precedent_engine.service import run_precedent_engine


def run_full_pipeline(user_plan: str) -> dict:

    print("\n🔷 STEP 1: Strategy Structuring...")
    result = crew.kickoff(inputs={"user_plan": user_plan})

    try:
        structured = StrategyOutput.model_validate_json(result.raw)
        data = structured.model_dump()
    except ValidationError as e:
        print(f"❌ Structuring failed: {e}")
        return {}

    Path("agent_outputs/precedent").mkdir(parents=True, exist_ok=True)
    Path("agent_outputs/resource").mkdir(parents=True, exist_ok=True)
    Path("agent_outputs/market").mkdir(parents=True, exist_ok=True)

    precedent_data = data["precedent_engine_input"]
    resource_data  = data["resource_simulator_input"]
    market_data    = data["market_trend_engine_input"]

    with open("agent_outputs/precedent/input.json", "w") as f:
        json.dump(precedent_data, f, indent=4, ensure_ascii=False)

    with open("agent_outputs/resource/input.json", "w") as f:
        json.dump(resource_data, f, indent=4, ensure_ascii=False)

    with open("agent_outputs/market/input.json", "w") as f:
        json.dump(market_data, f, indent=4, ensure_ascii=False)

    print("✅ agent_outputs saved")

    # ── STEP 2: Precedent Engine
    print("\n🔷 STEP 2: Precedent Engine...")

    precedent_input = {
        "strategy_type":     precedent_data["strategy_type"],
        "decision_category": precedent_data["decision_category"],
        "primary_action":    precedent_data["primary_action"],
        "company_context": {
            "industry": "Retail",
            "size":     "Medium",
            "location": precedent_data["primary_action"]["details"].get("location", "")
        }
    }

    precedent_result = run_precedent_engine(precedent_input)

    with open("agent_outputs/precedent/output.json", "w") as f:
        json.dump(precedent_result, f, indent=4, ensure_ascii=False)

    print("✅ Precedent Engine done")

    return {
        "structured_plan":  data,
        "precedent_result": precedent_result
    }


if __name__ == "__main__":
    user_plan = "We want to open a new physical branch in Cairo for our retail business and hire a sales team."
    result = run_full_pipeline(user_plan)

    if result:
        print("\n📊 PRECEDENT RESULT:")
        print(json.dumps(result["precedent_result"], indent=4, ensure_ascii=False))