import json
import time  # NEW: Added import for sleep
from json import JSONDecodeError  # NEW: Added import for specific exception
from ..graph.state import GraphState
from ..core.config import llm_model

# --- Node Functions --- 

def sales_analysis_and_recommendations_generator(state: GraphState):
    """
    Generates a comprehensive sales report.
    NOW INCLUDES A ROBUST RETRY MECHANISM.
    """
    print("---GENERATING SALES REPORT---")
    kpis = state.get("kpis")
    df = state.get("dataframe")
    # === MODIFICATION START: Get the user_request from the state ===
    user_request = state.get("user_request", "Generate a general sales analysis.")
    # === MODIFICATION END ===

    if not kpis or 'error' in kpis or df is None:
        print("❌ Missing KPIs or DataFrame. Skipping report generation.")
        return {"analysis_report": "Unable to generate a comprehensive sales report due to missing or invalid data."}
    
    kpis_text = json.dumps(kpis, indent=2)

    # === MODIFICATION START: Added user_request to the prompt ===
    prompt = f"""
        You are a professional and excellent data analyst and a highly skilled Sales Recommendation Agent.
        
        Your task is to generate a single, detailed, and actionable sales report. Your entire analysis and report MUST be based ONLY on the Key Performance Indicators (KPIs) provided below.
        
        **Do NOT write Python code. Do NOT explain data structures. Focus exclusively on creating the sales analysis and recommendations report as structured below.**
        
        The report must be structured in two main parts:
        
        **Part 1: Sales Analysis Report**
        1.  A brief introduction summarizing the main findings.
        2.  An analysis of each key performance indicator with an explanation of its importance.
        3.  A "Key Insights" section that draws deeper conclusions from the numbers and trends, such as sales trends, regional performance, or top-selling products.
        4.  A conclusion that provides a high-level summary.
        
        **Part 2: Actionable Recommendations**
        This part must be structured exactly as follows, using the insights from the analysis.
        
        1. Short-Term Plan (0-3 months)
        - Goal: Increase total orders by a data-driven percentage.
        - Analysis: Current monthly orders, region performance, key trends.
        - Recommendations / Actions: Digital marketing, sales incentives, training programs.
        - Scenarios: Best, Moderate, and Worst case projections.
        - Risk Management: How to reallocate resources if results are below expectations.
        
        2. Mid-Term Plan (3-6 months)
        - Goal: Increase Average Order Value (AOV) and improve margins.
        - Analysis: Current AOV, top-selling products, high-margin products.
        - Recommendations / Actions: Cross-selling, bundling, pricing adjustments.
        - Scenarios: Best / Moderate / Worst case with expected AOV impact.
        - Risk Management: Adjustments if adoption is lower than expected.
        
        3. Long-Term Plan (6+ months)
        - Goal: Increase annual sales growth and expand market share.
        - Analysis: Current growth rate, untapped regions, top channels.
        - Recommendations / Actions: Geographic expansion, channel development, social selling.
        - Scenarios: Best / Moderate / Worst case with expected growth percentages.
        - Risk Management: How to reduce investment in case of failure.
        
        ---
        **HERE ARE THE KPIS FOR YOUR ANALYSIS:**
        {kpis_text}

        **HERE IS THE ORIGINAL USER REQUEST:**
        "{user_request}"

        Please ensure your analysis, insights, and recommendations **directly address this user request**, using the KPIs as evidence.
        """
    # === MODIFICATION END ===

    # --- MODIFIED: Replaced the single try-except with a robust retry mechanism ---
    max_retries = 3
    report_response = None
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries} to generate sales report...")
            report_response = llm_model.invoke(prompt)
            if report_response and report_response.content:
                print("✅ Sales report generated successfully.")
                break  # Exit loop on success
            else:
                print(f"⚠️ Warning: Received an empty response on attempt {attempt + 1}.")
                if attempt + 1 < max_retries:
                    time.sleep(5)
        except (JSONDecodeError, Exception) as e:
            print(f"⚠️ Warning: An error occurred during report generation on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt + 1 < max_retries:
                time.sleep(5)

    if report_response and report_response.content:
        report_text = report_response.content
    else:
        print("❌ Failed to generate sales report after all retries.")
        report_text = "Failed to generate the sales report after multiple attempts due to API errors."

    return {"analysis_report": report_text}

def employee_analysis_and_recommendations_generator(state: GraphState):
    """
    Generates a comprehensive employee report.
    NOW INCLUDES A ROBUST RETRY MECHANISM.
    """
    print("---GENERATING EMPLOYEES REPORT---")
    kpis = state.get("kpis")
    df = state.get("dataframe")
    # === MODIFICATION START: Get the user_request from the state ===
    user_request = state.get("user_request", "Generate a general employee analysis.")
    # === MODIFICATION END ===

    if not kpis or 'error' in kpis or df is None:
        print("❌ Missing KPIs or DataFrame. Skipping report generation.")
        return {"analysis_report": "Unable to generate a comprehensive employee report due to missing or invalid data."}

    kpis_text = json.dumps(kpis, indent=2)

    # === MODIFICATION START: Added user_request to the prompt ===
    prompt = f"""
        You are a professional and excellent HR Data Analyst and a highly skilled Employee Performance and Retention Advisor.
        
        Your task is to generate a single, detailed, and actionable report based on employee data. Your entire analysis MUST be based ONLY on the Key Performance Indicators (KPIs) provided below.
        
        **Do NOT write Python code. Do NOT explain data structures. Focus exclusively on creating the HR analysis and recommendations report as structured below.**
        
        The report must be structured in two main parts:
        
        **Part 1: Employee Analysis Report**
        1.  A brief introduction summarizing the main findings.
        2.  An analysis of each key performance indicator (KPI), explaining its significance.
        3.  A "Key Insights" section that draws deeper conclusions from the numbers and trends.
        4.  A conclusion that provides a high-level summary.
        
        **Part 2: Actionable Recommendations**
        This part must be structured exactly as follows, using the insights from the analysis.
        
        1.  Short-Term Plan (0-3 months)
        -   **Goal:** Address immediate performance and morale issues.
        -   **Analysis:** Performance metrics, salary distribution, turnover trends.
        -   **Recommendations / Actions:** Implement performance improvement plans, conduct surveys, review salaries.
        -   **Reasoning:** Link each action to a specific insight from your analysis.

        2.  Mid-Term Plan (3-6 months)
        -   **Goal:** Improve employee retention and engagement.
        -   **Analysis:** Historical departure trends, training participation.
        -   **Recommendations / Actions:** Launch professional development budget, create mentorship program.
        -   **Reasoning:** Justify why these actions will lead to higher retention.

        3.  Long-Term Plan (6+ months)
        -   **Goal:** Foster a strong company culture and build a robust talent pipeline.
        -   **Analysis:** Long-term growth and skill gaps.
        -   **Recommendations / Actions:** Design leadership training, establish succession planning.
        -   **Reasoning:** Explain the long-term benefits to the company.
        
        ---
        **HERE ARE THE KPIS FOR YOUR ANALYSIS:**
        {kpis_text}

        **HERE IS THE ORIGINAL USER REQUEST:**
        "{user_request}"

        Please ensure your analysis, insights, and recommendations **directly address this user request**, using the KPIs as evidence.
        """
    # === MODIFICATION END ===
    
    # --- MODIFIED: Replaced the single try-except with a robust retry mechanism ---
    max_retries = 3
    report_response = None
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries} to generate employee report...")
            report_response = llm_model.invoke(prompt)
            if report_response and report_response.content:
                print("✅ Employee report generated successfully.")
                break  # Exit loop on success
            else:
                print(f"⚠️ Warning: Received an empty response on attempt {attempt + 1}.")
                if attempt + 1 < max_retries:
                    time.sleep(5)
        except (JSONDecodeError, Exception) as e:
            print(f"⚠️ Warning: An error occurred during report generation on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt + 1 < max_retries:
                time.sleep(5)

    if report_response and report_response.content:
        report_text = report_response.content
    else:
        print("❌ Failed to generate employee report after all retries.")
        report_text = "Failed to generate the employee report after multiple attempts due to API errors."

    return {"analysis_report": report_text}
