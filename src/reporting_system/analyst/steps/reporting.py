"""Report generation steps for LangGraph workflow."""

import json
import logging
import time
from typing import Dict, Any
from json import JSONDecodeError

from analyst.state import GraphState
from config.database import get_langgraph_llm

logger = logging.getLogger(__name__)


def sales_analysis_and_recommendations_generator(state: GraphState) -> Dict[str, Any]:
    """Generates comprehensive sales analysis report from calculated KPIs."""
    logger.info("--- STAGE 3.6: GENERATING SALES REPORT ---")
    kpis = state.get("kpis")
    df = state.get("dataframe")
    user_request = state.get("user_request", "Generate a general sales analysis.")

    if not kpis or "error" in kpis or df is None:
        logger.warning("Missing KPIs or DataFrame. Skipping sales report generation.")
        return {"analysis_report": "Unable to generate a comprehensive sales report due to missing or invalid data."}

    kpis_text = json.dumps(kpis, indent=2)

    prompt = f"""
        You are a professional data analyst and a highly skilled Sales Recommendation Agent.
        
        Your task is to generate a single, detailed, and actionable sales report. Your entire analysis and report MUST be based ONLY on the Key Performance Indicators (KPIs) provided below.
        
        **Do NOT write Python code. Do NOT explain data structures. Focus exclusively on creating the sales analysis and recommendations report as structured below.**
        
        The report must be structured in two main parts:
        
        **Part 1: Sales Analysis Report**
        1. A brief introduction summarizing the main findings.
        2. An analysis of each key performance indicator with an explanation of its importance.
        3. A "Key Insights" section that draws deeper conclusions from the numbers and trends, such as sales trends, regional performance, or top-selling products.
        4. A conclusion that provides a high-level summary.
        
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

    llm = get_langgraph_llm()
    max_retries = 3
    report_response = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries} generating sales report...")
            report_response = llm.invoke(prompt)
            if report_response and report_response.content:
                logger.info("Sales report generated successfully.")
                break
            if attempt < max_retries:
                time.sleep(2)
        except (JSONDecodeError, Exception) as e:
            logger.warning(f"Attempt {attempt}/{max_retries} error generating sales report: {e}")
            if attempt < max_retries:
                time.sleep(2)

    if report_response and report_response.content:
        return {"analysis_report": report_response.content}

    logger.error("Failed to generate sales report after all retries.")
    return {"analysis_report": "Failed to generate the sales report after multiple attempts due to API errors."}


def employee_analysis_and_recommendations_generator(state: GraphState) -> Dict[str, Any]:
    """Generates comprehensive employee performance report from calculated KPIs."""
    logger.info("--- STAGE 3.6: GENERATING EMPLOYEE REPORT ---")
    kpis = state.get("kpis")
    df = state.get("dataframe")
    user_request = state.get("user_request", "Generate a general employee analysis.")

    if not kpis or "error" in kpis or df is None:
        logger.warning("Missing KPIs or DataFrame. Skipping employee report generation.")
        return {"analysis_report": "Unable to generate a comprehensive employee report due to missing or invalid data."}

    kpis_text = json.dumps(kpis, indent=2)

    prompt = f"""
        You are a professional HR Data Analyst and a highly skilled Employee Performance and Retention Advisor.
        
        Your task is to generate a single, detailed, and actionable report based on employee data. Your entire analysis MUST be based ONLY on the Key Performance Indicators (KPIs) provided below.
        
        **Do NOT write Python code. Do NOT explain data structures. Focus exclusively on creating the HR analysis and recommendations report as structured below.**
        
        The report must be structured in two main parts:
        
        **Part 1: Employee Analysis Report**
        1. A brief introduction summarizing the main findings.
        2. An analysis of each key performance indicator (KPI), explaining its significance.
        3. A "Key Insights" section that draws deeper conclusions from the numbers and trends.
        4. A conclusion that provides a high-level summary.
        
        **Part 2: Actionable Recommendations**
        This part must be structured exactly as follows, using the insights from the analysis.
        
        1. Short-Term Plan (0-3 months)
        - **Goal:** Address immediate performance and morale issues.
        - **Analysis:** Performance metrics, salary distribution, turnover trends.
        - **Recommendations / Actions:** Implement performance improvement plans, conduct surveys, review salaries.
        - **Reasoning:** Link each action to a specific insight from your analysis.

        2. Mid-Term Plan (3-6 months)
        - **Goal:** Improve employee retention and engagement.
        - **Analysis:** Historical departure trends, training participation.
        - **Recommendations / Actions:** Launch professional development budget, create mentorship program.
        - **Reasoning:** Justify why these actions will lead to higher retention.

        3. Long-Term Plan (6+ months)
        - **Goal:** Foster a strong company culture and build a robust talent pipeline.
        - **Analysis:** Long-term growth and skill gaps.
        - **Recommendations / Actions:** Design leadership training, establish succession planning.
        - **Reasoning:** Explain the long-term benefits to the company.
        
        ---
        **HERE ARE THE KPIS FOR YOUR ANALYSIS:**
        {kpis_text}

        **HERE IS THE ORIGINAL USER REQUEST:**
        "{user_request}"

        Please ensure your analysis, insights, and recommendations **directly address this user request**, using the KPIs as evidence.
    """

    llm = get_langgraph_llm()
    max_retries = 3
    report_response = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries} generating employee report...")
            report_response = llm.invoke(prompt)
            if report_response and report_response.content:
                logger.info("Employee report generated successfully.")
                break
            if attempt < max_retries:
                time.sleep(2)
        except (JSONDecodeError, Exception) as e:
            logger.warning(f"Attempt {attempt}/{max_retries} error generating employee report: {e}")
            if attempt < max_retries:
                time.sleep(2)

    if report_response and report_response.content:
        return {"analysis_report": report_response.content}

    logger.error("Failed to generate employee report after all retries.")
    return {"analysis_report": "Failed to generate the employee report after multiple attempts due to API errors."}
