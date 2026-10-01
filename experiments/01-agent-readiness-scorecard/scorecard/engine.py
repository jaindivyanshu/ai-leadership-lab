"""Scoring engine: value, readiness and risk -> verdict + tiered controls.

Design choices (see README for rationale):
* Value is log-scaled so a $5M case doesn't make a $500k case look worthless.
* Risk is scored separately from value; a high-value case can still be blocked.
* Controls are *tiered by risk*, not uniform - light-touch for suggestion
  agents, heavy for autonomous agents acting on irreversible, regulated work.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .model import UseCase

VALUE_CAP_USD = 5_000_000  # net annual value that earns a full 70 value points
MATERIALITY_USD = 25_000  # net annual value below which value points are zero

AUTONOMY_RISK = {"suggest": 5, "draft": 12, "act_with_approval": 25, "act_autonomous": 35}
REVERSIBILITY_RISK = {"reversible": 0, "partially_reversible": 10, "irreversible": 20}
SENSITIVITY_RISK = {"public": 0, "internal": 5, "confidential": 12, "regulated": 20}
REGULATORY_RISK = {"none": 0, "transparency": 7, "high_risk": 15}
CUSTOMER_FACING_RISK = 10

VERDICTS = ("Fund to production", "Pilot with guardrails", "Rework before funding", "Stop")


@dataclass
class ScoreResult:
    use_case: UseCase
    annual_value_usd: float
    net_annual_value_usd: float
    payback_months: float | None
    value_score: int
    readiness_score: int
    risk_score: int
    risk_tier: str
    verdict: str
    reasons: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    controls: list[str] = field(default_factory=list)


def _clamp(x: float, lo: float = 0, hi: float = 100) -> int:
    return int(round(max(lo, min(hi, x))))


def annual_value(uc: UseCase) -> float:
    hours_saved = uc.tasks_per_month * 12 * uc.minutes_saved_per_task / 60
    return hours_saved * uc.loaded_cost_per_hour_usd + uc.other_annual_value_usd


def value_score(uc: UseCase) -> tuple[int, float, float, float | None]:
    gross = annual_value(uc)
    net = gross - uc.est_annual_run_cost_usd
    if net < MATERIALITY_USD:
        base = 0.0  # below this, an agent is rarely worth the governance overhead
    else:
        base = 70 * math.log10(net / MATERIALITY_USD) / math.log10(VALUE_CAP_USD / MATERIALITY_USD)
    score = base + (15 if uc.kpi_defined else 0) + (15 if uc.exec_sponsor else 0)
    payback = None
    if net > 0:
        payback = round(uc.est_build_cost_usd / (net / 12), 1)
    return _clamp(score), gross, net, payback


def readiness_score(uc: UseCase) -> int:
    score = (
        uc.data_access / 5 * 25
        + uc.tool_apis / 5 * 25
        + uc.process_documented / 5 * 20
        + (15 if uc.eval_set_exists else 0)
        + (15 if uc.observability_in_place else 0)
    )
    return _clamp(score)


def risk_score(uc: UseCase) -> tuple[int, str]:
    score = (
        AUTONOMY_RISK[uc.autonomy]
        + REVERSIBILITY_RISK[uc.reversibility]
        + SENSITIVITY_RISK[uc.data_sensitivity]
        + REGULATORY_RISK[uc.regulatory_scope]
        + (CUSTOMER_FACING_RISK if uc.customer_facing else 0)
    )
    score = _clamp(score)
    if uc.autonomy == "act_autonomous" and uc.reversibility == "irreversible":
        return max(score, 76), "Critical"
    if score >= 76:
        tier = "Critical"
    elif score >= 55:
        tier = "High"
    elif score >= 30:
        tier = "Medium"
    else:
        tier = "Low"
    return score, tier


def required_controls(uc: UseCase, tier: str) -> list[str]:
    controls = ["Named business owner and model/agent card in the AI inventory"]
    if tier in ("Medium", "High", "Critical"):
        controls += [
            "End-to-end tracing of every LLM call, tool call and decision step",
            "Golden evaluation set with pass thresholds, re-run on every change",
            "Cost budget and per-task cost alerting",
        ]
    if tier in ("High", "Critical"):
        controls += [
            "Tool allow-list enforced at a gateway (e.g. MCP proxy) with per-action audit log",
            "Kill switch and rollback runbook tested before go-live",
            "Pre-production red-team / adversarial testing (prompt injection, data exfiltration)",
        ]
    if tier == "Critical":
        controls += [
            "AI governance board sign-off before each autonomy increase",
            "Staged autonomy: start at act_with_approval, promote only on measured accuracy",
        ]
    if uc.autonomy in ("act_with_approval", "act_autonomous") or uc.reversibility != "reversible":
        controls.append("Human approval gate on irreversible or above-threshold actions")
    if uc.customer_facing or uc.regulatory_scope != "none":
        controls.append("Disclose AI interaction to end users; offer escalation to a human")
    if uc.data_sensitivity in ("confidential", "regulated"):
        controls.append("Data-loss prevention on prompts/outputs; confirm data residency for model hosting")
    if uc.regulatory_scope == "high_risk":
        controls.append("Risk-management file, logging retention and human-oversight design per applicable AI regulation")
    # de-duplicate, keep order
    seen: set[str] = set()
    return [c for c in controls if not (c in seen or seen.add(c))]


def score(uc: UseCase) -> ScoreResult:
    v, gross, net, payback = value_score(uc)
    r = readiness_score(uc)
    risk, tier = risk_score(uc)

    gaps: list[str] = []
    if not uc.kpi_defined:
        gaps.append("No measurable KPI agreed - define the success metric before building")
    if not uc.exec_sponsor:
        gaps.append("No executive sponsor")
    if uc.data_access < 3:
        gaps.append("Agent lacks reliable access to the data it needs")
    if uc.tool_apis < 3:
        gaps.append("Target systems lack usable APIs/tools for the agent to act through")
    if uc.process_documented < 3:
        gaps.append("Process is not documented well enough to specify agent behaviour")
    if not uc.eval_set_exists:
        gaps.append("No evaluation set - you cannot prove it works or detect regressions")
    if not uc.observability_in_place:
        gaps.append("No tracing/observability - you cannot see what the agent did or what it cost")
    if payback is not None and payback > 18:
        gaps.append(f"Payback of {payback} months exceeds 18-month threshold")

    reasons: list[str] = []
    if v < 25:
        verdict = "Stop"
        reasons.append("Value is too low to justify an agent; consider simpler automation")
    elif tier == "Critical" and r < 50:
        verdict = "Stop"
        reasons.append("Critical risk with low readiness - the controls cannot be built in time")
    elif not uc.kpi_defined or r < 40:
        verdict = "Rework before funding"
        reasons.append("Close the readiness/KPI gaps first; funding now risks a stalled pilot")
    elif tier in ("High", "Critical") or r < 65 or v < 50:
        verdict = "Pilot with guardrails"
        reasons.append("Promising, but prove value and controls in a bounded pilot first")
    else:
        verdict = "Fund to production"
        reasons.append("Strong value, ready foundations and manageable risk")

    return ScoreResult(
        use_case=uc,
        annual_value_usd=round(gross, 2),
        net_annual_value_usd=round(net, 2),
        payback_months=payback,
        value_score=v,
        readiness_score=r,
        risk_score=risk,
        risk_tier=tier,
        verdict=verdict,
        reasons=reasons,
        gaps=gaps,
        controls=required_controls(uc, tier),
    )
