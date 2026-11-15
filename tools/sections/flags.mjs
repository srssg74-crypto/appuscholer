import fs from "fs"; import { createRequire } from "module";
const S = createRequire(import.meta.url)("./sections.js");
const pdfjs = await import(process.env.PDFJS || "/opt/npm-tools/node_modules/pdfjs-dist/legacy/build/pdf.mjs");
const dir = (process.env.PDF_DIR || "/mnt/user-data/attachments/d540b351-a2df-5fa6-9a88-226a4c6e6a4f") + "/";
const files = fs.readdirSync(dir).filter(f => /s12889|s12879|pmed|ijerph|s12890|Procrastination|0263027|s12884|1177_|12888_|s12931|s13018|e187/.test(f));
let tp = 0, tf = {};
for (const f of files) {
  const pdf = await pdfjs.getDocument({ data: new Uint8Array(fs.readFileSync(dir + f)), useSystemFonts: true, verbosity: 0 }).promise;
  const pages = []; for (let k = 1; k <= Math.min(pdf.numPages, 60); k++) { const p = await pdf.getPage(k); pages.push((await p.getTextContent()).items.map(i => i.str + (i.hasEOL ? "\n" : " ")).join("")); }
  const fl = S.pageFlags(pages); tp += pages.length;
  const hit = fl.map((x, i) => x.length ? (i + 1) + ":" + x.join("+") : null).filter(Boolean);
  fl.forEach(x => x.forEach(k => tf[k] = (tf[k] || 0) + 1));
  console.log(f.slice(9, 45).padEnd(37), pages.length + "p", hit.join(" "));
}
console.log("pages", tp, JSON.stringify(tf));
