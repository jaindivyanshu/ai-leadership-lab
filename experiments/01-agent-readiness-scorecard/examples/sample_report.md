# Agent Portfolio Readiness Report

| Use case | Verdict | Value | Readiness | Risk | Net value / yr |
|---|---|---:|---:|---:|---:|
| Service desk triage & auto-resolution | 🟢 Fund to production | 90 | 86 | 30 (Medium) | $2,340,000 |
| Bank reconciliation agent | 🟡 Pilot with guardrails | 80 | 41 | 47 (Medium) | $1,080,000 |
| Sales lead-enrichment copilot | 🟠 Rework before funding | 68 | 53 | 24 (Low) | $1,420,000 |
| Autonomous refund agent | 🔴 Stop | 51 | 33 | 92 (Critical) | $390,000 |
| Meeting-notes summariser | 🔴 Stop | 0 | 52 | 10 (Low) | $3,000 |

## 🟢 Service desk triage & auto-resolution

*IT Operations* — Multi-agent system that classifies tickets, routes them and resolves password/access requests.

**Verdict: Fund to production** · Risk tier: **Medium**

| Pillar | Score | |
|---|---:|---|
| Value | 90 | `██████████████████░░` |
| Readiness | 86 | `█████████████████░░░` |
| Risk (higher = riskier) | 30 | `██████░░░░░░░░░░░░░░` |

Gross annual value **$2,520,000** · net of run cost **$2,340,000** · payback **2.3 months**

**Why:** Strong value, ready foundations and manageable risk

**Required controls for this risk tier**

- [ ] Named business owner and model/agent card in the AI inventory
- [ ] End-to-end tracing of every LLM call, tool call and decision step
- [ ] Golden evaluation set with pass thresholds, re-run on every change
- [ ] Cost budget and per-task cost alerting
- [ ] Human approval gate on irreversible or above-threshold actions

## 🟡 Bank reconciliation agent

*Finance - Controllership* — Matches ledger entries to bank statements and proposes journal adjustments.

**Verdict: Pilot with guardrails** · Risk tier: **Medium**

| Pillar | Score | |
|---|---:|---|
| Value | 80 | `████████████████░░░░` |
| Readiness | 41 | `████████░░░░░░░░░░░░` |
| Risk (higher = riskier) | 47 | `█████████░░░░░░░░░░░` |

Gross annual value **$1,200,000** · net of run cost **$1,080,000** · payback **3.3 months**

**Why:** Promising, but prove value and controls in a bounded pilot first

**Gaps to close**

- Target systems lack usable APIs/tools for the agent to act through
- No evaluation set - you cannot prove it works or detect regressions
- No tracing/observability - you cannot see what the agent did or what it cost

**Required controls for this risk tier**

- [ ] Named business owner and model/agent card in the AI inventory
- [ ] End-to-end tracing of every LLM call, tool call and decision step
- [ ] Golden evaluation set with pass thresholds, re-run on every change
- [ ] Cost budget and per-task cost alerting
- [ ] Human approval gate on irreversible or above-threshold actions
- [ ] Data-loss prevention on prompts/outputs; confirm data residency for model hosting

## 🟠 Sales lead-enrichment copilot

*Sales* — Drafts account briefs and next-best-action suggestions for B2B sales reps.

**Verdict: Rework before funding** · Risk tier: **Low**

| Pillar | Score | |
|---|---:|---|
| Value | 68 | `██████████████░░░░░░` |
| Readiness | 53 | `███████████░░░░░░░░░` |
| Risk (higher = riskier) | 24 | `█████░░░░░░░░░░░░░░░` |

Gross annual value **$1,480,000** · net of run cost **$1,420,000** · payback **1.3 months**

**Why:** Close the readiness/KPI gaps first; funding now risks a stalled pilot

**Gaps to close**

- No measurable KPI agreed - define the success metric before building
- Process is not documented well enough to specify agent behaviour
- No evaluation set - you cannot prove it works or detect regressions

**Required controls for this risk tier**

- [ ] Named business owner and model/agent card in the AI inventory
- [ ] Data-loss prevention on prompts/outputs; confirm data residency for model hosting

## 🔴 Autonomous refund agent

*Customer Service* — Issues customer refunds end-to-end without human review.

**Verdict: Stop** · Risk tier: **Critical**

| Pillar | Score | |
|---|---:|---|
| Value | 51 | `██████████░░░░░░░░░░` |
| Readiness | 33 | `███████░░░░░░░░░░░░░` |
| Risk (higher = riskier) | 92 | `██████████████████░░` |

Gross annual value **$480,000** · net of run cost **$390,000** · payback **7.7 months**

**Why:** Critical risk with low readiness - the controls cannot be built in time

**Gaps to close**

- No executive sponsor
- Agent lacks reliable access to the data it needs
- Process is not documented well enough to specify agent behaviour
- No evaluation set - you cannot prove it works or detect regressions
- No tracing/observability - you cannot see what the agent did or what it cost

**Required controls for this risk tier**

- [ ] Named business owner and model/agent card in the AI inventory
- [ ] End-to-end tracing of every LLM call, tool call and decision step
- [ ] Golden evaluation set with pass thresholds, re-run on every change
- [ ] Cost budget and per-task cost alerting
- [ ] Tool allow-list enforced at a gateway (e.g. MCP proxy) with per-action audit log
- [ ] Kill switch and rollback runbook tested before go-live
- [ ] Pre-production red-team / adversarial testing (prompt injection, data exfiltration)
- [ ] AI governance board sign-off before each autonomy increase
- [ ] Staged autonomy: start at act_with_approval, promote only on measured accuracy
- [ ] Human approval gate on irreversible or above-threshold actions
- [ ] Disclose AI interaction to end users; offer escalation to a human
- [ ] Data-loss prevention on prompts/outputs; confirm data residency for model hosting

## 🔴 Meeting-notes summariser

*Corporate* — Summarises internal meeting transcripts.

**Verdict: Stop** · Risk tier: **Low**

| Pillar | Score | |
|---|---:|---|
| Value | 0 | `░░░░░░░░░░░░░░░░░░░░` |
| Readiness | 52 | `██████████░░░░░░░░░░` |
| Risk (higher = riskier) | 10 | `██░░░░░░░░░░░░░░░░░░` |

Gross annual value **$15,000** · net of run cost **$3,000** · payback **80.0 months**

**Why:** Value is too low to justify an agent; consider simpler automation

**Gaps to close**

- No measurable KPI agreed - define the success metric before building
- No executive sponsor
- No evaluation set - you cannot prove it works or detect regressions
- No tracing/observability - you cannot see what the agent did or what it cost
- Payback of 80.0 months exceeds 18-month threshold

**Required controls for this risk tier**

- [ ] Named business owner and model/agent card in the AI inventory
