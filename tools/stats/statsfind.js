/* Find reported statistics in a paper's page text: M and SD, t, F, chi-square, r, p, CI, effect sizes, n.
   Pure text patterns, no model. Every hit is a literal piece of the page text, so it can be shown beside the page and checked.
   find(pages) -> [{stat, text, page, at, v}] in page order; summarise(hits) -> counts by kind.
   A hit says "the paper prints this", never "this result is right". */
(function (root) {
  "use strict";
  var NUM = "(-?\\d*\\.?\\d+)";
  function norm(t) {
    return String(t || "").replace(/[   ]/g, " ").replace(/[−–—]/g, "-").replace(/≤/g, "<=").replace(/≥/g, ">=")
      .replace(/[χх]\s*[²2]/g, "chi2").replace(/χ²/g, "chi2");
  }
  var P = [
    ["p", new RegExp("\\bp\\s*(<=|>=|<|>|=)\\s*(\\d*\\.?\\d+(?:e-?\\d+)?)", "gi"), function (m) { return { op: m[1], p: +m[2] }; }],
    ["t", new RegExp("\\bt\\s*\\(\\s*(\\d+(?:\\.\\d+)?)\\s*\\)\\s*=\\s*" + NUM, "g"), function (m) { return { df: +m[1], t: +m[2] }; }],
    ["F", new RegExp("\\bF\\s*\\(\\s*(\\d+(?:\\.\\d+)?)\\s*,\\s*(\\d+(?:\\.\\d+)?)\\s*\\)\\s*=\\s*" + NUM, "g"), function (m) { return { df1: +m[1], df2: +m[2], F: +m[3] }; }],
    ["chi2", new RegExp("(?:chi2|chi-?square[d]?)\\s*\\(\\s*(\\d+)(?:\\s*,\\s*[nN]\\s*=\\s*[\\d,]+)?\\s*\\)\\s*=\\s*" + NUM, "gi"), function (m) { return { df: +m[1], chi2: +m[2] }; }],
    ["r", new RegExp("\\br\\s*(?:\\(\\s*\\d+\\s*\\))?\\s*=\\s*" + NUM, "g"), function (m) { return { r: +m[1] }; }],
    ["MSD", new RegExp("\\bM\\s*=\\s*" + NUM + "\\s*[,;]?\\s*SD\\s*=\\s*(\\d*\\.?\\d+)", "g"), function (m) { return { M: +m[1], SD: +m[2] }; }],
    ["MSD", new RegExp(NUM + "\\s*\\u00b1\\s*(\\d*\\.\\d+)", "g"), function (m) { return { M: +m[1], SD: +m[2] }; }],
    ["CI", new RegExp("(\\d{2})\\s*%\\s*(?:CI|confidence interval)\\s*[:=,]?\\s*[\\[(]?\\s*" + NUM + "\\s*(?:,|;|to|-)\\s*" + NUM + "\\s*[\\])]?", "gi"), function (m) { return { level: +m[1], lo: +m[2], hi: +m[3] }; }],
    ["ratio", new RegExp("\\b(OR|aOR|HR|aHR|RR|IRR|PR)\\s*(?:[=:]\\s*(\\d+\\.?\\d*)|(\\d+\\.\\d+))", "g"), function (m) { return { measure: m[1], value: +(m[2] || m[3]) }; }],
    ["effect", new RegExp("(?:\\u03b2|\\bd|\\u03b7p?2|\\bR2|\\u03c9|Cohen['\\u2019]s d|Cronbach['\\u2019]s \\u03b1|\\u03b1)\\s*=\\s*" + NUM, "g"), function (m) { return { value: +m[1] }; }],
    ["n", new RegExp("\\b[nN]\\s*=\\s*(\\d[\\d,]*)", "g"), function (m) { return { n: +m[1].replace(/,/g, "") }; }]
  ];
  function find(pages) {
    var hits = [];
    (pages || []).forEach(function (raw, pi) {
      var text = norm(raw), got = [];
      P.forEach(function (pat) {
        var re = new RegExp(pat[1].source, pat[1].flags), m;
        while ((m = re.exec(text))) {
          if (!m[0].length) { re.lastIndex++; continue; }
          var v = pat[2](m);
          if (pat[0] === "p" && !(v.p >= 0 && v.p <= 1)) continue;
          if (pat[0] === "r" && Math.abs(v.r) > 1) continue;
          if (pat[0] === "MSD" && (isNaN(v.M) || isNaN(v.SD))) continue;
          if (pat[0] === "CI" && (v.level < 50 || v.level > 99.9 || v.lo > v.hi)) continue;
          got.push({ stat: pat[0], text: m[0].replace(/\s+/g, " ").trim(), page: pi + 1, at: m.index, v: v, before: text.slice(Math.max(0, m.index - 60), m.index), after: text.slice(m.index + m[0].length, m.index + m[0].length + 100) });
        }
      });
      /* a longer hit swallows a shorter one that sits inside it (the n inside a chi-square, the number inside a CI) */
      got.sort(function (a, b) { return a.at - b.at || b.text.length - a.text.length; });
      var end = -1;
      got.forEach(function (h) { var e = h.at + h.text.length; if (h.at >= end || e > end + 0) { if (h.at < end) return; hits.push(h); end = Math.max(end, e); } });
    });
    return hits;
  }
  function summarise(hits) { var o = {}; hits.forEach(function (h) { o[h.stat] = (o[h.stat] || 0) + 1; }); return o; }
  var api = { find: find, summarise: summarise, norm: norm };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.AppuStats = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
