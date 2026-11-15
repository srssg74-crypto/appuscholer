"use strict";
const C = require("./consistency.js"), S = require("./statsfind.js"), V = require("./dist_vectors.json");
let fails = 0;
function ok(c, m) { console.log((c ? "ok   " : "FAIL ") + m); if (!c) fails++; }
/* p-values against scipy (vectors made with scipy 1.18: t two-tailed, F and chi-square upper tail) */
let bad = 0;
V.forEach(r => {
  let got, want;
  if (r[0] === "t") { got = C.pT(r[2], r[1]); want = r[3]; } else if (r[0] === "F") { got = C.pF(r[3], r[1], r[2]); want = r[4]; } else { got = C.pChi2(r[2], r[1]); want = r[3]; }
  if (Math.abs(got - want) > 1e-12 && Math.abs(got - want) / Math.max(want, 1e-300) > 1e-9) bad++;
});
ok(bad === 0, V.length + " p-values agree with scipy (relative 1e-9 or absolute 1e-12); " + bad + " off");
const run = (t) => C.check([t], S.find([t]));
const st = (t) => { const r = run(t); return r.length ? r[0].status : "none"; };
ok(st("The groups differed, t(48) = 2.31, p = .025.") === "ok", "t(48) = 2.31, p = .025 is consistent (true p .0253)");
ok(st("t(48) = 2.31, p = .005") === "inconsistent", "p = .005 for t(48) = 2.31 is inconsistent");
ok(st("t(48) = 1.50, p = .03") === "decision", "a significant p for a t that gives .14 is a decision error");
ok(st("t(48) = 2.31, p < .05") === "ok" && st("t(48) = 2.31, p < .01") === "inconsistent", "bounds with < are checked");
ok(st("t(48) = 2.31, p > .05") === "decision", "p > .05 for a t that gives .025 is a decision error");
ok(st("F(2, 87) = 4.10, p = .020") === "ok", "F(2, 87) = 4.10, p = .020 is consistent");
ok(st("χ²(3) = 8.4, p = .04") === "ok", "chi-square(3) = 8.4, p = .04 is consistent (true .0385)");
ok(st("χ²(3) = 8.4, p = .40") === "decision" || st("χ²(3) = 8.4, p = .40") === "inconsistent", "chi-square with a wrong p is flagged");
ok(st("t(48) = 2.0, p = .051") === "ok", "rounding of t is allowed for (2.0 could be 1.95 to 2.05)");
ok(st("one-tailed test, t(48) = 1.80, p = .039") === "ok" && st("t(48) = 1.80, p = .039") === "decision", "one-tailed only when the page says so");
ok(st("t(48) = 2.31, p = .025") === "ok" && st("t(48) = 2.31, and a long stretch of other text goes on here for a good while, then p = .5") === "none", "a p far from the test is not paired with it");
ok(st("p = .03 and t(48) = 2.31") === "none", "a p before the test is not paired with it");
ok(st("t(48.5) = 2.31, p = .025") === "ok", "Welch (fractional) df works");
ok(run("t(48) = 2.31, p = .025. F(2, 87) = 4.10, p = .5").length === 2, "two tests in one text give two checks");
console.log(fails ? fails + " FAILED" : "ALL CONSISTENCY TESTS PASSED"); process.exit(fails ? 1 : 0);
