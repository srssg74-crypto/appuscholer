import fs from "fs"; import { createRequire } from "module";
const S = createRequire(import.meta.url)("./statsfind.js");
const pdfjs = await import(process.env.PDFJS || "/opt/npm-tools/node_modules/pdfjs-dist/legacy/build/pdf.mjs");
const dir = (process.env.PDF_DIR || "/mnt/user-data/attachments/d540b351-a2df-5fa6-9a88-226a4c6e6a4f") + "/";
const files = fs.readdirSync(dir).filter(f => /s12889|s12879|pmed|ijerph|s12890|Procrastination|0263027|s12884|1177_|12888_|s12931|s13018|e187/.test(f));
const verbose = process.argv[2] === "-v"; const tot = {}; const samples = {};
for (const f of files) {
  const pdf = await pdfjs.getDocument({ data: new Uint8Array(fs.readFileSync(dir + f)), useSystemFonts: true, verbosity: 0 }).promise;
  const pages = []; for (let k = 1; k <= Math.min(pdf.numPages, 60); k++) { const p = await pdf.getPage(k); pages.push((await p.getTextContent()).items.map(i => i.str + (i.hasEOL ? "\n" : "")).join("")); }
  const h = S.find(pages), s = S.summarise(h);
  Object.keys(s).forEach(k => { tot[k] = (tot[k] || 0) + s[k]; (samples[k] = samples[k] || []).push(...h.filter(x => x.stat === k).slice(0, 3).map(x => f.slice(9, 18) + " p" + x.page + " " + x.text)); });
  console.log(f.slice(9, 48).padEnd(40), JSON.stringify(s));
}
console.log("TOTAL", JSON.stringify(tot));
if (verbose) Object.keys(samples).forEach(k => { console.log("\n" + k); samples[k].filter((_, i) => i % 6 === 0).slice(0, 12).forEach(x => console.log("  " + x)); });
