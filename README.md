# AI Leadership Lab

**Hands-on experiments on emerging enterprise AI — built small, written up for decision-makers.**

Each month I pick one technology shift that enterprise leaders are being asked to bet on, build the smallest thing that answers a real question about it, and publish what I learned: the code, the numbers and the "so what" for an executive audience.

> Opinions are cheap. Working code and honest limitations are not.

## Experiments

| # | Experiment | Question | Status |
|---|---|---|---|
| 01 | [Agent Readiness Scorecard](experiments/01-agent-readiness-scorecard) | Which agent use cases should we fund — and with which controls? | ✅ Published |
| 02 | Governed MCP gateway | Can tool allow-lists and audit logs be enforced *outside* the agent? | 🔜 Next |
| 03 | A2A hand-off between two agents | What breaks when agents from different teams collaborate? | Planned |
| 04 | Agent evaluation harness | What does a minimum viable eval + tracing setup look like? | Planned |
| 05 | Cost-per-task benchmark | Frontier vs small models on the same agent task — where's the break-even? | Planned |
| 06 | AI-interaction disclosure checker | Can transparency requirements be tested automatically? | Planned |
| 07 | RAG vs long context | When does retrieval still win? | Planned |

Full backlog with hypotheses and success criteria: [BACKLOG.md](BACKLOG.md)

## How each experiment is structured

Every folder follows [EXPERIMENT_TEMPLATE.md](EXPERIMENT_TEMPLATE.md):

1. **Question** — one sentence a CXO would ask
2. **Why now** — the trend that makes it urgent
3. **What I built** — smallest viable artefact, runnable in minutes
4. **Findings** — numbers first, then three takeaways for leaders
5. **Limitations** — what this does *not* prove

## Principles

- **Runnable in under 5 minutes.** Standard library where possible; pinned dependencies where not.
- **Synthetic data only.** No employer, client or personal data — ever.
- **Tested.** Each experiment ships with tests and CI.
- **Honest.** Limitations are part of the result.

## About

I'm an enterprise AI architect working on agentic AI, AI governance and AI operating models. [LinkedIn](https://www.linkedin.com/in/divyanshu-jain-ai-leader)

<sub>Views are my own. Nothing here is legal, compliance or investment advice. MIT licensed.</sub>
