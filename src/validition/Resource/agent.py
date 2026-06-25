
"""
agent.py
========
The main Orchestrator of the system.
Coordinates all components and runs the pipeline from start to finish.

Usage:
    python agent.py --plan plan.json --resources company.txt
    python agent.py  (uses built-in demo data)
"""

from __future__ import annotations
import json
import argparse
import sys
from typing import Any

from processor   import build_user_prompt, parse_output, validate_output
from service     import run_simulation, format_report
from RE.search_tool import ALL_TOOLS
from RE.tasks import build_pipeline, AggregationTask, SimulationTask, ValidationTask, VerdictTask


# ── Agent Class ───────────────────────────────────────────────────────────────
class ResourceSimulatorAgent:
    """
    Agent that manages the simulation pipeline across four sequential tasks.
    """

    def __init__(self, verbose: bool = True):
        self.verbose  = verbose
        self.pipeline = build_pipeline()
        self.tools    = {t.name: t for t in ALL_TOOLS}

    # ── Public: run ───────────────────────────────────────────────────────────
    def run(self, plan_input: str, company_resources: str) -> dict[str, Any]:
        """
        Runs the full simulation and returns the Readiness Report.
        """
        self._log("🚀 Starting resource simulation...")

        # Task 1 — Aggregation
        agg_task: AggregationTask  = self.pipeline[0]
        agg_task.status            = "running"
        agg_task.plan_input        = plan_input
        agg_task.company_resources = company_resources
        agg_task.combined_prompt   = build_user_prompt(plan_input, company_resources)
        agg_task.status            = "done"
        self._log("✅ [1/4] Input aggregation — complete")

        # Task 2 — Simulation (LLM call via service layer)
        sim_task: SimulationTask = self.pipeline[1]
        sim_task.status          = "running"
        self._log("⚙️  [2/4] Calling Claude for simulation...")

        try:
            report = run_simulation(plan_input, company_resources)
            sim_task.status = "done"
        except Exception as e:
            sim_task.status = "failed"
            sim_task.error  = str(e)
            self._log(f"❌ Simulation failed: {e}")
            raise

        self._log("✅ [2/4] Claude response — received")

        # Task 3 — Validation
        val_task: ValidationTask = self.pipeline[2]
        val_task.status          = "running"
        is_valid, errors         = validate_output(report)
        val_task.report          = report
        val_task.is_valid        = is_valid
        val_task.errors          = errors

        if not is_valid:
            val_task.status = "failed"
            self._log(f"❌ Validation failed: {errors}")
            raise ValueError(f"Schema validation errors: {errors}")

        val_task.status = "done"
        self._log("✅ [3/4] JSON Schema validation — passed")

        # Task 4 — Verdict
        ver_task: VerdictTask     = self.pipeline[3]
        ver_task.status           = "running"
        verdict                   = report.get("overall_execution_verdict", {})
        ver_task.can_execute_plan = verdict.get("can_execute_plan", False)
        ver_task.blocking_factors = verdict.get("blocking_factors", [])
        ver_task.final_report     = report
        ver_task.status           = "done"

        decision = "✅ Plan can be executed" if ver_task.can_execute_plan else "🚫 Plan cannot be executed"
        self._log(f"✅ [4/4] Final verdict: {decision}")
        self._log("─" * 50)

        return report

    # ── Internal ──────────────────────────────────────────────────────────────
    def _log(self, msg: str):
        if self.verbose:
            print(msg)


# ── CLI Entry Point ───────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Resource Simulator AI Agent")
    parser.add_argument("--plan",      type=str, help="Path to plan file (JSON or TXT)")
    parser.add_argument("--resources", type=str, help="Path to company resources file (JSON or TXT)")
    parser.add_argument("--output",    type=str, help="Path to output file (optional)")
    parser.add_argument("--quiet",     action="store_true", help="Suppress log messages")
    args = parser.parse_args()

    # ── Read Inputs ───────────────────────────────────────────────────────────
    if args.plan:
        with open(args.plan, "r", encoding="utf-8") as f:
            plan_input = f.read()
    else:
        plan_input = DEMO_PLAN

    if args.resources:
        with open(args.resources, "r", encoding="utf-8") as f:
            company_resources = f.read()
    else:
        company_resources = DEMO_RESOURCES

    # ── Run Agent ─────────────────────────────────────────────────────────────
    agent  = ResourceSimulatorAgent(verbose=not args.quiet)
    report = agent.run(plan_input, company_resources)

    # ── Output ────────────────────────────────────────────────────────────────
    output_json = format_report(report)
    print("\n" + "═" * 50)
    print("📊 READINESS REPORT")
    print("═" * 50)
    print(output_json)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"\n💾 Report saved to: {args.output}")


# ── Demo Data ─────────────────────────────────────────────────────────────────
DEMO_PLAN = json.dumps({
    "all_actions": [
        {"action_type": "Open Branch",        "details": {"location": "Cairo", "channel": "Physical"}},
        {"action_type": "Hiring",             "details": {"department": "Sales", "scale": "New team"}},
        {"action_type": "Marketing Campaign", "details": {"channel": "Digital"}}
    ],
    "resource_requirements": {
        "financial":   ["Branch setup cost", "Marketing budget", "Employee salaries"],
        "human":       ["Sales representatives", "Branch manager"],
        "operational": ["Physical location", "Inventory management"]
    },
    "time_horizon": "Short to Medium Term"
}, ensure_ascii=False, indent=2)

DEMO_RESOURCES = """
Current Cash: 2,500,000 EGP
Monthly Burn Rate: 350,000 EGP/month
Current Runway: ~7 months | Minimum safe runway: 9 months

Current Employees: 18
Capacity Utilization: 85% occupied
Additional absorption capacity: Limited

Operational Assets:
- Main office in Alexandria only
- No office or contract in Cairo
- Basic inventory system not immediately scalable
"""

if __name__ == "__main__":
    main()