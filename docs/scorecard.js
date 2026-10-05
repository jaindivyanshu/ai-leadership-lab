/*
 * Agent Readiness Scorecard - JavaScript port of
 * experiments/01-agent-readiness-scorecard/scorecard/engine.py
 *
 * Kept deliberately 1:1 with the Python engine (same weights, thresholds and
 * Python-style rounding). tests/web/parity.mjs checks both produce identical
 * results on the sample portfolio in CI.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.Scorecard = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const VALUE_CAP_USD = 5_000_000;
  const MATERIALITY_USD = 25_000;

  const AUTONOMY_RISK = { suggest: 5, draft: 12, act_with_approval: 25, act_autonomous: 35 };
  const REVERSIBILITY_RISK = { reversible: 0, partially_reversible: 10, irreversible: 20 };
  const SENSITIVITY_RISK = { public: 0, internal: 5, confidential: 12, regulated: 20 };
  const REGULATORY_RISK = { none: 0, transparency: 7, high_risk: 15 };
  const CUSTOMER_FACING_RISK = 10;

  const DEFAULTS = {
    name: "", owner_function: "", description: "",
    tasks_per_month: 0, minutes_saved_per_task: 0, loaded_cost_per_hour_usd: 0,
    other_annual_value_usd: 0, kpi_defined: false, exec_sponsor: false,
    data_access: 0, tool_apis: 0, process_documented: 0,
    eval_set_exists: false, observability_in_place: false,
    autonomy: "suggest", reversibility: "reversible", data_sensitivity: "internal",
    customer_facing: false, regulatory_scope: "none",
    est_annual_run_cost_usd: 0, est_build_cost_usd: 0, tags: [],
  };

  /* Python's round(): round-half-to-even on the *exact* decimal expansion of
     the double (toFixed(100) gives that expansion for values in our range). */
  function pyRound(x, ndigits) {
    const nd = ndigits || 0;
    if (!isFinite(x)) return x;
    const neg = x < 0;
    const [ip, fp] = Math.abs(x).toFixed(100).split(".");
    const kept = ip + fp.slice(0, nd);
    const rest = fp.slice(nd);
    let up;
    if (rest[0] > "5") up = true;
    else if (rest[0] < "5") up = false;
    else up = /[1-9]/.test(rest.slice(1)) || Number(kept[kept.length - 1]) % 2 === 1;
    let n = BigInt(kept) + (up ? 1n : 0n);
    let s = n.toString().padStart(nd + 1, "0");
    const r = Number(nd ? s.slice(0, -nd) + "." + s.slice(-nd) : s);
    return neg && r !== 0 ? -r : r;
  }

  const clamp = (x, lo = 0, hi = 100) => pyRound(Math.max(lo, Math.min(hi, x)));

  function normalise(raw) {
    const uc = Object.assign({}, DEFAULTS, raw || {});
    const errors = [];
    const enums = {
      autonomy: AUTONOMY_RISK, reversibility: REVERSIBILITY_RISK,
      data_sensitivity: SENSITIVITY_RISK, regulatory_scope: REGULATORY_RISK,
    };
    for (const [k, table] of Object.entries(enums)) {
      if (!(uc[k] in table)) errors.push(`${k} must be one of ${Object.keys(table).join(", ")}`);
    }
    for (const k of ["data_access", "tool_apis", "process_documented"]) {
      uc[k] = Number(uc[k]);
      if (!Number.isInteger(uc[k]) || uc[k] < 0 || uc[k] > 5) errors.push(`${k} must be an integer 0-5`);
    }
    for (const k of ["tasks_per_month", "minutes_saved_per_task", "loaded_cost_per_hour_usd",
      "other_annual_value_usd", "est_annual_run_cost_usd", "est_build_cost_usd"]) {
      uc[k] = Number(uc[k]) || 0;
      if (uc[k] < 0) errors.push(`${k} cannot be negative`);
    }
    for (const k of ["kpi_defined", "exec_sponsor", "eval_set_exists", "observability_in_place", "customer_facing"]) {
      uc[k] = Boolean(uc[k]);
    }
    return { uc, errors };
  }

  function annualValue(uc) {
    const hoursSaved = uc.tasks_per_month * 12 * uc.minutes_saved_per_task / 60;
    return hoursSaved * uc.loaded_cost_per_hour_usd + uc.other_annual_value_usd;
  }

  function valueScore(uc) {
    const gross = annualValue(uc);
    const net = gross - uc.est_annual_run_cost_usd;
    const base = net < MATERIALITY_USD ? 0
      : 70 * Math.log10(net / MATERIALITY_USD) / Math.log10(VALUE_CAP_USD / MATERIALITY_USD);
    const score = base + (uc.kpi_defined ? 15 : 0) + (uc.exec_sponsor ? 15 : 0);
    const payback = net > 0 ? pyRound(uc.est_build_cost_usd / (net / 12), 1) : null;
    return { score: clamp(score), gross, net, payback };
  }

  function readinessScore(uc) {
    return clamp(
      uc.data_access / 5 * 25 + uc.tool_apis / 5 * 25 + uc.process_documented / 5 * 20 +
      (uc.eval_set_exists ? 15 : 0) + (uc.observability_in_place ? 15 : 0)
    );
  }

  function riskScore(uc) {
    let score = clamp(
      AUTONOMY_RISK[uc.autonomy] + REVERSIBILITY_RISK[uc.reversibility] +
      SENSITIVITY_RISK[uc.data_sensitivity] + REGULATORY_RISK[uc.regulatory_scope] +
      (uc.customer_facing ? CUSTOMER_FACING_RISK : 0)
    );
    if (uc.autonomy === "act_autonomous" && uc.reversibility === "irreversible") {
      return { score: Math.max(score, 76), tier: "Critical" };
    }
    const tier = score >= 76 ? "Critical" : score >= 55 ? "High" : score >= 30 ? "Medium" : "Low";
    return { score, tier };
  }

  function requiredControls(uc, tier) {
    const c = ["Named business owner and model/agent card in the AI inventory"];
    if (["Medium", "High", "Critical"].includes(tier)) c.push(
      "End-to-end tracing of every LLM call, tool call and decision step",
      "Golden evaluation set with pass thresholds, re-run on every change",
      "Cost budget and per-task cost alerting");
    if (["High", "Critical"].includes(tier)) c.push(
      "Tool allow-list enforced at a gateway (e.g. MCP proxy) with per-action audit log",
      "Kill switch and rollback runbook tested before go-live",
      "Pre-production red-team / adversarial testing (prompt injection, data exfiltration)");
    if (tier === "Critical") c.push(
      "AI governance board sign-off before each autonomy increase",
      "Staged autonomy: start at act_with_approval, promote only on measured accuracy");
    if (["act_with_approval", "act_autonomous"].includes(uc.autonomy) || uc.reversibility !== "reversible")
      c.push("Human approval gate on irreversible or above-threshold actions");
    if (uc.customer_facing || uc.regulatory_scope !== "none")
      c.push("Disclose AI interaction to end users; offer escalation to a human");
    if (["confidential", "regulated"].includes(uc.data_sensitivity))
      c.push("Data-loss prevention on prompts/outputs; confirm data residency for model hosting");
    if (uc.regulatory_scope === "high_risk")
      c.push("Risk-management file, logging retention and human-oversight design per applicable AI regulation");
    return [...new Set(c)];
  }

  function score(raw) {
    const { uc, errors } = normalise(raw);
    if (errors.length) return { errors };
    const v = valueScore(uc);
    const r = readinessScore(uc);
    const risk = riskScore(uc);

    const gaps = [];
    if (!uc.kpi_defined) gaps.push("No measurable KPI agreed - define the success metric before building");
    if (!uc.exec_sponsor) gaps.push("No executive sponsor");
    if (uc.data_access < 3) gaps.push("Agent lacks reliable access to the data it needs");
    if (uc.tool_apis < 3) gaps.push("Target systems lack usable APIs/tools for the agent to act through");
    if (uc.process_documented < 3) gaps.push("Process is not documented well enough to specify agent behaviour");
    if (!uc.eval_set_exists) gaps.push("No evaluation set - you cannot prove it works or detect regressions");
    if (!uc.observability_in_place) gaps.push("No tracing/observability - you cannot see what the agent did or what it cost");
    if (v.payback !== null && v.payback > 18) gaps.push(`Payback of ${v.payback.toFixed(1)} months exceeds 18-month threshold`);

    let verdict, reason;
    if (v.score < 25) {
      verdict = "Stop"; reason = "Value is too low to justify an agent; consider simpler automation";
    } else if (risk.tier === "Critical" && r < 50) {
      verdict = "Stop"; reason = "Critical risk with low readiness - the controls cannot be built in time";
    } else if (!uc.kpi_defined || r < 40) {
      verdict = "Rework before funding"; reason = "Close the readiness/KPI gaps first; funding now risks a stalled pilot";
    } else if (["High", "Critical"].includes(risk.tier) || r < 65 || v.score < 50) {
      verdict = "Pilot with guardrails"; reason = "Promising, but prove value and controls in a bounded pilot first";
    } else {
      verdict = "Fund to production"; reason = "Strong value, ready foundations and manageable risk";
    }

    return {
      use_case: uc,
      annual_value_usd: pyRound(v.gross, 2),
      net_annual_value_usd: pyRound(v.net, 2),
      payback_months: v.payback,
      value_score: v.score,
      readiness_score: r,
      risk_score: risk.score,
      risk_tier: risk.tier,
      verdict,
      reasons: [reason],
      gaps,
      controls: requiredControls(uc, risk.tier),
    };
  }

  return { score, DEFAULTS, pyRound, VERSION: "0.1.0" };
});
