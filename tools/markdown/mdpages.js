/* Markdown from an OCR or conversion tool -> pages and sections for the Reading shelf.
   parse(md, kindOf) -> { pages, sections, how, title, notes }
   how: "markers" (the file marks its pages), "formfeed" (page breaks), "none" (no page numbers in the file; the text is cut into parts).
   Page markers understood: <!-- page 3 -->, --- Page 3 ---, [Page 3], # Page 3, {2}------ (zero-based, as some converters print), form feed.
   Nothing here reads the network. kindOf(title) is optional and names a heading's kind (abstract, methods ...). */
(function (root) {
  "use strict";
  var MAXP = 2000, PART = 3000;
  var MARK = [
    [/^\s*<!--\s*page[\s:_-]*(\d+)(?:\s*(?:of|\/)\s*\d+)?\s*-->\s*$/i, 0],
    [/^\s*[-=_*]{2,}\s*page\s*(\d+)(?:\s*(?:of|\/)\s*\d+)?\s*[-=_*]{2,}\s*$/i, 0],
    [/^\s*\[\s*page\s*(\d+)(?:\s*(?:of|\/)\s*\d+)?\s*\]\s*$/i, 0],
    [/^\s*#{1,6}\s*page\s*(\d+)(?:\s*(?:of|\/)\s*\d+)?\s*$/i, 0],
    [/^\s*\{(\d+)\}\s*-{8,}\s*$/, 1]
  ];
  function markerOf(line) {
    for (var i = 0; i < MARK.length; i++) { var m = MARK[i][0].exec(line); if (m) return +m[1] + MARK[i][1]; }
    return 0;
  }
  function clean(t) {
    return String(t)
      .replace(/<!--[\s\S]*?-->/g, "")
      .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
      .replace(/\[([^\]]+)\]\((?:[^)]*)\)/g, "$1")
      .replace(/<\/?[a-zA-Z][^>]*>/g, "")
      .replace(/\*\*|__/g, "")
      .replace(/`/g, "")
      .replace(/[ \t]+$/gm, "");
  }
  function splitPages(md) {
    var lines = md.split(/\r?\n/), marked = [], seq = true, last = 0, any = false;
    var cur = { n: 0, lines: [] }, parts = [cur];
    lines.forEach(function (ln) {
      var n = markerOf(ln);
      if (n) { any = true; if (n <= last) seq = false; last = n; cur = { n: n, lines: [] }; parts.push(cur); }
      else cur.lines.push(ln);
    });
    if (any && seq) {
      var pages = [];
      parts.forEach(function (p) {
        if (!p.n) { if (p.lines.join("").trim()) { pages[0] = (pages[0] || "") + p.lines.join("\n"); } return; }
        if (p.n > MAXP) return;
        pages[p.n - 1] = (pages[p.n - 1] || "") + p.lines.join("\n");
      });
      for (var i = 0; i < pages.length; i++) if (pages[i] === undefined) pages[i] = "";
      return { pages: pages, how: "markers" };
    }
    if (md.indexOf("\f") >= 0) return { pages: md.split("\f").slice(0, MAXP), how: "formfeed" };
    return { pages: cut(md.replace(/<!--\s*page[^>]*-->/gi, "")), how: "none" };
  }
  function cut(md) {
    var paras = md.split(/\n\s*\n/), out = [], buf = "";
    paras.forEach(function (p) { if (buf.length + p.length > PART && buf) { out.push(buf); buf = ""; } buf += (buf ? "\n\n" : "") + p; });
    if (buf) out.push(buf);
    return out.slice(0, MAXP);
  }
  function parse(md, kindOf) {
    md = String(md || "").replace(/^﻿/, "");
    var sp = splitPages(md), heads = [];
    sp.pages.forEach(function (pg, i) {
      String(pg).split("\n").forEach(function (ln) {
        var m = /^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$/.exec(ln);
        if (m) heads.push({ level: m[1].length, title: clean(m[2]).replace(/\s+/g, " ").trim(), page: i + 1 });
      });
    });
    heads = heads.filter(function (h) { return h.title && !/^page\s*\d+/i.test(h.title); });
    var l1 = heads.filter(function (h) { return h.level === 1; }).length, l2 = heads.filter(function (h) { return h.level === 2; }).length;
    var top = (l1 === 1 && l2 >= 2) ? 2 : (heads.length ? Math.min.apply(null, heads.map(function (h) { return h.level; })) : 1);
    var title = "";
    if (l1 === 1 && l2 >= 2) title = heads.filter(function (h) { return h.level === 1; })[0].title;
    var sections = [], cur = null;
    heads.forEach(function (h) {
      if (h.level < top) return;
      if (h.level === top) {
        var k = "other"; try { if (kindOf) k = kindOf(h.title) || "other"; } catch (e) {}
        cur = { kind: k, title: h.title, page: h.page, subs: [] }; sections.push(cur);
      } else if (cur && cur.subs.length < 40) cur.subs.push({ title: h.title, page: h.page });
    });
    var pages = sp.pages.map(function (pg) { return clean(String(pg).replace(/^\s{0,3}#{1,6}\s+/gm, "")).replace(/\n{3,}/g, "\n\n").trim(); });
    var notes = [];
    if (sp.how === "none") notes.push("This file has no page numbers. The text is cut into parts of about 3,000 characters; a part number is not a printed page.");
    if (sp.how === "markers" && pages.some(function (p) { return !p; })) notes.push("Some pages in the file are empty.");
    return { pages: pages, sections: sections.slice(0, 60), how: sp.how, title: title, notes: notes };
  }
  var api = { parse: parse, markerOf: markerOf };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.AppuMd = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
