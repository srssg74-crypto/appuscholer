/* Do the reported statistics agree with each other? A reported t, F, chi-square or r (with its degrees of freedom) fixes the p-value.
   check(pages, hits) -> [{ test, p, page, status, computed, range, note }]
   status: "ok", "inconsistent" (the printed p does not match the test statistic), "decision" (the mismatch changes whether p is below .05) or "adjusted" (the p is described as corrected, so a difference is expected).
   Allowed for: rounding of the test statistic and of p; one-tailed tests when the page says so. It checks what the paper prints against itself,
   not whether the analysis was right. A mismatch is a reason to look at the page, not proof of an error. */
(function (root) {
  "use strict";
  /* log-gamma (Lanczos) */
  function lg(x) {
    var g = 7, c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313, -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
    if (x < 0.5) return Math.log(Math.PI / Math.abs(Math.sin(Math.PI * x))) - lg(1 - x);
    x -= 1; var a = c[0], t = x + g + 0.5;
    for (var i = 1; i < g + 2; i++) a += c[i] / (x + i);
    return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
  }
  function betacf(a, b, x) {
    var qab = a + b, qap = a + 1, qam = a - 1, c = 1, d = 1 - qab * x / qap, FP = 1e-300;
    if (Math.abs(d) < FP) d = FP; d = 1 / d; var h = d;
    for (var m = 1; m <= 500; m++) {
      var m2 = 2 * m, aa = m * (b - m) * x / ((qam + m2) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < FP) d = FP; c = 1 + aa / c; if (Math.abs(c) < FP) c = FP; d = 1 / d; h *= d * c;
      aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
      d = 1 + aa * d; if (Math.abs(d) < FP) d = FP; c = 1 + aa / c; if (Math.abs(c) < FP) c = FP; d = 1 / d;
      var del = d * c; h *= del; if (Math.abs(del - 1) < 3e-16) break;
    }
    return h;
  }
  function ibeta(x, a, b) {
    if (x <= 0) return 0; if (x >= 1) return 1;
    var bt = Math.exp(lg(a + b) - lg(a) - lg(b) + a * Math.log(x) + b * Math.log(1 - x));
    return x < (a + 1) / (a + b + 2) ? bt * betacf(a, b, x) / a : 1 - bt * betacf(b, a, 1 - x) / b;
  }
  function gammaQ(a, x) {
    if (x <= 0) return 1;
    if (x < a + 1) {
      var ap = a, sum = 1 / a, del = sum;
      for (var n = 0; n < 1000; n++) { ap++; del *= x / ap; sum += del; if (Math.abs(del) < Math.abs(sum) * 3e-16) break; }
      return 1 - sum * Math.exp(-x + a * Math.log(x) - lg(a));
    }
    var b = x + 1 - a, c = 1 / 1e-300, d = 1 / b, h = d;
    for (var i = 1; i < 1000; i++) {
      var an = -i * (i - a); b += 2; d = an * d + b; if (Math.abs(d) < 1e-300) d = 1e-300; c = b + an / c; if (Math.abs(c) < 1e-300) c = 1e-300;
      d = 1 / d; var del2 = d * c; h *= del2; if (Math.abs(del2 - 1) < 3e-16) break;
    }
    return Math.exp(-x + a * Math.log(x) - lg(a)) * h;
  }
  function pT(t, df) { return ibeta(df / (df + t * t), df / 2, 0.5); }               /* two-tailed */
  function pF(F, d1, d2) { return F <= 0 ? 1 : ibeta(d2 / (d2 + d1 * F), d2 / 2, d1 / 2); }   /* upper tail */
  function pR(r, df) { r = Math.min(Math.abs(r), 1 - 1e-15); return pT(r * Math.sqrt(df / (1 - r * r)), df); }   /* two-tailed, from r and its df */
  function pChi2(x, df) { return gammaQ(df / 2, x / 2); }                             /* upper tail */
  function decimals(t) { var m = /\.(\d+)/.exec(t); return m ? m[1].length : 0; }
  function range(kind, v, dec) {
    var u = 0.5 * Math.pow(10, -dec), lo, hi;
    function f(x) { return kind === "t" ? pT(Math.abs(x), v.df) : kind === "F" ? pF(x, v.df1, v.df2) : kind === "r" ? pR(x, v.df) : pChi2(x, v.df); }
    var s = kind === "t" ? Math.abs(v.t) : kind === "F" ? v.F : kind === "r" ? Math.abs(v.r) : v.chi2;
    if (kind === "r") { var ra = f(Math.min(1, s + u)), rb = f(Math.max(0, s - u)); return [Math.min(ra, rb), Math.max(ra, rb)]; }
    var a = f(Math.max(0, s - u)), b = f(s + u);
    return [Math.min(a, b), Math.max(a, b)];
  }
  function check(pages, hits) {
    var out = [], text = (pages || []).map(function (t) { return String(t || "").toLowerCase(); });
    var by = {}; hits.forEach(function (h) { (by[h.page] = by[h.page] || []).push(h); });
    Object.keys(by).forEach(function (pg) {
      var hs = by[pg].slice().sort(function (a, b) { return a.at - b.at; });
      hs.forEach(function (h, i) {
        if (h.stat !== "t" && h.stat !== "F" && h.stat !== "chi2" && !(h.stat === "r" && h.v.df > 0)) return;
        var n = hs[i + 1];
        if (!n || n.stat !== "p") return;
        var gap = n.at - (h.at + h.text.length);
        if (gap < 0 || gap > 60) return;
        var v = h.v;
        if (h.stat === "t" && !(v.df > 0) || h.stat === "F" && !(v.df1 > 0 && v.df2 > 0) || h.stat === "chi2" && !(v.df > 0) || h.stat === "r" && !(v.df > 0)) return;
        var dec = decimals(h.text), r = range(h.stat, v, dec), pdec = decimals(n.text.replace(/^p\s*(<=|>=|<|>|=)\s*/i, ""));
        var one = /one[- ]?(tailed|sided)|1-tailed/.test(text[pg - 1] || "");
        var cands = [r]; if (one && (h.stat === "t" || h.stat === "r")) cands.push([r[0] / 2, r[1] / 2]);
        var rep = n.v.p, op = n.v.op, ph = 0.5 * Math.pow(10, -pdec), good = false, note = "";
        cands.forEach(function (c) {
          /* "=" : the printed p is the rounded value, or the value cut off after its last decimal (.0289 printed as .02) */
          if (op === "=") good = good || (c[1] >= rep - ph - 1e-12 && c[0] < rep + 2 * ph + 1e-12);
          else if (op === "<") good = good || c[0] < rep;
          else if (op === "<=") good = good || c[0] <= rep + 1e-12;
          else if (op === ">") good = good || c[1] > rep;
          else if (op === ">=") good = good || c[1] >= rep - 1e-12;
        });
        var mid = (r[0] + r[1]) / 2, status = "ok";
        var win = ((n.after || "").slice(0, 100) + " " + (h.before || "").slice(-40)).replace(/\bR\s?(?:2|\u00b2)\s*adj\w*|\badj\w*\s*R\s?(?:2|\u00b2)/gi, ""), adj = /adjust|correct|bonferroni|holm|benjamini|\bfdr\b|greenhouse|geisser/i.test(win);
        if (!good && op === "=" && pdec >= 3 && Math.abs(rep - Math.pow(10, -pdec)) < 1e-12 && r[1] < rep) { good = true; note = "Printed as the smallest value; the test statistic gives p below that. Write p < .001."; }
        if (!good && op === "=" && rep === 0 && r[1] < 0.0005) { good = true; note = "p = .000 is printed; write p < .001."; }
        if (!good) {
          var sigComp = r[1] < 0.05, nonComp = r[0] >= 0.05;
          var repSig = (op === "=" && rep < 0.05) || ((op === "<" || op === "<=") && rep <= 0.05);
          var repNon = (op === "=" && rep >= 0.05) || ((op === ">" || op === ">=") && rep >= 0.05);
          status = adj ? "adjusted" : ((repSig && nonComp) || (repNon && sigComp)) ? "decision" : "inconsistent";
          note = adj ? "The printed p is described as adjusted, so it can differ from the raw p of the test statistic." : "The test statistic gives p about " + (mid < 0.001 ? "< .001" : mid.toFixed(3).replace(/^0/, ""));
        }
        out.push({ test: h.text, p: n.text, page: +pg, status: status, computed: mid, range: r, note: note });
      });
    });
    return out;
  }
  /* An estimate with its confidence interval and a p-value: the estimate must lie inside its interval, and the interval and p must agree
     about significance (a 95% interval that excludes 1 for a ratio, or 0 for beta and d, goes with p below .05). */
  function checkCI(pages, hits) {
    var out = [], by = {};
    hits.forEach(function (h) { (by[h.page] = by[h.page] || []).push(h); });
    Object.keys(by).forEach(function (pg) {
      var hs = by[pg].slice().sort(function (a, b) { return a.at - b.at; });
      hs.forEach(function (h, i) {
        var ratio = h.stat === "ratio", eff = h.stat === "effect" && /^(\u03b2|d\b|cohen)/i.test(h.text);
        if (!ratio && !eff) return;
        var c = hs[i + 1];
        if (!c || c.stat !== "CI" || c.at - (h.at + h.text.length) > 40 || c.at < h.at) return;
        var est = ratio ? h.v.value : h.v.value, lo = c.v.lo, hi = c.v.hi, dec = Math.max(decimals(c.text), decimals(h.text)), u = 0.5 * Math.pow(10, -dec) + 1e-12;
        var nul = ratio ? 1 : 0, pp = hs[i + 2], res = { test: h.text + ", " + c.text, p: "", page: +pg, status: "ok", computed: null, range: null, note: "", kind: "ci" };
        if (est < lo - u || est > hi + u) { res.status = "inconsistent"; res.note = "The estimate is outside its own confidence interval."; out.push(res); return; }
        if (pp && pp.stat === "p" && pp.at - (c.at + c.text.length) <= 70 && pp.at >= c.at) {
          var alpha = 1 - c.v.level / 100, op = pp.v.op, rep = pp.v.p, ph = 0.5 * Math.pow(10, -decimals(pp.text.replace(/^p\s*(<=|>=|<|>|=)\s*/i, "")));
          res.p = pp.text;
          var excl = lo > nul + u || hi < nul - u, incl = lo < nul - u && hi > nul + u;
          var repSig = ((op === "=" && rep + ph <= alpha + 1e-12) || ((op === "<" || op === "<=") && rep <= alpha + 1e-12)), repNon = ((op === "=" && rep - ph >= alpha - 1e-12) || ((op === ">" || op === ">=") && rep >= alpha - 1e-12));
          if ((excl && repNon) || (incl && repSig)) { res.status = "decision"; res.note = "The " + c.v.level + "% interval " + (excl ? "excludes " : "includes ") + nul + ", which goes with p " + (excl ? "below " : "above ") + alpha.toFixed(2).replace(/^0/, "") + "."; }
        }
        out.push(res);
      });
    });
    return out;
  }
  var api = { check: check, checkCI: checkCI, pT: pT, pF: pF, pChi2: pChi2, pR: pR };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.AppuConsistency = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
