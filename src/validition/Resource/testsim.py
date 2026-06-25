"""
test.py
=======
Unit and integration tests for the system.
Tests are split into:
  - Unit tests  : processor + tasks + search_tool (no API calls)
  - Integration : service + agent (requires ANTHROPIC_API_KEY)
"""

import json
import unittest
from unittest.mock import patch, MagicMock

# ── Import Components ─────────────────────────────────────────────────────────
from processor   import build_user_prompt, parse_output, validate_output
from tasks       import build_pipeline, AggregationTask, SimulationTask, ValidationTask, VerdictTask
from search_tool import resource_gap_analysis_tool, runway_check_tool


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Unit Tests — Processor
# ═══════════════════════════════════════════════════════════════════════════════
class TestProcessor(unittest.TestCase):

    def test_build_user_prompt_contains_inputs(self):
        """Verifies that the prompt contains both inputs"""
        prompt = build_user_prompt("PLAN_DATA", "RESOURCE_DATA")
        self.assertIn("PLAN_DATA",     prompt)
        self.assertIn("RESOURCE_DATA", prompt)

    def test_parse_output_clean_json(self):
        """Verifies that parse_output parses clean JSON without issues"""
        sample = json.dumps({"key": "value"})
        result = parse_output(sample)
        self.assertEqual(result["key"], "value")

    def test_parse_output_strips_backticks(self):
        """Verifies that parse_output removes backticks"""
        sample = "```json\n{\"key\": \"val\"}\n```"
        result = parse_output(sample)
        self.assertEqual(result["key"], "val")

    def test_parse_output_invalid_raises(self):
        """Verifies that parse_output raises ValueError on invalid JSON"""
        with self.assertRaises(ValueError):
            parse_output("not a json string {{")

    def test_validate_output_valid(self):
        """Verifies that validate_output accepts a correct structure"""
        valid = _make_valid_report()
        is_valid, errors = validate_output(valid)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])

    def test_validate_output_missing_key(self):
        """Verifies that validate_output rejects an incomplete structure"""
        bad = {"financial_resources": {"status": "ok"}}
        is_valid, errors = validate_output(bad)
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Unit Tests — Tasks Pipeline
# ═══════════════════════════════════════════════════════════════════════════════
class TestTasks(unittest.TestCase):

    def test_pipeline_has_four_tasks(self):
        """Verifies that the pipeline contains 4 tasks in the correct order"""
        pipeline = build_pipeline()
        self.assertEqual(len(pipeline), 4)
        self.assertIsInstance(pipeline[0], AggregationTask)
        self.assertIsInstance(pipeline[1], SimulationTask)
        self.assertIsInstance(pipeline[2], ValidationTask)
        self.assertIsInstance(pipeline[3], VerdictTask)

    def test_tasks_start_as_pending(self):
        """Verifies that all tasks start with status=pending"""
        for task in build_pipeline():
            self.assertEqual(task.status, "pending")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Unit Tests — Search Tools
# ═══════════════════════════════════════════════════════════════════════════════
class TestSearchTools(unittest.TestCase):

    def test_gap_tool_all_ok(self):
        """Verifies PROCEED when all resources are sufficient"""
        result = resource_gap_analysis_tool.invoke({
            "financial_ok": True, "human_ok": True, "operational_ok": True
        })
        self.assertIn("PROCEED", result)

    def test_gap_tool_all_blocked(self):
        """Verifies BLOCKED with all three reasons when nothing is sufficient"""
        result = resource_gap_analysis_tool.invoke({
            "financial_ok": False, "human_ok": False, "operational_ok": False
        })
        self.assertIn("BLOCKED",     result)
        self.assertIn("Financial",   result)
        self.assertIn("Human",       result)
        self.assertIn("Operational", result)

    def test_runway_check_safe(self):
        """Verifies Safe status when runway is above minimum"""
        result = runway_check_tool.invoke({
            "current_cash":       5_000_000,
            "monthly_burn":         200_000,
            "extra_monthly_cost":    50_000,
            "min_safe_months":          9.0
        })
        self.assertIn("Safe", result)

    def test_runway_check_low(self):
        """Verifies Low status when runway is below minimum"""
        result = runway_check_tool.invoke({
            "current_cash":       1_000_000,
            "monthly_burn":         350_000,
            "extra_monthly_cost":   200_000,
            "min_safe_months":          9.0
        })
        self.assertIn("Low", result)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Integration Tests — Agent (Mocked LLM)
# ═══════════════════════════════════════════════════════════════════════════════
class TestAgentIntegration(unittest.TestCase):

    @patch("service.get_llm")
    def test_agent_run_success(self, mock_get_llm):
        """Runs the agent with a mocked LLM and verifies the output structure"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content=json.dumps(_make_valid_report()))
        mock_get_llm.return_value = mock_llm

        from agent import ResourceSimulatorAgent
        agent  = ResourceSimulatorAgent(verbose=False)
        report = agent.run("test plan", "test resources")

        self.assertIn("financial_resources",       report)
        self.assertIn("human_resources",           report)
        self.assertIn("operational_resources",     report)
        self.assertIn("overall_execution_verdict", report)

    @patch("service.get_llm")
    def test_agent_verdict_false(self, mock_get_llm):
        """Verifies that the agent returns can_execute_plan=False when blockers exist"""
        bad_report = _make_valid_report(can_execute=False)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content=json.dumps(bad_report))
        mock_get_llm.return_value = mock_llm

        from agent import ResourceSimulatorAgent
        agent  = ResourceSimulatorAgent(verbose=False)
        report = agent.run("plan", "resources")

        self.assertFalse(report["overall_execution_verdict"]["can_execute_plan"])

    @patch("service.get_llm")
    def test_financial_key_metrics_present(self, mock_get_llm):
        """Verifies that financial key_metrics contains required numeric fields"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content=json.dumps(_make_valid_report()))
        mock_get_llm.return_value = mock_llm

        from agent import ResourceSimulatorAgent
        report = ResourceSimulatorAgent(verbose=False).run("plan", "resources")

        metrics = report["financial_resources"]["key_metrics"]
        self.assertIn("cash_balance",             metrics)
        self.assertIn("runway_after_plan_months", metrics)

    @patch("service.get_llm")
    def test_human_key_metrics_present(self, mock_get_llm):
        """Verifies that human key_metrics contains required numeric fields"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content=json.dumps(_make_valid_report()))
        mock_get_llm.return_value = mock_llm

        from agent import ResourceSimulatorAgent
        report = ResourceSimulatorAgent(verbose=False).run("plan", "resources")

        metrics = report["human_resources"]["key_metrics"]
        self.assertIn("current_employees",  metrics)
        self.assertIn("required_new_hires", metrics)


# ── Helper ────────────────────────────────────────────────────────────────────
def _make_valid_report(can_execute: bool = True) -> dict:
    return {
        "financial_resources": {
            "is_sufficient": can_execute,
            "status": "Sufficient" if can_execute else "Insufficient for full execution",
            "why": [
                "Projected burn rate increases by 14%",
                "Cash runway drops to 7 months",
                "Minimum safe runway is 9 months"
            ],
            "key_metrics": {
                "cash_balance":             2_500_000,
                "runway_after_plan_months": 7
            }
        },
        "human_resources": {
            "is_sufficient": True,
            "status": "Sufficient with phased hiring",
            "why": [
                "Current team can absorb initial workload",
                "Only critical hires are required at later stages"
            ],
            "key_metrics": {
                "current_employees":  18,
                "required_new_hires": 6
            }
        },
        "operational_resources": {
            "is_sufficient": can_execute,
            "status": "Partially ready" if not can_execute else "Ready",
            "why": [] if can_execute else [
                "New physical location required",
                "Inventory processes not yet scalable"
            ]
        },
        "overall_execution_verdict": {
            "can_execute_plan": can_execute,
            "blocking_factors": [] if can_execute else [
                "Runway insufficient",
                "No operational location in Cairo"
            ]
        }
    }


# ── Runner ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🧪 Running Resource Simulator tests...\n")
    unittest.main(verbosity=2)