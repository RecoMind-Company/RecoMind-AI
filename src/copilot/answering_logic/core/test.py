# test.py - Agent-by-Agent Testing
# Run each agent individually to debug and optimize

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crewai import Crew, Process, Task
from shared.config import get_llm
from core.answering_agents import (
    intent_understanding_agent, 
    access_control_filter_agent,
    table_column_detection_agent,
    sql_generator_agent
)
from core.answering_tasks import (
    IntentOutput, RBACOutput, SchemaMappingOutput, SQLQueryOutput,
    create_intent_task, get_date_context, create_rbac_task
)
from core.answering_tools import GetAllowedTablesTool, VectorDBTableSearchTool, GetAvailableColumnsTool

# ============================================================
# TEST CONFIGURATION
# ============================================================
TEST_QUERIES = [
    "What is the total revenue in 2023?",
    "How many orders were made in Cairo?",
    "Show me all products in Electronics category",
    "What is the average sales per customer?",
    "عايز اعرف اجمالي المبيعات في 2024",  # Arabic test
    "List all customers from Riyadh",
    "Count the number of products sold last month",
]

# Set to None to test ALL queries, or set index to test specific one
TEST_ALL = True
CURRENT_TEST_INDEX = 0

# RBAC Test Configuration
TEST_COMPANY_ID = "fb140d33-7e96-474d-a06d-ab3a6c65d1a9"
TEST_TEAM_NAME = "Sales"

# ============================================================
# AGENT 1: Intent Understanding Agent - ISOLATED TEST
# ============================================================
def test_intent_agent(user_query: str):
    print("=" * 70)
    print("🧪 TESTING: Intent Understanding Agent")
    print("=" * 70)
    print(f"📝 User Query: {user_query}")
    print(f"📅 Date Context: {get_date_context()}")
    print("-" * 70)
    
    # Get LLM
    llm = get_llm()
    intent_understanding_agent.llm = llm
    
    # Create isolated task with date context
    intent_task = create_intent_task(user_query)
    
    # Create mini crew with just this agent
    crew = Crew(
        agents=[intent_understanding_agent],
        tasks=[intent_task],
        process=Process.sequential,
        verbose=True,
    )
    
    print("\n🚀 Starting Agent Execution...\n")
    print("-" * 70)
    
    try:
        result = crew.kickoff()
        
        print("\n" + "=" * 70)
        print("✅ AGENT OUTPUT:")
        print("=" * 70)
        print(result)
        print("\n📊 Raw Output Type:", type(result))
        
        if hasattr(result, 'pydantic'):
            print("📋 Pydantic Output:", result.pydantic)
        if hasattr(result, 'json_dict'):
            print("📋 JSON Dict:", result.json_dict)
            
        print("=" * 70)
        
        return result
        
    except Exception as e:
        print("\n❌ ERROR:")
        print(e)
        import traceback
        traceback.print_exc()
        return None


# ============================================================
# AGENT 3: Table & Column Detection Agent - ISOLATED TEST
# ============================================================
def test_schema_agent(user_query: str, company_id: str, team_name: str):
    print("=" * 70)
    print("🧪 TESTING: Table & Column Detection Agent")
    print("=" * 70)
    print(f"📝 User Query: {user_query}")
    print(f"🏢 Company ID: {company_id}")
    print(f"👥 Team Name: {team_name}")
    print("-" * 70)
    
    # First, get intent from Agent 1 (simulated)
    print("\n📌 Step 1: Getting Intent...")
    intent_result = test_intent_agent(user_query)
    if not intent_result:
        print("❌ Failed to get intent")
        return None
    
    intent_data = intent_result.pydantic
    print(f"✅ Intent: {intent_data}")
    
    # Second, get RBAC from Agent 2 (simulated)  
    print("\n📌 Step 2: Getting RBAC Tables...")
    rbac_result = test_rbac_agent(company_id, team_name)
    if not rbac_result:
        print("❌ Failed to get RBAC")
        return None
        
    allowed_tables = rbac_result.pydantic.allowed_tables
    print(f"✅ Got {len(allowed_tables)} allowed tables")
    
    # Now test Agent 3
    print("\n" + "=" * 70)
    print("📌 Step 3: Testing Schema Detection Agent...")
    print("=" * 70)
    
    # Get LLM
    llm = get_llm()
    table_column_detection_agent.llm = llm
    
    # Setup tools
    from shared.config import get_vector_db_url
    import os
    
    # Get source DB settings
    from core.answering_context_builder import get_source_db_settings_from_postgres
    source_db = get_source_db_settings_from_postgres(company_id)
    
    if not source_db:
        print("❌ Failed to get source DB settings")
        return None
    
    tool_params = {
        "company_id": company_id,
        "db_server": source_db["db_server"],
        "db_database": source_db["db_database"],
        "db_username": source_db["db_username"],
        "db_password": source_db["db_password"],
        "vector_db_host": os.getenv("VECTOR_DB_HOST"),
        "vector_db_name": os.getenv("VECTOR_DB_NAME"),
        "vector_db_user": os.getenv("VECTOR_DB_USER"),
        "vector_db_password": os.getenv("VECTOR_DB_PASSWORD"),
        "metadata_url": get_vector_db_url()
    }
    
    vector_search_tool = VectorDBTableSearchTool(**tool_params)
    get_columns_tool = GetAvailableColumnsTool(**tool_params)
    table_column_detection_agent.tools = [vector_search_tool, get_columns_tool]
    
    # Create schema detection task with VERY explicit instructions
    group_by_instruction = "null (because group_by in intent is None/null)" if intent_data.group_by is None else f"find column matching '{intent_data.group_by}'"
    
    # Filter allowed_tables to only include Sales-related tables for revenue queries
    metric = intent_data.metric_word.lower()
    if 'revenue' in metric or 'sales' in metric or 'order' in metric:
        hint_tables = [t for t in allowed_tables if 'Sales' in t or 'Order' in t]
        table_hint = f"Best tables for revenue/sales: {hint_tables[:5]}"
    else:
        table_hint = ""
    
    schema_task = Task(
        name="schema_test_task",
        description=(
            f"Find the best table and columns for this query. YOU MUST USE BOTH TOOLS.\n\n"
            f"### INPUT ###\n"
            f"metric_word: '{intent_data.metric_word}'\n"
            f"group_by: {intent_data.group_by}\n"
            f"conditions: {intent_data.conditions}\n\n"
            f"allowed_tables (TOP 10): {allowed_tables[:10]}\n"
            f"{table_hint}\n\n"
            f"### MANDATORY TOOL CALLS ###\n"
            f"You MUST make these TWO tool calls in order:\n\n"
            f"TOOL CALL 1 - vector_db_table_search:\n"
            f"  Action: vector_db_table_search\n"
            f"  Action Input: {{'query_key': '{intent_data.metric_word}', 'allowed_tables': {allowed_tables}}}\n\n"
            f"TOOL CALL 2 - get_available_columns (REQUIRED - DO NOT SKIP):\n"
            f"  Action: get_available_columns\n"
            f"  Action Input: {{'table_name': 'Sales.SalesOrderHeader'}}\n\n"
            f"### AFTER BOTH TOOL CALLS ###\n"
            f"selected_column: Use TotalDue for revenue\n"
            f"group_by_column: {group_by_instruction}\n\n"
            f"### FINAL ANSWER FORMAT ###\n"
            f'{{"table_name": "Sales.SalesOrderHeader", "selected_column": "TotalDue", "group_by_column": null}}\n'
        ),
        expected_output="JSON: {\"table_name\": \"...\", \"selected_column\": \"...\", \"group_by_column\": null}",
        agent=table_column_detection_agent,
        output_pydantic=SchemaMappingOutput,
    )
    
    # Create mini crew
    crew = Crew(
        agents=[table_column_detection_agent],
        tasks=[schema_task],
        process=Process.sequential,
        verbose=True,
    )
    
    print("\n🚀 Starting Agent Execution...\n")
    print("-" * 70)
    
    try:
        result = crew.kickoff()
        
        print("\n" + "=" * 70)
        print("✅ SCHEMA AGENT OUTPUT:")
        print("=" * 70)
        print(result)
        print("\n📊 Raw Output Type:", type(result))
        
        if hasattr(result, 'pydantic'):
            pydantic_out = result.pydantic
            print("📋 Pydantic Output:", pydantic_out)
            
            # Post-process validation
            print("\n🔍 POST-PROCESS VALIDATION:")
            
            # Fix 1: Ensure table_name has schema prefix
            if pydantic_out.table_name and '.' not in pydantic_out.table_name:
                # Try to find the full name from allowed tables
                for t in allowed_tables:
                    if pydantic_out.table_name in t:
                        print(f"  ⚠️ Fixing table_name: '{pydantic_out.table_name}' -> '{t}'")
                        pydantic_out.table_name = t
                        break
            
            # Fix 2: Ensure group_by_column is None if intent has no group_by
            if intent_data.group_by is None and pydantic_out.group_by_column is not None:
                print(f"  ⚠️ Fixing group_by_column: '{pydantic_out.group_by_column}' -> None (intent has no group_by)")
                pydantic_out.group_by_column = None
            
            print("\n📋 CORRECTED Output:", pydantic_out)
            
        print("=" * 70)
        
        return result
        
    except Exception as e:
        print("\n❌ ERROR:")
        print(e)
        import traceback
        traceback.print_exc()
        return None
def test_rbac_agent(company_id: str, team_name: str):
    print("=" * 70)
    print("🧪 TESTING: Access Control Filter Agent (RBAC)")
    print("=" * 70)
    print(f"🏢 Company ID: {company_id}")
    print(f"👥 Team Name: {team_name}")
    print("-" * 70)
    
    # Get LLM
    llm = get_llm()
    access_control_filter_agent.llm = llm
    
    # Setup the tool with required params
    from shared.config import get_vector_db_url
    import os
    
    tool_params = {
        "company_id": company_id,
        "all_company_tables": [],  # Will be fetched by tool
        "vector_db_host": os.getenv("VECTOR_DB_HOST"),
        "vector_db_name": os.getenv("VECTOR_DB_NAME"),
        "vector_db_user": os.getenv("VECTOR_DB_USER"),
        "vector_db_password": os.getenv("VECTOR_DB_PASSWORD"),
        "metadata_url": get_vector_db_url()
    }
    
    rbac_tool = GetAllowedTablesTool(**tool_params)
    access_control_filter_agent.tools = [rbac_tool]
    
    # Create RBAC task
    rbac_task = Task(
        name="rbac_test_task",
        description=(
            f"Call the get_allowed_tables tool with team_name='{team_name}'.\n"
            "Return ONLY the JSON object with allowed_tables list."
        ),
        expected_output="A JSON object with key: allowed_tables containing list of table names.",
        agent=access_control_filter_agent,
        output_pydantic=RBACOutput,
    )
    
    # Create mini crew
    crew = Crew(
        agents=[access_control_filter_agent],
        tasks=[rbac_task],
        process=Process.sequential,
        verbose=True,
    )
    
    print("\n🚀 Starting Agent Execution...\n")
    print("-" * 70)
    
    try:
        result = crew.kickoff()
        
        print("\n" + "=" * 70)
        print("✅ AGENT OUTPUT:")
        print("=" * 70)
        print(result)
        print("\n📊 Raw Output Type:", type(result))
        
        if hasattr(result, 'pydantic'):
            print("📋 Pydantic Output:", result.pydantic)
            
        print("=" * 70)
        
        return result
        
    except Exception as e:
        print("\n❌ ERROR:")
        print(e)
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n" + "🔬 AGENT ISOLATION TEST MODE 🔬".center(70))
    print()
    
    # =============================================
    # Choose which agent to test:
    # 1 = Intent Agent
    # 2 = RBAC Agent
    # 3 = Schema Detection Agent
    # =============================================
    TEST_AGENT = 3  # <-- Change this to test different agents
    
    if TEST_AGENT == 1:
        # Test Intent Agent
        if TEST_ALL:
            results = []
            for i, query in enumerate(TEST_QUERIES):
                print(f"\n{'='*70}")
                print(f"📌 TEST {i+1}/{len(TEST_QUERIES)}")
                print(f"{'='*70}")
                result = test_intent_agent(query)
                results.append({"query": query, "result": result})
                print("\n" + "-"*70)
            
            print("\n" + "="*70)
            print("📊 SUMMARY OF ALL TESTS")
            print("="*70)
            for i, r in enumerate(results):
                print(f"\n{i+1}. Query: {r['query']}")
                if r['result'] and hasattr(r['result'], 'pydantic'):
                    print(f"   Result: {r['result'].pydantic}")
                else:
                    print(f"   Result: {r['result']}")
        else:
            result = test_intent_agent(TEST_QUERIES[CURRENT_TEST_INDEX])
            
    elif TEST_AGENT == 2:
        # Test RBAC Agent
        print("🔐 Testing RBAC Agent...")
        result = test_rbac_agent(TEST_COMPANY_ID, TEST_TEAM_NAME)
        
    elif TEST_AGENT == 3:
        # Test Schema Detection Agent
        print("🔍 Testing Schema Detection Agent...")
        # Test with a simple query first
        test_query = "What is the total revenue in 2023?"
        result = test_schema_agent(test_query, TEST_COMPANY_ID, TEST_TEAM_NAME)
    
    print("\n" + "=" * 70)
    print("🏁 Test Complete!")
    print("=" * 70)