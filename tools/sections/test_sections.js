"use strict";
const S = require("./sections.js");
let fails = 0;
function check(label, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if (!ok) { fails++; console.log("FAIL " + label + "\n  got  " + JSON.stringify(got) + "\n  want " + JSON.stringify(want)); } else console.log("ok   " + label);
}
/* a line of text as pdf.js would give it: one item, size in the transform, font name, position */
function L(str, y, o) { o = o || {}; const size = o.size || 10; return { str: str, transform: [size, 0, 0, size, o.x || 72, y], width: str.length * size * 0.5, height: size, fontName: o.font || "body", hasEOL: true }; }
const BODY = "Participants were students from three colleges and completed the scale twice, a week apart, in class.";
function page(extra, n) {
  const items = [L("Journal of Test Psychology", 780, { size: 8, font: "run" })];
  extra.forEach(function (e) { items.push(e); });
  items.push(L(String(n), 30, { size: 8, font: "run" }));
  return items;
}
function filler(y0, n) { const a = []; for (let i = 0; i < n; i++) a.push(L(BODY, y0 - i * 12)); return a; }
const H = { size: 13, font: "head" };

const pages = [
  page([L("Sleep and Exam Anxiety in First-Year Students", 740, { size: 18, font: "head" }), L("A. Rao and B. Sen", 715, {}), L("Abstract", 690, H),
    L("Background", 670, { font: "head" }), L(BODY, 658), L("Methods", 640, { font: "head" }), L(BODY, 628), ...filler(600, 6),
    L("1. Introduction", 500, H), ...filler(480, 8)], 1),
  page([...filler(740, 5), L("2. Methods", 680, H), L("2.1. Participants", 660, { font: "head" }), ...filler(640, 4),
    L("Table 1. Sample characteristics", 560, { size: 9 }), L("M ± SD", 545, { size: 8, font: "tbl" }), L("Group", 535, { size: 8, font: "tbl" }), ...filler(500, 6)], 2),
  page([L("3. Results", 740, H), ...filler(720, 6), L("(see Table 2)", 640, {}), L("results were mixed.", 628, { font: "head" }), L("4. Discussion", 560, H), ...filler(540, 4),
    L("References", 450, H), L("Smith, J. (2020). Sleep and learning. Journal of Sleep, 4, 1-9.", 430, { size: 9, font: "head" }), L("Jones, K. (2019). Anxiety. Journal of Mind, 2, 3-8.", 418, { size: 9, font: "head" })], 3)
];
const r = S.detect(pages);
check("title is the largest line on page 1", r.title, "Sleep and Exam Anxiety in First-Year Students");
check("main sections found in order", r.sections.map(s => s.kind), ["abstract", "introduction", "methods", "results", "discussion", "references"]);
check("structured-abstract headings belong to the abstract", r.sections[0].subs.map(s => s.title), ["Background", "Methods"]);
check("numbered subheading is a subsection of Methods", r.sections[2].subs.map(s => s.title), ["Participants"]);
check("running head and page numbers are never headings", r.headings.some(h => /Journal of Test|^\d+$/.test(h.raw)), false);
check("caption and table header are not headings", r.headings.some(h => /^Table 1|M ± SD|^Group$/.test(h.raw)), false);
check("lower-case line in a heading font is not a heading", r.headings.some(h => /results were mixed/.test(h.raw)), false);
check("reference entries are never headings", r.headings.some(h => /Smith|Jones/.test(h.raw)), false);
check("page numbers recorded", r.sections.map(s => s.page), [1, 1, 2, 3, 3, 3]);

/* letter-spaced capitals, as some publishers set them */
const wiley = [page([L("A study of procrastination", 740, { size: 18, font: "head" }), L("Abstract", 700, H), ...filler(680, 5), L("1 | I N T RO DU CT I O N", 600, H), ...filler(580, 5),
  L("2 | METHODS", 500, H), ...filler(480, 4), L("3 | RE SU LT S", 400, H), ...filler(380, 4), L("REFERENC ES", 300, H), L("Smith, J. (2020). Sleep.", 280, { size: 9, font: "head" })], 1)];
check("letter-spaced capitals are recognised", S.detect(wiley).sections.map(s => s.kind), ["abstract", "introduction", "methods", "results", "references"]);

/* a page printed as images has almost no text */
check("a scan is reported, not guessed at", S.detect([[L("13/11/26", 780, { size: 7 }), L("Page 1 of 1", 20, { size: 7 })]]).notes.length, 1);
check("no pages gives an empty result", S.detect([]).sections, []);

/* page warnings */
const prose = "Participants were students from three colleges and completed the scale twice, a week apart, in class. ".repeat(18);
const digits = Array.from({ length: 30 }, (_, i) => (i * 7 % 100) + "." + (i % 10) + "  " + (i * 3 % 90) + "  " + (i % 5) + ".2").join("\n");
const frag = Array.from({ length: 40 }, (_, i) => (i % 3 ? "a" + i : "B")).join("\n") + "\n" + prose;
check("a normal page has no warning", S.pageFlags([prose, prose, prose])[0], []);
check("a page of numbers is flagged", S.pageFlags([prose, digits, prose, prose])[1], ["numbers"]);
check("a nearly empty page among full ones is flagged blank", S.pageFlags([prose, "Fig 1", prose, prose, prose])[1], ["blank"]);
check("many very short lines are flagged", S.pageFlags([prose, frag, prose, prose])[1], ["fragments"]);
check("a short paper does not flag blank", S.pageFlags(["short note", "another short note"]).map(x => x.length), [0, 0]);
check("no pages gives no flags", S.pageFlags([]), []);
console.log(fails ? fails + " FAILED" : "ALL SECTION TESTS PASSED");
process.exit(fails ? 1 : 0);
