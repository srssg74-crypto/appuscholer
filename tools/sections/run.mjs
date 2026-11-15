import fs from "fs";
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const S = require("./sections.js");
const pdfjs = await import((process.env.PDFJS || "/opt/npm-tools/node_modules/pdfjs-dist/legacy/build/pdf.mjs"));
const dir = (process.env.PDF_DIR || "/mnt/user-data/attachments/d540b351-a2df-5fa6-9a88-226a4c6e6a4f") + "/";
const files = process.argv.slice(2);
for (const f of files) {
  const data = new Uint8Array(fs.readFileSync(dir + f));
  const pdf = await pdfjs.getDocument({ data, useSystemFonts: true, verbosity: 0 }).promise;
  const pages = [];
  for (let k = 1; k <= Math.min(pdf.numPages, 60); k++) { const p = await pdf.getPage(k); const tc = await p.getTextContent(); pages.push(tc.items); }
  const r = S.detect(pages);
  console.log("\n=== " + f + " (" + pdf.numPages + " pages) body " + (r.body && r.body.size.toFixed(1)) + " title: " + r.title);
  r.headings.forEach(h => console.log("  ".repeat(h.level - 1) + "[" + (h.kind || "-") + " L" + h.level + " p" + h.page + " " + h.size.toFixed(1) + "] " + h.raw));
}
