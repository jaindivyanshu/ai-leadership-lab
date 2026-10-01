"""Render ScoreResults as Markdown."""
from __future__ import annotations

from .engine import ScoreResult

VERDICT_BADGE = {
    "Fund to production": "🟢",
    "Pilot with guardrails": "🟡",
    "Rework before funding": "🟠",
    "Stop": "🔴",
}


def _usd(x: float) -> str:
    return f"${x:,.0f}"


def _bar(score: int, width: int = 20) -> str:
    filled = round(score / 100 * width)
    return "█" * filled + "░" * (width - filled)


def render_one(r: ScoreResult) -> str:
    uc = r.use_case
    payback = f"{r.payback_months} months" if r.payback_months is not None else "n/a (no net value)"
    lines = [
        f"## {VERDICT_BADGE[r.verdict]} {uc.name}",
        "",
        f"*{uc.owner_function}* — {uc.description}".rstrip(" —"),
        "",
        f"**Verdict: {r.verdict}** · Risk tier: **{r.risk_tier}**",
        "",
        "| Pillar | Score | |",
        "|---|---:|---|",
        f"| Value | {r.value_score} | `{_bar(r.value_score)}` |",
        f"| Readiness | {r.readiness_score} | `{_bar(r.readiness_score)}` |",
        f"| Risk (higher = riskier) | {r.risk_score} | `{_bar(r.risk_score)}` |",
        "",
        f"Gross annual value **{_usd(r.annual_value_usd)}** · net of run cost **{_usd(r.net_annual_value_usd)}** · payback **{payback}**",
        "",
        "**Why:** " + " ".join(r.reasons),
        "",
    ]
    if r.gaps:
        lines += ["**Gaps to close**", ""] + [f"- {g}" for g in r.gaps] + [""]
    lines += ["**Required controls for this risk tier**", ""] + [f"- [ ] {c}" for c in r.controls] + [""]
    return "\n".join(lines)


def render_portfolio(results: list[ScoreResult]) -> str:
    order = {v: i for i, v in enumerate(VERDICT_BADGE)}
    results = sorted(results, key=lambda r: (order[r.verdict], -r.value_score))
    head = [
        "# Agent Portfolio Readiness Report",
        "",
        "| Use case | Verdict | Value | Readiness | Risk | Net value / yr |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in results:
        head.append(
            f"| {r.use_case.name} | {VERDICT_BADGE[r.verdict]} {r.verdict} | {r.value_score} | "
            f"{r.readiness_score} | {r.risk_score} ({r.risk_tier}) | {_usd(r.net_annual_value_usd)} |"
        )
    head.append("")
    return "\n".join(head + [render_one(r) for r in results])
