/* Tables of a research paper from the text items pdf.js gives (position of every piece of text). No model, no network.
   read(pages) -> { tables, hits, notes }
   tables: [{ num, caption, title, pages:[first,last], header:[...], rows:[[...]], joined }]   (a table that runs over two pages is one table)
   hits:   [{ stat:"MSD", text, page, table, v:{M,SD} }]   mean and SD read from the table's own columns
   A hit says what the table prints, not that it is right. A table drawn as a picture has no text and is not found. */
(function (root) {
  "use strict";
  var NUMRE = /^[-−–]?\.?\d[\d.,]*%?\*{0,3}$/;
  var PAIRRE = /^[-−–]?\.?\d[\d.,]*\s*[(\[]\s*[-−–]?\.?\d[\d.,]*\s*[)\]]\*{0,3}$/;
  var PMRE = /^[-−–]?\.?\d[\d.,]*\s*(?:±|\+\/-)\s*\.?\d[\d.,]*$/;
  function isNum(t) { t = String(t).trim(); return NUMRE.test(t) || PAIRRE.test(t) || PMRE.test(t); }
  function norm(t) { return String(t || "").replace(/[   ]/g, " ").replace(/\s+/g, " ").trim(); }
  function rowsOf(items) {
    var it = [];
    (items || []).forEach(function (x) {
      if (!x || typeof x.str !== "string" || !x.transform || !x.str.trim()) return;
      it.push({ s: x.str, x: x.transform[4], y: x.transform[5], w: x.width || 0, sz: Math.abs(x.transform[3]) || x.height || 9 });
    });
    it.sort(function (a, b) { return b.y - a.y || a.x - b.x; });
    var rows = [], cur = null;
    it.forEach(function (a) {
      if (!cur || Math.abs(a.y - cur.y) > Math.max(1.5, cur.sz * 0.45)) { cur = { y: a.y, sz: a.sz, its: [] }; rows.push(cur); }
      cur.its.push(a); cur.sz = Math.max(cur.sz, a.sz);
    });
    rows.forEach(function (r) {
      r.its.sort(function (a, b) { return a.x - b.x; });
      var cells = [], c = null;
      r.its.forEach(function (a) {
        if (c && a.x - c.x1 <= r.sz * 0.85) { c.t += (a.x - c.x1 > r.sz * 0.15 && !/\s$/.test(c.t) && !/^\s/.test(a.s) ? " " : "") + a.s; c.x1 = a.x + a.w; }
        else { c = { t: a.s, x0: a.x, x1: a.x + a.w }; cells.push(c); }
      });
      cells.forEach(function (c) { c.t = norm(c.t); });
      r.cells = cells.filter(function (c) { return c.t; });
      r.text = r.cells.map(function (c) { return c.t; }).join(" ");
    });
    return rows.filter(function (r) { return r.cells.length; });
  }
  var CAP = /^table\s+(\d+|[IVX]{1,5})\b\s*[.:]?\s*(.*)$/i;
  var PROSE = /^table\s+(\d+|[IVX]{1,5})\s+(shows?|presents?|summari[sz]es?|lists?|reports?|displays?|gives?|provides?|contains?|and|is|are|was|were|has|have|can|also|below|above)\b/i;
  function captionAt(rows, i) {
    var r = rows[i], m = CAP.exec(r.text);
    if (!m || r.text.length > 140 || PROSE.test(r.text)) return null;
    var multi = 0;
    for (var k = i + 1; k < Math.min(rows.length, i + 6); k++) if (rows[k].cells.length >= 3) multi++;
    if (multi < 2) return null;
    return { num: m[1], rest: norm(m[2]), cont: /\b(continued|cont\.?)\b/i.test(r.text) };
  }
  function stopRow(r) {
    if (r.cells.length >= 2) return false;
    var t = r.text;
    return /^(note|notes|source|sources|abbreviations?)\b/i.test(t) || /^[*†‡]/.test(t) || t.length >= 70 || CAP.test(t) || /^(figure|fig\.)\s*\d/i.test(t);
  }
  function region(rows, start) {
    var title = [], body = [], i = start, ended = true;
    while (i < rows.length && rows[i].cells.length < 2 && !stopRow(rows[i]) && title.length < 3) { title.push(rows[i].text); i++; }
    for (; i < rows.length; i++) {
      var r = rows[i], prev = body[body.length - 1];
      if (stopRow(r)) { ended = false; break; }
      if (prev && body.length >= 3 && prev.y - r.y > prev.sz * 4.2) { ended = false; break; }
      body.push(r);
    }
    return { title: title, body: body, ended: ended, end: i };
  }
  function columns(body) {
    var pts = [], firsts = [];
    body.forEach(function (r) { if (r.cells.length >= 2) { firsts.push(r.cells[0].x0); r.cells.slice(1).forEach(function (c) { pts.push((c.x0 + c.x1) / 2); }); } });
    if (!firsts.length) return null;
    var sz = body[0].sz, lab = Math.min.apply(null, firsts);
    pts.sort(function (a, b) { return a - b; });
    var cl = [];
    pts.forEach(function (p) { var c = cl[cl.length - 1]; if (c && p - c.hi <= sz * 1.6) { c.hi = p; c.sum += p; c.n++; } else cl.push({ lo: p, hi: p, sum: p, n: 1 }); });
    var cx = cl.map(function (c) { return c.sum / c.n; });
    return { lab: lab, cx: cx, sz: sz };
  }
  function grid(body, col) {
    return body.map(function (r) {
      var out = new Array(col.cx.length + 1).fill("");
      r.cells.forEach(function (c, k) {
        if (k === 0 && Math.abs(c.x0 - col.lab) <= col.sz * 1.5 && (r.cells.length >= 2 || true)) { out[0] = out[0] ? out[0] + " " + c.t : c.t; return; }
        var mid = (c.x0 + c.x1) / 2, best = 0, bd = 1e9;
        col.cx.forEach(function (x, j) { var d = Math.abs(x - mid); if (d < bd) { bd = d; best = j; } });
        out[best + 1] = out[best + 1] ? out[best + 1] + " " + c.t : c.t;
      });
      return out;
    });
  }
  function splitHeader(g) {
    var h = 0;
    for (var i = 0; i < g.length; i++) {
      var vals = g[i].slice(1).filter(function (v) { return v; }), nums = vals.filter(isNum).length;
      if (vals.length && nums >= Math.max(1, vals.length * 0.5)) break;
      h++;
    }
    h = Math.min(h, 3);
    var head = [];
    for (var c = 0; c < (g[0] || []).length; c++) head.push(norm(g.slice(0, h).map(function (r) { return r[c]; }).filter(Boolean).join(" ")));
    return { header: head, rows: g.slice(h) };
  }
  /* the number as printed (minus signs unified, stars removed) and its value; "3,7241" is a decimal comma, "1,250" a thousands comma */
  function shown(t) { return String(t).replace(/[\u2212\u2013\u2011]/g, "-").replace(/\*+$/, "").trim(); }
  function value(t) {
    var x = shown(t);
    if (/^-?\d{1,3}(,\d{3})+$/.test(x)) return +x.replace(/,/g, "");
    return +x.replace(",", ".");
  }
  function msd(tb) {
    var out = [], H = tb.header, R = tb.rows, descr = /descriptive|\bmeans?\b|\bSD\b|standard deviation/i.test(tb.caption + " " + tb.title);
    var mC = [], sdC = [], comb = [];
    H.forEach(function (h, c) {
      if (c === 0) return;
      var t = h.toLowerCase();
      if (/(^|\s)(m\s*\(\s*sd\s*\)|mean\s*\(\s*sd\s*\)|mean\s*\u00b1\s*sd|m\s*\u00b1\s*sd)/.test(t)) comb.push(c);
      else if (/(^|\s)(sd|s\.d\.|st\.?\s*dev\w*|std\.?\s*dev\w*|standard deviation|deviation)$/.test(t)) sdC.push(c);
      else if (/(^|\s)(m|mean|average)$/.test(t)) mC.push(c);
    });
    var last = "", grp = "";
    var ri = 0;
    function push(label, m, s, c) {
      var mv = value(m), sv = value(s);
      if (!label || isNaN(mv) || isNaN(sv) || sv < 0) return;
      out.push({ stat: "MSD", text: label + (H[c] ? ", " + H[c] : "") + ": M = " + shown(m) + ", SD = " + shown(s), table: tb.num, page: tb.rowPage[ri] || tb.pages[0], v: { M: mv, SD: sv } });
    }
    R.forEach(function (r, idx) {
      ri = idx;
      var only = r[0] && r.slice(1).every(function (v) { return !v; });
      if (only) { grp = norm(r[0]); return; }
      var only = r[0] && r.slice(1).every(function (v) { return !v; });
      if (only) { grp = norm(r[0]); return; }
      if (r[0]) last = norm(r[0]);
      var lead = [r[0] ? norm(r[0]) : last];
      for (var j = 1; j < r.length && r[j] && !isNum(r[j]) && lead.length < 2; j++) if (!/^[-\u2212\u2013\u2011]$/.test(r[j])) lead.push(norm(r[j]));
      var label = (grp && grp !== lead[0] ? grp + ", " : "") + lead.join(", ");
      mC.forEach(function (c) {
        var s = sdC.filter(function (x) { return x > c; })[0];
        if (s !== undefined && r[c] && r[s] && isNum(r[c]) && isNum(r[s])) push(label, r[c], r[s], c);
      });
      H.forEach(function (h, c) {
        if (c === 0 || !r[c]) return;
        var v = norm(r[c]), isComb = comb.indexOf(c) >= 0, pm = /^([-\u2212\u2013]?\.?\d[\d.,]*)\s*(?:\u00b1|\+\/-)\s*(\.?\d[\d.,]*)$/.exec(v);
        var pr = /^([-\u2212\u2013]?\.?\d[\d.,]*)\s*[(\[]\s*(\.?\d[\d.,]*)\s*[)\]]$/.exec(v);
        var m = isComb ? (pr || pm) : (descr ? pm : null);
        if (m) push(label, m[1], m[2], c);
      });
    });
    return out;
  }
  function read(pages) {
    var tables = [], notes = [], open = null, P = (pages || []).map(rowsOf);
    P.forEach(function (rows, pi) {
      var page = pi + 1, i = 0, usedTop = 0;
      /* a table that ran off the previous page and goes on here */
      if (open) {
        var k = 0;
        var oc = columns(open.parts[0].body), wide3 = oc && oc.cx.length >= 2;
        /* top of the page: single pieces of text, and a running head with a page number (two cells) when the table has three or more columns */
        while (k < rows.length && k < 3 && !CAP.test(rows[k].text) && (rows[k].cells.length < 2 || (wide3 && rows[k].cells.length === 2 && (/^\d{1,4}$/.test(rows[k].cells[1].t) || /^\d{1,4}$/.test(rows[k].cells[0].t))))) k++;
        var cap = k < rows.length ? CAP.exec(rows[k].text) : null, contCap = cap && cap[1] === open.num && /continued|cont\./i.test(rows[k].text);
        var from = contCap ? k + 1 : k, reg = region(rows, from), noCap = !cap;
        var wide = reg.body.length >= 2 && reg.body.some(function (r) { return r.cells.length >= 3; });
        if ((contCap || noCap) && wide) {
          open.parts.push({ page: page, body: reg.body });
          open.lastPage = page; usedTop = reg.end; i = reg.end;
          if (!reg.ended) { finish(open); open = null; } else if (!contCap && !noCap) { finish(open); open = null; }
        } else { finish(open); open = null; }
      }
      for (; i < rows.length; i++) {
        var c = captionAt(rows, i);
        if (!c || c.cont && !open) { if (!c) continue; }
        var reg2 = region(rows, i + 1);
        if (reg2.body.length < 2) continue;
        var t = { num: c.num, caption: "Table " + c.num + (c.rest ? ". " + c.rest : ""), title: reg2.title.join(" "), page: page, parts: [{ page: page, body: reg2.body }], lastPage: page };
        if (reg2.ended) { open = t; i = rows.length; } else { finish(t); i = reg2.end; }
      }
    });
    if (open) finish(open);
    function finish(t) {
      var cols = columns(t.parts[0].body);
      if (!cols) return;
      var all = [], pg = [];
      t.parts.forEach(function (p) { all = all.concat(p.body); p.body.forEach(function () { pg.push(p.page); }); });
      var g = grid(all, cols), sp = splitHeader(g), h = g.length - sp.rows.length;
      var rows = [], rp = [];
      var hd = sp.header.join("|");
      sp.rows.forEach(function (r, i) {
        if (t.parts.length > 1 && rows.length && r.join("|") === hd) return;   /* the header printed again at the top of the next page */
        rows.push(r); rp.push(pg[h + i]);
      });
      var tb = { num: t.num, caption: t.caption, title: t.title, pages: [t.page, t.lastPage], header: sp.header, rows: rows.slice(0, 150), rowPage: rp.slice(0, 150), joined: t.parts.length > 1 };
      tb.rows = tb.rows.map(function (r) { return r.map(function (c) { return c.length > 60 ? c.slice(0, 58) + "…" : c; }); });
      tables.push(tb);
    }
    var hits = [];
    tables.forEach(function (tb) { hits = hits.concat(msd(tb)); });
    return { tables: tables.slice(0, 40), hits: hits, notes: notes };
  }
  var api = { read: read, rowsOf: rowsOf, isNum: isNum };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.AppuTables = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
