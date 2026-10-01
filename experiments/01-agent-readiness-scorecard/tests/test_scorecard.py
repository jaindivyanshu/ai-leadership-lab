import json
import unittest
from pathlib import Path

from scorecard import UseCase, ValidationError, render_portfolio, score
from scorecard.__main__ import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "sample_portfolio.json"


def base(**overrides):
    d = dict(
        name="t", owner_function="f", tasks_per_month=10000, minutes_saved_per_task=10,
        loaded_cost_per_hour_usd=40, kpi_defined=True, exec_sponsor=True, data_access=5,
        tool_apis=5, process_documented=5, eval_set_exists=True, observability_in_place=True,
        est_annual_run_cost_usd=50000, est_build_cost_usd=100000,
    )
    d.update(overrides)
    return UseCase.from_dict(d)


class TestValidation(unittest.TestCase):
    def test_unknown_field_rejected(self):
        with self.assertRaises(ValidationError):
            UseCase.from_dict({"name": "x", "owner_function": "y", "bogus": 1})

    def test_bad_enum_rejected(self):
        with self.assertRaises(ValidationError):
            base(autonomy="yolo")

    def test_readiness_range(self):
        with self.assertRaises(ValidationError):
            base(data_access=7)

    def test_missing_required(self):
        with self.assertRaises(ValidationError):
            UseCase.from_dict({"name": "x"})


class TestScoring(unittest.TestCase):
    def test_strong_case_is_funded(self):
        r = score(base())
        self.assertEqual(r.verdict, "Fund to production")
        self.assertEqual(r.risk_tier, "Low")
        self.assertEqual(r.readiness_score, 100)

    def test_annual_value_math(self):
        r = score(base())
        # 10k tasks * 12 * 10min / 60 * $40 = $800,000
        self.assertEqual(r.annual_value_usd, 800000)
        self.assertEqual(r.net_annual_value_usd, 750000)
        self.assertEqual(r.payback_months, 1.6)

    def test_autonomous_irreversible_is_critical(self):
        r = score(base(autonomy="act_autonomous", reversibility="irreversible"))
        self.assertEqual(r.risk_tier, "Critical")
        self.assertIn("Kill switch and rollback runbook tested before go-live", r.controls)

    def test_critical_and_unready_is_stopped(self):
        r = score(base(autonomy="act_autonomous", reversibility="irreversible",
                       data_access=1, tool_apis=1, process_documented=1,
                       eval_set_exists=False, observability_in_place=False))
        self.assertEqual(r.verdict, "Stop")

    def test_no_kpi_means_rework(self):
        r = score(base(kpi_defined=False))
        self.assertEqual(r.verdict, "Rework before funding")

    def test_negative_net_value_is_stopped(self):
        r = score(base(tasks_per_month=10, est_annual_run_cost_usd=100000,
                       kpi_defined=False, exec_sponsor=False))
        self.assertEqual(r.value_score, 0)
        self.assertIsNone(r.payback_months)
        self.assertEqual(r.verdict, "Stop")

    def test_controls_are_tiered_not_uniform(self):
        low = score(base())
        high = score(base(autonomy="act_autonomous", data_sensitivity="regulated", customer_facing=True))
        self.assertLess(len(low.controls), len(high.controls))

    def test_customer_facing_requires_disclosure(self):
        r = score(base(customer_facing=True))
        self.assertTrue(any("Disclose AI interaction" in c for c in r.controls))


class TestEndToEnd(unittest.TestCase):
    def test_sample_portfolio_verdicts(self):
        cases = [UseCase.from_dict(d) for d in json.loads(EXAMPLES.read_text())]
        verdicts = {uc.name: score(uc).verdict for uc in cases}
        self.assertEqual(verdicts["Service desk triage & auto-resolution"], "Fund to production")
        self.assertEqual(verdicts["Bank reconciliation agent"], "Pilot with guardrails")
        self.assertEqual(verdicts["Autonomous refund agent"], "Stop")
        self.assertEqual(verdicts["Sales lead-enrichment copilot"], "Rework before funding")
        self.assertEqual(verdicts["Meeting-notes summariser"], "Stop")

    def test_report_renders(self):
        cases = [UseCase.from_dict(d) for d in json.loads(EXAMPLES.read_text())]
        md = render_portfolio([score(c) for c in cases])
        self.assertIn("# Agent Portfolio Readiness Report", md)
        self.assertEqual(md.count("## "), len(cases))

    def test_cli_exit_codes(self):
        self.assertEqual(main([str(EXAMPLES), "--json"]), 0)
        self.assertEqual(main(["does-not-exist.json"]), 2)


if __name__ == "__main__":
    unittest.main()
