"""Generate use cases + Python scorecard results for the JS parity test.

Usage (from repo root):
    python tests/web/gen_cases.py > /tmp/parity.json
    node tests/web/parity.mjs /tmp/parity.json
"""
import dataclasses
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "experiments" / "01-agent-readiness-scorecard"
sys.path.insert(0, str(EXP))

from scorecard import UseCase, score  # noqa: E402
from scorecard.model import AUTONOMY_LEVELS, DATA_SENSITIVITY, REGULATORY_SCOPE, REVERSIBILITY  # noqa: E402


def random_case(rng: random.Random, i: int) -> dict:
    return {
        "name": f"case-{i}",
        "owner_function": "Synthetic",
        "tasks_per_month": rng.choice([0, 50, 300, 1200, 8000, 40000, 120000]),
        "minutes_saved_per_task": rng.choice([0, 1, 2.5, 5, 9, 12, 20, 45]),
        "loaded_cost_per_hour_usd": rng.choice([0, 18, 25, 35, 40, 45, 90]),
        "other_annual_value_usd": rng.choice([0, 0, 0, 50000, 400000, 2000000]),
        "kpi_defined": rng.random() < 0.6,
        "exec_sponsor": rng.random() < 0.6,
        "data_access": rng.randint(0, 5),
        "tool_apis": rng.randint(0, 5),
        "process_documented": rng.randint(0, 5),
        "eval_set_exists": rng.random() < 0.5,
        "observability_in_place": rng.random() < 0.5,
        "autonomy": rng.choice(AUTONOMY_LEVELS),
        "reversibility": rng.choice(REVERSIBILITY),
        "data_sensitivity": rng.choice(DATA_SENSITIVITY),
        "customer_facing": rng.random() < 0.4,
        "regulatory_scope": rng.choice(REGULATORY_SCOPE),
        "est_annual_run_cost_usd": rng.choice([0, 12000, 60000, 180000, 900000]),
        "est_build_cost_usd": rng.choice([0, 20000, 150000, 450000, 2000000]),
    }


def main() -> None:
    rng = random.Random(2026)
    cases = json.loads((EXP / "examples" / "sample_portfolio.json").read_text(encoding="utf-8"))
    cases += [random_case(rng, i) for i in range(2000)]
    out = []
    for c in cases:
        r = dataclasses.asdict(score(UseCase.from_dict(c)))
        r.pop("use_case")
        out.append({"input": c, "expected": r})
    json.dump(out, sys.stdout)


if __name__ == "__main__":
    main()
