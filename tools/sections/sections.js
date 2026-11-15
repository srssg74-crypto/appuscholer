/* Section detection for research-paper PDFs, from pdf.js text items. No model, no network.

   Input: an array with one entry per page, each entry the `items` array of pdf.js getTextContent()
   (objects with str, transform, width, height, fontName, hasEOL).
   Output: { body, lines, headings, sections, notes }.

   Idea (borrowed from how document parsers treat a paper as one thing, not 12 separate pages): the
   body-text size and font are decided once for the whole paper. A heading is then a short line that
   stands apart from that body: larger, or in a font used for little else, or a numbered or well-known
   section name. Levels come from the sizes found, not from a fixed table.

   pdf.js gives items in reading order (checked on 15 papers on 8 Nov 2026), so lines are built by walking
   the items in that order and never by sorting on y, which would merge the two columns. */
(function (root) {
  "use strict";

  var NAMES = [
    ["abstract", /^(structured\s+)?abstract$|^summary$/i],
    ["keywords", /^key\s*words?(\s+and\s+phrases)?$|^index terms$/i],
    ["introduction", /^(introduction|background|background and (aims?|objectives?|rationale)|literature review|theoretical (background|framework)|review of (the )?literature|rationale)$/i],
    ["methods", /^(methods?|materials? and methods?|methodology|methods? and materials?|study design|research design|design and methods?|participants?( and procedure)?|procedure|measures?|instruments?|materials?|data analysis|statistical analysis|study population|sample|setting|patients and methods|subjects and methods|experimental (design|procedure))$/i],
    ["results", /^(results?( and (discussion|analysis))?|findings|outcomes?|main results|statistical results)$/i],
    ["discussion", /^(discussion( and conclusions?)?|general discussion|interpretation)$/i],
    ["limitations", /^(limitations?( and future (research|directions|work))?|strengths and limitations|study limitations)$/i],
    ["conclusion", /^(conclusions?( and (implications|recommendations))?|concluding remarks|implications|practical implications|future (research|directions|work))$/i],
    ["references", /^(references?|bibliography|literature cited|works cited|reference list)$/i],
    ["backmatter", /^(acknowledge?ments?|funding|financial support|declarations?( of (conflicting|competing) interests?)?|conflicts? of interest|orcid( ids?)?|open access|notes?|corresponding author|competing interests?|disclosure statement|author contributions?|authors?'? contributions?|ethics( approval| statement)?( and consent( to participate)?)?|ethical considerations|data availability( statement)?|availability of data and materials?|supplementary (material|information)|supporting information|abbreviations|publisher'?s note|additional files?|consent for publication|appendix|appendices)$/i]
  ];

  function clean(s) {
    return String(s || "").replace(/[­​]/g, "").replace(/\s+/g, " ").trim();
  }
  /* "2.1. Participants", "II. METHOD", "3 Results" -> the name part and the depth of the number */
  function splitNumber(t) {
    var m = /^((?:\d{1,2}(?:\.\d{1,2}){0,3}|[IVX]{1,5}|[A-H])[.)]?)(?:\s*\|\s*|\s+)(\p{L}.*)$/u.exec(t);
    if (!m) return { num: "", depth: 0, name: t };
    var num = m[1].replace(/[.)]$/, ""), depth = /^\d/.test(num) ? num.split(".").length : 1;
    return { num: num, depth: depth, name: m[2] };
  }
  /* Some publishers set headings in letter-spaced capitals, and extraction breaks them into odd pieces
     ("RE SU LT S", "REFERENC ES"). A space-free copy of each pattern is tried on the space-free text. */
  NAMES.forEach(function (n) { n.push(new RegExp(n[1].source.replace(/\\s[+*]/g, "").replace(/ /g, ""), "i")); });
  function kindOf(name, numbered) {
    if (!numbered && /\.$/.test(name)) return "";   // "sample." ends a sentence; a numbered "2. Methods." may keep its stop
    var n = name.replace(/[:.—–-]+$/, "").trim();
    for (var i = 0; i < NAMES.length; i++) if (NAMES[i][1].test(n)) return NAMES[i][0];
    if (/^[A-Z0-9 ]+$/.test(n) && /(^| )[A-Z0-9]{1,2}( |$)/.test(n)) {
      var c = n.replace(/\s+/g, "");
      for (var j = 0; j < NAMES.length; j++) if (NAMES[j][2].test(c)) return NAMES[j][0];
    }
    return "";
  }

  function buildLines(pages) {
    var lines = [];
    pages.forEach(function (items, pi) {
      var cur = null;
      function flush() { if (cur && clean(cur.text)) lines.push(cur); cur = null; }
      (items || []).forEach(function (it) {
        if (!it || typeof it.str !== "string" || !it.transform) return;
        var size = Math.abs(it.transform[3]) || it.height || 0, x = it.transform[4], y = it.transform[5];
        if (!it.str.trim()) { if (it.hasEOL) flush(); return; }
        var sameLine = cur && Math.abs(y - cur.y) < Math.max(1.2, cur.size * 0.35) && x >= cur.xEnd - cur.size * 0.5 && x - cur.xEnd < cur.size * 2.2;
        if (!sameLine) {
          flush();
          cur = { page: pi + 1, text: "", size: size, y: y, x: x, xEnd: x, fonts: {}, chars: 0 };
        }
        cur.text += (cur.text && !/\s$/.test(cur.text) && !/^\s/.test(it.str) && x - cur.xEnd > cur.size * 0.15 ? " " : "") + it.str;
        cur.xEnd = x + (it.width || 0);
        cur.size = Math.max(cur.size * 0.0 + size, cur.size);
        var f = it.fontName || "?", n = it.str.length;
        cur.fonts[f] = (cur.fonts[f] || 0) + n; cur.chars += n;
        if (it.hasEOL) flush();
      });
      flush();
    });
    lines.forEach(function (l) {
      l.text = clean(l.text);
      var best = "", bn = -1;
      Object.keys(l.fonts).forEach(function (f) { if (l.fonts[f] > bn) { bn = l.fonts[f]; best = f; } });
      l.font = best;
    });
    return lines;
  }

  function bodyStyle(lines) {
    var bySize = {}, byFont = {};
    lines.forEach(function (l) {
      if (l.chars < 30) return;
      var k = Math.round(l.size * 2) / 2;
      bySize[k] = (bySize[k] || 0) + l.chars;
      byFont[l.font] = (byFont[l.font] || 0) + l.chars;
    });
    var size = 0, sn = -1, font = "", fn = -1;
    Object.keys(bySize).forEach(function (k) { if (bySize[k] > sn) { sn = bySize[k]; size = +k; } });
    Object.keys(byFont).forEach(function (k) { if (byFont[k] > fn) { fn = byFont[k]; font = k; } });
    var total = lines.reduce(function (a, l) { return a + l.chars; }, 0) || 1;
    return { size: size, font: font, fontShare: {}, total: total, byFont: byFont };
  }

  /* lines that repeat on three or more pages are running heads or feet, never headings */
  function repeated(lines, nPages) {
    var seen = {};
    lines.forEach(function (l) {
      var k = l.text.toLowerCase().replace(/[^a-z]+/g, "");
      if (!k) return;
      seen[k] = seen[k] || {};
      seen[k][l.page] = 1;
    });
    var need = Math.max(3, Math.ceil(nPages * 0.25)), out = {};
    Object.keys(seen).forEach(function (k) { if (Object.keys(seen[k]).length >= need) out[k] = 1; });
    return out;
  }

  function detect(pages) {
    var notes = [], lines = buildLines(pages), nPages = pages.length;
    if (!lines.length) return { body: null, lines: [], headings: [], sections: [], notes: ["no text"] };
    var body = bodyStyle(lines), rep = repeated(lines, nPages);
    var textChars = lines.reduce(function (a, l) { return a + (rep[l.text.toLowerCase().replace(/[^a-z]+/g, "")] ? 0 : l.chars); }, 0);
    if (textChars / nPages < 400) notes.push("little or no text layer: a scan or a page printed as images, OCR is needed");
    var fontUse = body.byFont, totalChars = body.total;
    var heads = [], MAIN = { abstract: 1, keywords: 1, introduction: 1, methods: 1, results: 1, discussion: 1, conclusion: 1, references: 1 };
    var frontDone = false, inRefs = false;
    function balanced(t) { return (t.split("(").length === t.split(")").length) && (t.split("[").length === t.split("]").length); }
    lines.forEach(function (l, i) {
      var t = l.text;
      if (t.length < 3 || t.length > 110) return;
      var key = t.toLowerCase().replace(/[^a-z]+/g, "");
      if (rep[key]) return;
      var sp = splitNumber(t), kind = kindOf(sp.name, !!sp.num);
      if (/^[a-z]/.test(sp.name) || /^[^\p{L}\p{N}]/u.test(sp.name)) return;   // headings do not start in lower case or with a symbol
      if (/^(table|fig\.?|figure|box|panel)\s*\d/i.test(t)) return;     // captions
      if (/^[\d\s.,()\[\]\u00b1%<>=-]+$/.test(t)) return;              // numbers only
      var bigger = l.size >= body.size * 1.12;
      var smaller = l.size < body.size * 0.97;                           // table cells, footnotes, address blocks
      var rareFont = l.font !== body.font && (fontUse[l.font] || 0) / totalChars < 0.12;
      var words = sp.name.split(/\s+/).length;
      var endsSentence = /[.!?;,]$/.test(sp.name) && !kind;
      var looksLikeProse = /\b(was|were|is|are|has|have|had|et al|yielded|showed)\b/i.test(sp.name) && words > 5;
      var lowerStart = /^[a-z]/.test(sp.name);
      if (kind === "abstract" || kind === "introduction" || kind === "keywords" || kind === "methods" && sp.num) frontDone = true;
      if (kind === "references") { inRefs = true; }
      else if (inRefs && kind !== "backmatter") return;                   // reference entries are never headings
      if (!kind && (/[=+\u00b1<>]/.test(sp.name) || /-$/.test(sp.name))) return;     // table headers, hyphenated line ends
      if (!kind && sp.num && !/\./.test(sp.num) && words > 8) return;               // "1. The study sample consisted of..." list items
      var ok = false;
      if (kind) {
        ok = (sp.num || bigger || rareFont || /^[A-Z0-9 \u2014\u2013:-]+$/.test(sp.name) || !smaller) && !(smaller && !sp.num && !(rareFont && t.length < 24));
        if (ok && !bigger && !rareFont && !sp.num && l.text.length > 40) ok = false;
      } else if (frontDone && !smaller && balanced(t) && !endsSentence && !looksLikeProse && !lowerStart && words <= 14) {
        ok = bigger || (rareFont && (sp.num || words <= 8)) || (sp.num && sp.depth >= 2 && words <= 12);
      } else if (sp.num && sp.depth >= 1 && !smaller && balanced(t) && !endsSentence && !looksLikeProse && !lowerStart && words <= 14 && /^\d/.test(sp.num)) {
        ok = true;
      }
      if (ok && heads.length && heads[heads.length - 1].raw === t && heads[heads.length - 1].page === l.page) ok = false;
      var shown = sp.name.replace(/[:.\u2014\u2013-]+$/, "").trim();
      if (kind && /^[A-Z0-9 ]+$/.test(shown) && /(^| )[A-Z0-9]{1,2}( |$)/.test(shown)) shown = shown.replace(/\s+/g, "");
      if (ok) heads.push({ idx: i, text: shown, num: sp.num, depth: sp.depth, kind: kind, size: l.size, font: l.font, page: l.page, y: l.y, raw: t });
    });
    /* a long heading wraps onto a second line of the same size and font; join the pieces */
    var CONN = /\b(of|and|the|in|to|with|among|for|on|at|by|from|a|an|or|between|during|after|before)$/i;
    var merged = [];
    heads.forEach(function (h) {
      var prev = merged[merged.length - 1];
      if (prev && h.idx === prev.lastIdx + 1 && h.font === prev.font && Math.abs(h.size - prev.size) < 0.3 && !h.num && !h.kind && !prev.kind &&
          (CONN.test(prev.text) || (prev.num && prev.text.split(/\s+/).length >= 4 && !/[.!?]$/.test(prev.text)))) {
        prev.text += " " + h.text; prev.raw += " " + h.raw; prev.lastIdx = h.idx; return;
      }
      h.lastIdx = h.idx; merged.push(h);
    });
    heads = merged;
    /* the same numbered heading met again later (a running head set a little smaller) is dropped */
    var seenNum = {};
    heads = heads.filter(function (h) { if (!h.num) return true; var k = h.num + "|" + h.text.toLowerCase(); if (seenNum[k]) return false; seenNum[k] = 1; return true; });
    /* an Abstract with no heading of its own: leave it; the first heading decides. The title is the largest line on page 1. */
    var title = "", ts = 0, titleIdx = [];
    lines.forEach(function (l) { if (l.page === 1 && l.size > ts && l.text.length > 8 && l.text.length < 220 && !rep[l.text.toLowerCase().replace(/[^a-z]+/g, "")]) ts = l.size; });
    lines.forEach(function (l, i) { if (l.page === 1 && Math.abs(l.size - ts) < 0.6 && l.text.length > 3 && l.text.length < 220) { title += (title ? " " : "") + l.text; titleIdx.push(i); } });
    title = title.replace(/-\s+/g, "-").slice(0, 300);
    /* levels: numbered headings use their depth; others rank by size among the sizes seen for headings */
    var mainSizes = heads.filter(function (h) { return MAIN[h.kind]; }).map(function (h) { return h.size; });
    var ref = mainSizes.length ? mainSizes.sort(function (x, y) { return x - y; })[Math.floor(mainSizes.length / 2)] : body.size;
    heads.forEach(function (h) {
      if (h.num) h.level = Math.min(3, h.depth);
      else if (MAIN[h.kind]) h.level = 1;
      else if (h.size > ref + 0.6) h.level = 1;
      else if (h.size >= ref - 0.6) h.level = 2;
      else h.level = 3;
    });
    /* the title line itself can pass as a heading; drop it */
    heads = heads.filter(function (h) { return !(h.page === 1 && titleIdx.indexOf(h.idx) >= 0); });

    /* A structured abstract repeats Background / Methods / Results / Conclusions before the real Introduction.
       Those belong to the abstract. */
    var ai = -1, ii = -1;
    heads.forEach(function (h, k) { if (ai < 0 && h.kind === "abstract") ai = k; });
    if (ai >= 0) for (var q = ai + 1; q < heads.length; q++) if (/^introduction$/i.test(heads[q].text)) { ii = q; break; }
    if (ai >= 0 && ii > ai) for (var q2 = ai + 1; q2 < ii; q2++) if (heads[q2].kind !== "keywords") { heads[q2].kind = "abstract"; heads[q2].level = 2; heads[q2].abstractPart = true; }
    /* "Ethics" inside the Methods is a Methods subsection; only after the Discussion is it back matter */
    var seenMain = {};
    heads.forEach(function (h) {
      if (MAIN[h.kind]) seenMain[h.kind] = 1;
      if (h.kind === "backmatter" && /^ethic/i.test(h.text) && seenMain.methods && !seenMain.discussion && !seenMain.conclusion) { h.kind = "methods"; h.level = 2; }
    });
    var sections = [], cur = null, inRefs = false;
    for (var i = 0; i < heads.length; i++) {
      var h = heads[i], nextIdx = i + 1 < heads.length ? heads[i + 1].idx : lines.length;
      var kind = h.kind;
      if (kind === "references") inRefs = true;
      else if (kind && kind !== "backmatter") inRefs = false;
      /* a numbered subheading takes the kind of its parent: "2.1 Participants" is Methods */
      if (!kind && cur && h.level >= 2) kind = cur.kind;
      if (h.abstractPart) { if (cur && cur.kind === "abstract") cur.subs.push({ title: h.text, page: h.page }); continue; }
      var TOP = /^(methods?|materials? and methods?|methods? and materials?|methodology|patients and methods|subjects and methods|design and methods?|results?( and (discussion|analysis))?|findings|introduction|background|discussion|conclusions?)$/i;
      var isSub = cur && ((h.num && h.depth >= 2) || (kind && kind === cur.kind && !TOP.test(h.text) && h.kind !== "references"));
      if (isSub) { cur.subs.push({ title: h.text, page: h.page }); cur.to = nextIdx; continue; }
      if (h.level <= 1 || h.kind || !cur) {
        cur = { kind: kind || "other", title: h.text, page: h.page, level: h.level, from: h.idx, to: nextIdx, subs: [] };
        sections.push(cur);
      } else {
        cur.subs.push({ title: h.text, page: h.page });
        cur.to = nextIdx;
      }
    }
    return { body: { size: body.size, font: body.font }, title: title, lines: lines, headings: heads, sections: sections, notes: notes };
  }

  var api = { detect: detect, buildLines: buildLines, kindOf: function (t) { var sp = splitNumber(t); return kindOf(sp.name, !!sp.num); }, splitNumber: splitNumber };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.AppuSections = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
