# Experiment Backlog

One experiment a month, sized for about 4–6 hours of build time. Ordered by relevance to enterprise leadership conversations as of late 2026.

| # | Experiment | Trend it tests | Hypothesis | Build (MVP) | Success = |
|---|---|---|---|---|---|
| 02 | **Governed MCP gateway** | MCP is the de facto agent-to-tool standard; governance is the gap | Tool allow-lists, rate limits and audit logs can be enforced in a proxy, independent of the agent framework | Python MCP server exposing 3 mock tools + a gateway that enforces a YAML policy and writes a JSONL audit log | Blocked calls are logged; policy change needs no agent change |
| 03 | **A2A hand-off** | A2A reached v1.0 with signed Agent Cards | Cross-team agent collaboration fails mostly on identity and contract, not on intelligence | Two agents (intake → specialist) exchanging tasks via A2A; one has a tampered card | Tampered card is rejected; hand-off latency measured |
| 04 | **Minimum viable agent evals** | Observability is now "table stakes" for agent survival | 30 golden cases + tracing catch most regressions from a prompt/model change | LangGraph agent + Langfuse or Phoenix tracing + pytest eval suite | Deliberate regression is caught automatically in CI |
| 05 | **Cost-per-task benchmark** | Cost overruns are a top cancellation driver | A small model with good tools beats a frontier model on cost per *successful* task for structured workflows | Same task, 3 model tiers, 50 runs each; measure success, tokens, $ | Break-even chart published |
| 06 | **AI-interaction disclosure checker** | Transparency obligations for AI interactions now apply in major markets | Disclosure can be regression-tested like any UI requirement | Playwright test that asserts chatbot disclosure + human-escalation path | Test fails when disclosure is removed |
| 07 | **RAG vs long context** | Million-token context windows are mainstream | RAG still wins on cost and freshness above ~200 docs | Same Q&A set over a synthetic policy corpus, both approaches | Accuracy/cost/latency table |
| 08 | **Agent kill-switch drill** | Governance gaps surface only after incidents | A tested kill switch + rollback cuts incident time by >80% | Chaos-style script that trips a running agent mid-workflow | Recovery time measured before vs after |

## Idea parking lot
- Sovereign / in-region model hosting: latency and cost trade-offs
- Citizen-developer agent builder with guardrails-as-code
- Multi-agent org chart: when does adding agents reduce reliability?
