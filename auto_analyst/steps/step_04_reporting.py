import json
from auto_analyst.graph.state import GraphState
from auto_analyst.core.config import llm_model

# --- Node Functions --- 

def sales_analysis_and_recommendations_generator(state: GraphState):
    """
    Generates a comprehensive sales report including both analysis and recommendations, using a powerful, specific prompt.
    """
    print("---GENERATING SALES REPORT---")
    kpis = state.get("kpis")
    df = state.get("dataframe")

    if not kpis or 'error' in kpis or df is None:
        print("❌ Missing KPIs or DataFrame. Skipping report generation.")
        return {"analysis_report": "Unable to generate a comprehensive sales report due to missing or invalid data."}
    
    kpis_text = json.dumps(kpis, indent=2)
    sample_df = df.sample(n=min(100, len(df)), random_state=42)

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
        - Analysis:
          - Current monthly orders.
          - Best performing region(s) and underperforming region(s).
          - Key trends or anomalies.
        - Recommendations / Actions:
          - Digital marketing campaigns: budget %, target regions, expected impact.
          - Incentive programs for sales reps: bonus per extra order, criteria.
          - Training programs: tailored training per sales rep based on performance.
          - Reasoning for each action.
        - Scenarios:
          - Best Case: projected orders and revenue.
          - Moderate Case: realistic projection.
          - Worst Case: flat growth and mitigation actions.
          - Risk Management: how to reallocate resources if results are below expectations.
        
        2. Mid-Term Plan (3-6 months)
        - Goal: Increase Average Order Value (AOV) and improve margins.
        - Analysis:
          - Current AOV.
          - Top-selling products.
          - High-margin products.
        - Recommendations / Actions:
          - Cross-selling and bundling strategies.
          - Pricing adjustments for high-margin products.
          - Reasoning for each action.
        - Scenarios:
          - Best / Moderate / Worst case with expected AOV and revenue impact.
        - Risk Management: adjustments if adoption is lower than expected.
        
        3. Long-Term Plan (6+ months)
        - Goal: Increase annual sales growth and expand market share.
        - Analysis:
          - Current annual growth rate.
          - Untapped regions and top-performing channels.
        - Recommendations / Actions:
          - Geographic expansion and investment amount.
          - Channel development budget and strategies.
          - Social selling: train reps to engage on LinkedIn/Twitter.
          - Reasoning for each action.
        - Scenarios:
          - Best / Moderate / Worst case with expected growth percentages.
          - Risk Management: how to reduce investment or redirect resources in case of failure.
        
        Output Format:
        - Use clear markdown headings for both parts and sub-sections.
        - Do not just list the numbers; provide real, insightful analysis and connect the dots between the different metrics.
        
        ---
        **HERE ARE THE KPIS FOR YOUR ANALYSIS:**
        {kpis_text}
        """
    try:
        report_response = llm_model.invoke(prompt)
        report_text = report_response.content
        print("✅ Sales report generated successfully.")
    except Exception as e:
        print(f"❌ Error generating sales report with LLM: {e}")
        report_text = "An error occurred while generating the sales report. Please try again."

    return {"analysis_report": report_text}

def employee_analysis_and_recommendations_generator(state: GraphState):
    """
    Generates a comprehensive employee report with analysis and recommendations.
    """
    print("---GENERATING EMPLOYEES REPORT---")
    kpis = state.get("kpis")
    df = state.get("dataframe")

    if not kpis or 'error' in kpis or df is None:
        print("❌ Missing KPIs or DataFrame. Skipping report generation.")
        return {"analysis_report": "Unable to generate a comprehensive employee report due to missing or invalid data."}

    kpis_text = json.dumps(kpis, indent=2)
    sample_df = df.sample(n=min(100, len(df)), random_state=42)

    prompt = f"""
        You are a professional and excellent HR Data Analyst and a highly skilled Employee Performance and Retention Advisor.
        
        Your task is to generate a single, detailed, and actionable report based on employee data. Your entire analysis MUST be based ONLY on the Key Performance Indicators (KPIs) provided below.
        
        **Do NOT write Python code. Do NOT explain data structures. Focus exclusively on creating the HR analysis and recommendations report as structured below.**
        
        The report must be structured in two main parts:
        
        **Part 1: Employee Analysis Report**
        1.  A brief introduction summarizing the main findings.
        2.  An analysis of each key performance indicator (KPI), explaining its significance (e.g., average salary, department-wise distribution, retention rate).
        3.  A "Key Insights" section that draws deeper conclusions from the numbers and trends, such as factors influencing low performance, salary disparities, or departments with high turnover.
        4.  A conclusion that provides a high-level summary.
        
        **Part 2: Actionable Recommendations**
        This part must be structured exactly as follows, using the insights from the analysis.
        
        1.  Short-Term Plan (0-3 months)
        -   **Goal:** Address immediate performance and morale issues.
        -   **Analysis:** Current performance metrics (if available), salary distribution analysis, recent turnover trends.
        -   **Recommendations / Actions:** Implement performance improvement plans for underperforming employees. Conduct anonymous surveys to gauge morale. Review and adjust entry-level salaries in underpaid departments.
        -   **Reasoning:** Link each action to a specific insight from your analysis (e.g., "Adjusting salaries in 'Sales' is crucial due to high turnover rates shown in the data.").

        2.  Mid-Term Plan (3-6 months)
        -   **Goal:** Improve employee retention and engagement.
        -   **Analysis:** Analyze historical data to identify trends in employee departures. Examine training participation rates.
        -   **Recommendations / Actions:** Launch a professional development budget for each employee. Create a mentorship program to boost internal promotions.
        -   **Reasoning:** Justify why these actions will lead to higher retention (e.g., "Investing in development shows commitment and reduces the likelihood of top talent leaving for better opportunities.").

        3.  Long-Term Plan (6+ months)
        -   **Goal:** Foster a strong company culture and build a robust talent pipeline.
        -   **Analysis:** Review long-term growth and skill gaps within the company.
        -   **Recommendations / Actions:** Design a comprehensive leadership training program. Establish a formal succession planning process for key roles. Develop a plan for long-term hiring and market share expansion.
        -   **Reasoning:** Explain how these actions will benefit the company's long-term health (e.g., "A strong internal pipeline ensures business continuity and reduces hiring costs.").
        
        Output Format:
        - Use clear markdown headings for both parts and sub-sections.
        - Do not just list the numbers; provide real, insightful analysis and connect the dots between the different metrics.
        
        ---
        **HERE ARE THE KPIS FOR YOUR ANALYSIS:**
        {kpis_text}
        """
    try:
        report_response = llm_model.invoke(prompt)
        report_text = report_response.content
        print("✅ Employee report generated successfully.")
    except Exception as e:
        print(f"❌ Error generating employee report with LLM: {e}")
        report_text = "An error occurred while generating the employee report. Please try again."

    return {"analysis_report": report_text}