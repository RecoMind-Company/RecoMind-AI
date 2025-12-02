# test.py - System test for answering logic

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.answering_context_builder import create_crew_and_params
from shared.config import get_llm

TEST_QUERY = "How many orders were made in 2014?"

print("Initializing LLM...")
llm = get_llm()
print("LLM initialized successfully.")
print("-" * 70)

print(f"Query: {TEST_QUERY}")
print("-" * 70)

crew, source_settings = create_crew_and_params(
    user_query=TEST_QUERY,
    company_id="fb140d33-7e96-474d-a06d-ab3a6c65d1a9",
    team_name="Sales"
)

if not crew:
    print("Failed to create Crew - check database connection.")
    exit()

print("Crew ready. Starting execution...\n")

try:
    result = crew.kickoff()
    print("\nFinal Answer:")
    print("=" * 50)
    print(result)
    print("=" * 50)
except Exception as e:
    print("Error during execution:")
    print(e)
    import traceback
    traceback.print_exc()