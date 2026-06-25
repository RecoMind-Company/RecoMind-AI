from service import run_precedent_engine
import json

input_data = {
    "strategy_type": "Expansion",
    "decision_category": "Growth",
    "primary_action": {
        "action_type": "Open Branch",
        "details": {"location": "Cairo"}
    },
    "company_context": {
        "industry": "Retail",
        "size": "Medium",
        "location": "Egypt"
    }
}

result = run_precedent_engine(input_data)

print(json.dumps(result, indent=4))


