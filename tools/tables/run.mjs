import fs from "fs";
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const T = require("./tables.js");
const pdfjs = await import((process.env.PDFJS || "/opt/npm-tools/node_modules/pdfjs-dist/legacy/build/pdf.mjs"));
const dir = (process.env.PDF_DIR || "/mnt/user-data/attachments/d540b351-a2df-5fa6-9a88-226a4c6e6a4f") + "/";
const files = process.argv.slice(2).filter(a => !a.startsWith("-")), verbose = process.argv.includes("-v");
const list = files.length ? files : fs.readdirSync(dir).filter(f => /\.pdf$/i.test(f));
let tt = 0, th = 0, tj = 0;
for (const f of list) {
  try {
    const data = new Uint8Array(fs.readFileSync(dir + f));
    const pdf = await pdfjs.getDocument({ data, useSystemFonts: true, verbosity: 0 }).promise;
    const pages = [];
    for (let k = 1; k <= Math.min(pdf.numPages, 60); k++) { const p = await pdf.getPage(k); pages.push((await p.getTextContent()).items); }
    const r = T.read(pages);
    tt += r.tables.length; th += r.hits.length; tj += r.tables.filter(t => t.joined).length;
    console.log(f.slice(0, 60).padEnd(60), "tables", r.tables.length, "joined", r.tables.filter(t => t.joined).length, "M/SD hits", r.hits.length);
    if (verbose) r.tables.forEach(t => { console.log("  " + t.caption.slice(0, 80) + " pp" + t.pages.join("-") + (t.joined ? " JOINED" : "") + " cols " + t.header.length + " rows " + t.rows.length); console.log("    H: " + t.header.join(" | ").slice(0, 150)); t.rows.slice(0, 3).forEach(x => console.log("    R: " + x.join(" | ").slice(0, 150))); });
    if (verbose) r.hits.slice(0, 5).forEach(h => console.log("  HIT " + h.text + " (Table " + h.table + ", p" + h.page + ")"));
  } catch (e) { console.log(f.slice(0, 50), "ERR", e.message); }
}
console.log("TOTAL tables", tt, "joined", tj, "hits", th);
