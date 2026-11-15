/* Printed page numbers for the Reading shelf.
   label(pages, edges) -> { confident, offset, same, votes, labels, how, notes }
   pages: one text string per PDF page (the shelf's extracted text, with line breaks).
   edges (optional): per page, the lines found in the top and bottom margins by position, from edgesOf(items, view); used when given.
   How it works: the first and last three lines of every page are searched for a number (alone on its line, or at the start or end of a
   running head or foot). Each number votes for "printed page = PDF page + offset". The offset with most pages behind it wins, and
   the label of every page is PDF page + offset. So a number the OCR misread ("200S", "lOlO") is put right, and a page whose number
   was not read gets it from its neighbours (only within one page of the first and last page where a number was seen).
   how[i]: "seen" (the page shows this number), "fixed" (the page shows something else that reads like a page number; the sequence wins),
   "inferred" (no number read on this page; taken from the sequence), "" (no label).
   confident is false when too few pages agree, or two offsets are nearly as common (for example a gazette with two numbering schemes).
   Roman numerals are not read. Nothing here reads the network. */
(function (root) {
  "use strict";
  var LOOK = { O: "0", o: "0", l: "1", I: "1", S: "5", B: "8" };
  function digits(tok) {
    var out = "", real = 0;
    for (var i = 0; i < tok.length; i++) {
      var c = tok.charAt(i);
      if (/[0-9]/.test(c)) { out += c; real++; } else if (LOOK[c]) out += LOOK[c]; else return null;
    }
    if (!real && tok.length < 3) return null;
    return out.length >= 1 && out.length <= 4 ? parseInt(out, 10) : null;
  }
  function candidates(text) {
    var lines = (Array.isArray(text) ? text : String(text || "").split(/\n/)).map(function (x) { return String(x).trim(); }).filter(Boolean);
    var pick = Array.isArray(text) ? lines : lines.slice(0, 3).concat(lines.slice(-3)), out = [];
    pick.forEach(function (ln) {
      var m = /^[\W_]*([0-9OolISB]{1,4})[\W_]*$/.exec(ln);
      if (m) { var v = digits(m[1]); if (v !== null && v > 0) out.push({ v: v, w: 2 }); return; }
      var a = /^(\d{1,4})\s+[A-Za-z]/.exec(ln), b = /[^\d\s]\s+(\d{1,4})$/.exec(ln);
      if (a) out.push({ v: parseInt(a[1], 10), w: 1 });
      if (b) out.push({ v: parseInt(b[1], 10), w: 1 });
    });
    return out;
  }
  /* Lines in the top and bottom margins of a page, found by position (pdf.js text items and the page view), top to bottom.
     This is better than the first and last lines of the text, because an OCR layer often lists text out of order. */
  function edgesOf(items, view) {
    var y0 = view[1], H = view[3] - view[1], rows = {};
    (items || []).forEach(function (it) {
      var s = it && typeof it.str === "string" ? it.str.trim() : "";
      if (!s || !it.transform) return;
      var rel = (it.transform[5] - y0) / H;
      if (rel > 0.12 && rel < 0.88) return;
      var k = Math.round(it.transform[5] / 4);
      (rows[k] || (rows[k] = { y: it.transform[5], p: [] })).p.push({ x: it.transform[4], s: s });
    });
    var lines = Object.keys(rows).map(function (k) { return rows[k]; }).sort(function (a, b) { return b.y - a.y; })
      .map(function (r) { return r.p.sort(function (a, b) { return a.x - b.x; }).map(function (q) { return q.s; }).join(" "); });
    return lines.slice(0, 3).concat(lines.length > 3 ? lines.slice(-3) : []);
  }
  function label(pages, edges) {
    var n = pages.length, notes = [], votes = {}, cand = [];
    for (var i = 0; i < n; i++) {
      cand[i] = candidates(edges && edges[i] && edges[i].length ? edges[i] : pages[i]);
      var seenOff = {};
      cand[i].forEach(function (c) { var o = c.v - (i + 1); if (!seenOff[o]) { seenOff[o] = 1; var e = votes[o] || (votes[o] = { w: 0, p: 0 }); e.w += c.w; e.p += 1; } });
    }
    var offs = Object.keys(votes).map(function (k) { return { o: parseInt(k, 10), w: votes[k].w, p: votes[k].p }; })
      .sort(function (a, b) { return b.w - a.w || b.p - a.p; });
    var res = { confident: false, offset: 0, same: false, votes: 0, labels: [], how: [], notes: notes };
    for (var z = 0; z < n; z++) { res.labels.push(""); res.how.push(""); }
    if (!offs.length) { notes.push("No printed page numbers were found."); return res; }
    var best = offs[0], second = offs[1];
    res.offset = best.o; res.votes = best.p;
    var need = n <= 4 ? 2 : Math.max(3, Math.ceil(n * 0.25));
    if (best.p < need) { notes.push("Too few pages agree on a numbering (" + best.p + " of " + n + ")."); return res; }
    if (second && second.p >= best.p * 0.8 && second.o !== best.o) { notes.push("Two page numberings are about equally common (offsets " + best.o + " and " + second.o + "), so none is used."); return res; }
    var first = -1, last = -1;
    for (var j = 0; j < n; j++) if (cand[j].some(function (c) { return c.v === j + 1 + best.o; })) { if (first < 0) first = j; last = j; }
    for (var k = 0; k < n; k++) {
      var exp = k + 1 + best.o;
      if (exp < 1) continue;
      var shows = cand[k].some(function (c) { return c.v === exp; });
      if (shows) { res.labels[k] = String(exp); res.how[k] = "seen"; }
      else if (cand[k].length && k >= first - 1 && k <= last + 1) { res.labels[k] = String(exp); res.how[k] = "fixed"; }
      else if (k >= first - 1 && k <= last + 1) { res.labels[k] = String(exp); res.how[k] = "inferred"; }
    }
    res.same = best.o === 0;
    res.confident = true;
    return res;
  }
  var api = { label: label, candidates: candidates, edgesOf: edgesOf };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.AppuPageNums = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
