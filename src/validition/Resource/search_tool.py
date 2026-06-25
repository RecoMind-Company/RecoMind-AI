

"""
search_tool.py
==============
Defines the LangChain Tools for the Resource Simulator.
These tools are invoked by the Agent when it needs to analyze resource gaps.
"""

from langchain.tools import tool


@tool
def resource_gap_analysis_tool(financial_ok: bool, human_ok: bool, operational_ok: bool) -> str:
    """
    Calculates the overall execution verdict based on the status of the three resource types.

    Args:
        financial_ok:    Are financial resources sufficient?
        human_ok:        Are human resources sufficient?
        operational_ok:  Are operational resources sufficient?

    Returns:
        str: "PROCEED" if all resources are sufficient, otherwise "BLOCKED: <reasons>"
    """
    blockers = []

    if not financial_ok:
        blockers.append("Financial resources are insufficient")
    if not human_ok:
        blockers.append("Human resources are insufficient or require urgent hiring")
    if not operational_ok:
        blockers.append("Operational resources are missing (location, equipment, systems)")

    if not blockers:
        return "PROCEED: All resources are sufficient for immediate execution"

    return "BLOCKED: " + " | ".join(blockers)


@tool
def runway_check_tool(
    current_cash: float,
    monthly_burn: float,
    extra_monthly_cost: float,
    min_safe_months: float = 9.0
) -> str:
    """
    Calculates whether the runway is sufficient after adding plan costs.

    Args:
        current_cash:       Current available cash in EGP
        monthly_burn:       Current monthly burn rate
        extra_monthly_cost: Additional monthly costs from the plan
        min_safe_months:    Minimum safe runway in months (default: 9)

    Returns:
        str: Runway report with verdict
    """
    new_burn   = monthly_burn + extra_monthly_cost
    new_runway = current_cash / new_burn if new_burn > 0 else float("inf")
    burn_pct   = ((new_burn - monthly_burn) / monthly_burn * 100) if monthly_burn > 0 else 0

    status = "Safe" if new_runway >= min_safe_months else ("Critical" if new_runway >= 6 else "Low")

    return (
        f"New burn rate: {new_burn:,.0f} EGP/month | "
        f"Increase: {burn_pct:.1f}% | "
        f"New runway: {new_runway:.1f} months | "
        f"Status: {status}"
    )


# List of all available tools to be imported in agent.py
ALL_TOOLS = [resource_gap_analysis_tool, runway_check_tool]