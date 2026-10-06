/**
 * Agent Readiness Scorecard Engine
 * Ported from Python experiments/01-agent-readiness-scorecard/scorecard/engine.py
 */

const VALUE_CAP_USD = 5000000;
const MATERIALITY_USD = 25000;

const AUTONOMY_RISK = {
    "suggest": 5,
    "draft": 12,
    "act_with_approval": 25,
    "act_autonomous": 35
};

const REVERSIBILITY_RISK = {
    "reversible": 0,
    "partially_reversible": 10,
    "irreversible": 20
};

const SENSITIVITY_RISK = {
    "public": 0,
    "internal": 5,
    "confidential": 12,
    "regulated": 20
};

const REGULATORY_RISK = {
    "none": 0,
    "transparency": 7,
    "high_risk": 15
};

const CUSTOMER_FACING_RISK = 10;

function clamp(x, lo = 0, hi = 100) {
    return Math.round(Math.max(lo, Math.min(hi, x)));
}

function calculateAnnualValue(uc) {
    const hoursSaved = (uc.tasks_per_month * 12 * uc.minutes_saved_per_task) / 60;
    return (hoursSaved * uc.loaded_cost_per_hour_usd) + uc.other_annual_value_usd;
}

function calculateValueScore(uc) {
    const gross = calculateAnnualValue(uc);
    const net = gross - uc.est_annual_run_cost_usd;
    
    let base = 0.0;
    if (net >= MATERIALITY_USD) {
        base = 70 * Math.log10(net / MATERIALITY_USD) / Math.log10(VALUE_CAP_USD / MATERIALITY_USD);
    }
    
    const score = base + (uc.kpi_defined ? 15 : 0) + (uc.exec_sponsor ? 15 : 0);
    
    let payback = null;
    if (net > 0) {
        payback = Math.round((uc.est_build_cost_usd / (net / 12)) * 10) / 10;
    }
    
    return {
        score: clamp(score),
        gross: gross,
        net: net,
        payback: payback
    };
}

function calculateReadinessScore(uc) {
    const score = (uc.data_access / 5 * 25) +
                  (uc.tool_apis / 5 * 25) +
                  (uc.process_documented / 5 * 20) +
                  (uc.eval_set_exists ? 15 : 0) +
                  (uc.observability_in_place ? 15 : 0);
    return clamp(score);
}

function calculateRiskScore(uc) {
    let score = AUTONOMY_RISK[uc.autonomy] +
                REVERSIBILITY_RISK[uc.reversibility] +
                SENSITIVITY_RISK[uc.data_sensitivity] +
                REGULATORY_RISK[uc.regulatory_scope] +
                (uc.customer_facing ? CUSTOMER_FACING_RISK : 0);
                
    score = clamp(score);
    
    let tier = "";
    if (uc.autonomy === "act_autonomous" && uc.reversibility === "irreversible") {
        score = Math.max(score, 76);
        tier = "Critical";
        return { score, tier };
    }
    
    if (score >= 76) tier = "Critical";
    else if (score >= 55) tier = "High";
    else if (score >= 30) tier = "Medium";
    else tier = "Low";
    
    return { score, tier };
}

function getRequiredControls(uc, tier) {
    const controls = ["Named business owner and model/agent card in the AI inventory"];
    
    if (["Medium", "High", "Critical"].includes(tier)) {
        controls.push(
            "End-to-end tracing of every LLM call, tool call and decision step",
            "Golden evaluation set with pass thresholds, re-run on every change",
            "Cost budget and per-task cost alerting"
        );
    }
    if (["High", "Critical"].includes(tier)) {
        controls.push(
            "Tool allow-list enforced at a gateway (e.g. MCP proxy) with per-action audit log",
            "Kill switch and rollback runbook tested before go-live",
            "Pre-production red-team / adversarial testing (prompt injection, data exfiltration)"
        );
    }
    if (tier === "Critical") {
        controls.push(
            "AI governance board sign-off before each autonomy increase",
            "Staged autonomy: start at act_with_approval, promote only on measured accuracy"
        );
    }
    if (["act_with_approval", "act_autonomous"].includes(uc.autonomy) || uc.reversibility !== "reversible") {
        controls.push("Human approval gate on irreversible or above-threshold actions");
    }
    if (uc.customer_facing || uc.regulatory_scope !== "none") {
        controls.push("Disclose AI interaction to end users; offer escalation to a human");
    }
    if (["confidential", "regulated"].includes(uc.data_sensitivity)) {
        controls.push("Data-loss prevention on prompts/outputs; confirm data residency for model hosting");
    }
    if (uc.regulatory_scope === "high_risk") {
        controls.push("Risk-management file, logging retention and human-oversight design per applicable AI regulation");
    }
    
    // Deduplicate while keeping order
    return [...new Set(controls)];
}

function scoreUseCase(uc) {
    const { score: v, gross, net, payback } = calculateValueScore(uc);
    const r = calculateReadinessScore(uc);
    const { score: risk, tier } = calculateRiskScore(uc);
    
    const gaps = [];
    if (!uc.kpi_defined) gaps.push("No measurable KPI agreed - define the success metric before building");
    if (!uc.exec_sponsor) gaps.push("No executive sponsor");
    if (uc.data_access < 3) gaps.push("Agent lacks reliable access to the data it needs");
    if (uc.tool_apis < 3) gaps.push("Target systems lack usable APIs/tools for the agent to act through");
    if (uc.process_documented < 3) gaps.push("Process is not documented well enough to specify agent behaviour");
    if (!uc.eval_set_exists) gaps.push("No evaluation set - you cannot prove it works or detect regressions");
    if (!uc.observability_in_place) gaps.push("No tracing/observability - you cannot see what the agent did or what it cost");
    if (payback !== null && payback > 18) gaps.push(`Payback of ${payback} months exceeds 18-month threshold`);
    
    const reasons = [];
    let verdict = "";
    
    if (v < 25) {
        verdict = "Stop";
        reasons.push("Value is too low to justify an agent; consider simpler automation");
    } else if (tier === "Critical" && r < 50) {
        verdict = "Stop";
        reasons.push("Critical risk with low readiness - the controls cannot be built in time");
    } else if (!uc.kpi_defined || r < 40) {
        verdict = "Rework before funding";
        reasons.push("Close the readiness/KPI gaps first; funding now risks a stalled pilot");
    } else if (["High", "Critical"].includes(tier) || r < 65 || v < 50) {
        verdict = "Pilot with guardrails";
        reasons.push("Promising, but prove value and controls in a bounded pilot first");
    } else {
        verdict = "Fund to production";
        reasons.push("Strong value, ready foundations and manageable risk");
    }
    
    return {
        annual_value_usd: Math.round(gross * 100) / 100,
        net_annual_value_usd: Math.round(net * 100) / 100,
        payback_months: payback,
        value_score: v,
        readiness_score: r,
        risk_score: risk,
        risk_tier: tier,
        verdict: verdict,
        reasons: reasons,
        gaps: gaps,
        controls: getRequiredControls(uc, tier)
    };
}

// UI Binding functions
function getFormData() {
    return {
        tasks_per_month: parseFloat(document.getElementById('tasks_per_month').value) || 0,
        minutes_saved_per_task: parseFloat(document.getElementById('minutes_saved').value) || 0,
        loaded_cost_per_hour_usd: parseFloat(document.getElementById('cost_per_hour').value) || 0,
        other_annual_value_usd: parseFloat(document.getElementById('other_value').value) || 0,
        est_annual_run_cost_usd: parseFloat(document.getElementById('run_cost').value) || 0,
        est_build_cost_usd: parseFloat(document.getElementById('build_cost').value) || 0,
        kpi_defined: document.getElementById('kpi_defined').checked,
        exec_sponsor: document.getElementById('exec_sponsor').checked,
        
        data_access: parseInt(document.getElementById('data_access').value) || 0,
        tool_apis: parseInt(document.getElementById('tool_apis').value) || 0,
        process_documented: parseInt(document.getElementById('process_documented').value) || 0,
        eval_set_exists: document.getElementById('eval_set').checked,
        observability_in_place: document.getElementById('observability').checked,
        
        autonomy: document.getElementById('autonomy').value,
        reversibility: document.getElementById('reversibility').value,
        data_sensitivity: document.getElementById('data_sensitivity').value,
        regulatory_scope: document.getElementById('regulatory_scope').value,
        customer_facing: document.getElementById('customer_facing').checked
    };
}

function updateUI() {
    const uc = getFormData();
    const result = scoreUseCase(uc);
    
    // Update Scores
    document.getElementById('value_score').textContent = result.value_score;
    document.getElementById('readiness_score').textContent = result.readiness_score;
    document.getElementById('risk_score').textContent = result.risk_score;
    document.getElementById('risk_tier').textContent = result.risk_tier;
    
    // Set colors for scores
    setScoreColor('value_score', result.value_score, true);
    setScoreColor('readiness_score', result.readiness_score, true);
    setScoreColor('risk_score', result.risk_score, false); // Risk is inverted logic for colors if needed
    
    // Format Currency
    const formatUSD = (val) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);
    document.getElementById('net_value').textContent = formatUSD(result.net_annual_value_usd);
    
    const paybackText = result.payback_months !== null ? `${result.payback_months} months` : 'N/A';
    document.getElementById('payback').textContent = paybackText;

    // Verdict styling
    const verdictEl = document.getElementById('verdict');
    verdictEl.textContent = result.verdict;
    verdictEl.className = 'verdict-badge ' + getVerdictClass(result.verdict);
    
    // Arrays rendering
    renderList('reasons_list', result.reasons);
    renderList('gaps_list', result.gaps);
    renderList('controls_list', result.controls);
}

function setScoreColor(elementId, score, isHigherBetter) {
    const el = document.getElementById(elementId);
    el.classList.remove('text-success', 'text-warning', 'text-danger');
    let colorClass = '';
    
    if (isHigherBetter) {
        if (score >= 65) colorClass = 'text-success';
        else if (score >= 40) colorClass = 'text-warning';
        else colorClass = 'text-danger';
    } else {
        if (score >= 76) colorClass = 'text-danger';
        else if (score >= 55) colorClass = 'text-warning';
        else colorClass = 'text-success';
    }
    
    el.classList.add(colorClass);
}

function getVerdictClass(verdict) {
    switch(verdict) {
        case 'Fund to production': return 'badge-success';
        case 'Pilot with guardrails': return 'badge-warning';
        case 'Rework before funding': return 'badge-orange';
        case 'Stop': return 'badge-danger';
        default: return 'badge-secondary';
    }
}

function renderList(elementId, items) {
    const el = document.getElementById(elementId);
    el.innerHTML = '';
    
    if (items.length === 0) {
        el.innerHTML = '<li class="text-muted">None detected.</li>';
        return;
    }
    
    items.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        el.appendChild(li);
    });
}

// Add event listeners on DOM load
document.addEventListener('DOMContentLoaded', () => {
    // Only run this if we're on the main page with the form
    if (!document.getElementById('tasks_per_month')) return;
    
    const inputs = document.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('change', updateUI);
        input.addEventListener('input', updateUI);
    });
    
    // Initial run
    updateUI();
});
