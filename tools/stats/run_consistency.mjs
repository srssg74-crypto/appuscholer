import fs from "fs";
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const S = require("./statsfind.js"), C = require("./consistency.js");
const pdfjs = await import((process.env.PDFJS || "/opt/npm-tools/node_modules/pdfjs-dist/legacy/build/pdf.mjs"));
const dir = (process.env.PDF_DIR || "/mnt/user-data/attachments/d540b351-a2df-5fa6-9a88-226a4c6e6a4f") + "/";
const list = fs.readdirSync(dir).filter(f => /\.pdf$/i.test(f));
let checked = 0, ok = 0, inc = 0, dec = 0;
for (const f of list) {
  try {
    const pdf = await pdfjs.getDocument({ data: new Uint8Array(fs.readFileSync(dir + f)), useSystemFonts: true, verbosity: 0 }).promise;
    const pages = [];
    for (let k = 1; k <= Math.min(pdf.numPages, 60); k++) { const p = await pdf.getPage(k); pages.push((await p.getTextContent()).items.map(x => x.str).join(" ").replace(/\s+/g, " ")); }
    const hh = S.find(pages), r = C.check(pages, hh).concat(C.checkCI(pages, hh));
    r.forEach(x => { checked++; if (x.status === "ok") ok++; else { x.status === "decision" ? dec++ : inc++; const t = pages[x.page - 1], i = t.indexOf(x.test); console.log(f.slice(9, 40) + " p" + x.page + " [" + x.status + "] " + x.test + " ... " + x.p + "  (computed " + x.computed.toFixed(4) + ")\n    ..." + t.slice(Math.max(0, i - 60), i + 130) + "..."); } });
  } catch (e) { }
}
console.log("pairs checked", checked, "ok", ok, "inconsistent", inc, "decision", dec);
