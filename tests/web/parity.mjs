// Checks docs/scorecard.js returns exactly what the Python engine returns.
// Usage: node tests/web/parity.mjs <cases.json produced by gen_cases.py>
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const Scorecard = require("../../docs/scorecard.js");

const FIELDS = ["annual_value_usd", "net_annual_value_usd", "payback_months", "value_score",
  "readiness_score", "risk_score", "risk_tier", "verdict", "reasons", "gaps", "controls"];

const cases = JSON.parse(readFileSync(process.argv[2], "utf8"));
let failures = 0;
for (const { input, expected } of cases) {
  const got = Scorecard.score(input);
  for (const f of FIELDS) {
    if (JSON.stringify(got[f]) !== JSON.stringify(expected[f])) {
      failures++;
      if (failures <= 10) console.error(`MISMATCH ${input.name}.${f}: js=${JSON.stringify(got[f])} py=${JSON.stringify(expected[f])}`);
    }
  }
}
console.log(`${cases.length} cases, ${failures} mismatches`);
process.exit(failures ? 1 : 0);
