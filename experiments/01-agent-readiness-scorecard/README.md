# Experiment 01 — Agent Readiness Scorecard

> **Question:** Can we tell, *before* funding, which agentic AI use cases will reach production — and which will stall?

## Why this matters now

Enterprises have moved from "should we use agents?" to "which of these 40 agent ideas do we fund?" Analyst forecasts expect a large share of agentic AI projects to be cancelled by 2027 for three reasons: **escalating cost, unclear business value, and inadequate risk controls**. All three are visible at intake — if you look.

A second lesson from 2026: **uniform governance fails**. Applying the same heavy controls to a meeting summariser and an autonomous payments agent either strangles the low-risk work or under-protects the high-risk work. Controls need to be *tiered by risk*.

## What I built

A small, dependency-free Python tool that scores a use case on three independent pillars and returns a verdict plus the controls it must have.

```
use case (JSON) ──► Value      (log-scaled net $ + KPI + sponsor)          ─┐
                ──► Readiness  (data, APIs, process, evals, observability) ─┼─► Verdict + gaps + tiered controls
                ──► Risk       (autonomy, reversibility, data, users, reg) ─┘
```

| Verdict | Rule of thumb |
|---|---|
| 🟢 Fund to production | High value, ready foundations, risk ≤ Medium |
| 🟡 Pilot with guardrails | Promising, but risk is High or readiness is incomplete |
| 🟠 Rework before funding | No agreed KPI, or readiness < 40 |
| 🔴 Stop | Value below materiality, or Critical risk with low readiness |

**Controls are tiered.** A Low-risk case gets one control (an owner and an inventory entry). A Critical case — e.g. an autonomous agent taking irreversible actions on regulated data — gets gateway-enforced tool allow-lists, per-action audit logs, kill switch, red-teaming, staged autonomy and board sign-off.

## Run it

**In the browser:** [jaindivyanshu.github.io/ai-leadership-lab](https://jaindivyanshu.github.io/ai-leadership-lab/). It has the same engine ported to JavaScript (`docs/scorecard.js`). CI checks it gives identical results to the Python version on the sample portfolio plus 2,000 random cases.

**From the command line:**

```bash
cd experiments/01-agent-readiness-scorecard
python -m scorecard examples/sample_portfolio.json            # Markdown to stdout
python -m scorecard examples/sample_portfolio.json -o report.md
python -m scorecard examples/sample_portfolio.json --json      # for dashboards
python -m unittest discover -s tests                           # 15 tests
```

Python 3.10+, standard library only.

## Findings from the sample portfolio

See [`examples/sample_report.md`](examples/sample_report.md). Five synthetic use cases:

| Use case | Verdict | What the scorecard caught |
|---|---|---|
| Service desk triage | 🟢 Fund | Everything in place — evals, tracing, APIs, sponsor |
| Bank reconciliation | 🟡 Pilot | $1M+ value, but no eval set, no tracing and weak APIs |
| Sales copilot | 🟠 Rework | Big number, **no agreed KPI** — the #1 cause of "negative ROI" pilots |
| Autonomous refunds | 🔴 Stop | Autonomous + irreversible + regulated + customer-facing, with low readiness |
| Meeting summariser | 🔴 Stop | $3k/yr — use an off-the-shelf tool, not a governed agent |

**Three takeaways for leaders**

1. **The biggest value number is rarely the best first bet.** Readiness — evals and observability especially — separates pilots that ship from pilots that stall.
2. **"No KPI" should be a hard stop at intake.** It costs nothing to fix before funding and everything to fix after.
3. **Autonomy is a dial, not a switch.** Start at `act_with_approval`, measure, then promote. The scorecard makes that explicit.

## Limitations & next steps

- Weights are opinionated defaults, not calibrated on outcome data. Next: calibrate against real pilot outcomes.
- Risk tiers are generic; map them to your own AI policy and to the regulations you operate under.
- Next experiment: enforce the High-tier controls at runtime with an MCP gateway ([Backlog](../../BACKLOG.md)).

---
<sub>All examples are synthetic. Not legal or compliance advice.</sub>
