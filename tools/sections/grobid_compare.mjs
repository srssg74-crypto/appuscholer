/* Run GROBID and our detector on the same PDFs and compare. UNTESTED against a live GROBID: this sandbox has no network.
   1. Start GROBID (needs Docker; check the current image tag on the GROBID docs page):
        docker run --rm --init -p 8070:8070 lfoppiano/grobid:<tag>
   2. PDF_DIR=/path/to/pdfs GROBID=http://localhost:8070 PDFJS=/path/to/pdfjs-dist/legacy/build/pdf.mjs node grobid_compare.mjs
   Writes one TEI file per PDF into ./tei/ and prints a table. */
import fs from "fs"; import { createRequire } from "module";
const S = createRequire(import.meta.url)("./sections.js");
const pdfjs = await import(process.env.PDFJS || "/opt/npm-tools/node_modules/pdfjs-dist/legacy/build/pdf.mjs");
const dir = process.env.PDF_DIR, grobid = process.env.GROBID || "http://localhost:8070";
if (!dir) { console.log("set PDF_DIR"); process.exit(1); }
fs.mkdirSync("tei", { recursive: true });
const WANT = ["introduction", "methods", "results", "discussion", "references"];
const kinds = (heads) => new Set(heads.map(h => S.kindOf(h)).filter(Boolean));
console.log("paper".padEnd(36), "ours(IMRDR)", "grobid(IMRDR)", "g.heads", "g.refs", "g.seconds");
for (const f of fs.readdirSync(dir).filter(x => /\.pdf$/i.test(x))) {
  const bytes = fs.readFileSync(dir + "/" + f);
  const pdf = await pdfjs.getDocument({ data: new Uint8Array(bytes), useSystemFonts: true, verbosity: 0 }).promise;
  const pages = []; for (let k = 1; k <= Math.min(pdf.numPages, 60); k++) { const p = await pdf.getPage(k); pages.push((await p.getTextContent()).items); }
  const ours = new Set(S.detect(pages).sections.map(s => s.kind));
  const fd = new FormData(); fd.append("input", new Blob([bytes], { type: "application/pdf" }), f);
  fd.append("consolidateHeader", "0"); fd.append("consolidateCitations", "0");
  const t0 = Date.now(); let tei = "";
  try { const r = await fetch(grobid + "/api/processFulltextDocument", { method: "POST", body: fd }); tei = await r.text(); } catch (e) { console.log(f.slice(0, 35).padEnd(36), "GROBID not reachable:", e.message); continue; }
  fs.writeFileSync("tei/" + f.replace(/\.pdf$/i, ".tei.xml"), tei);
  const body = (tei.match(/<body>([\s\S]*?)<\/body>/) || [, ""])[1];
  const heads = [...body.matchAll(/<head[^>]*>([\s\S]*?)<\/head>/g)].map(m => m[1].replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim());
  const refs = (tei.match(/<biblStruct/g) || []).length;
  const g = kinds(heads);
  const flag = (set) => WANT.map(k => set.has(k) ? k[0].toUpperCase() : "-").join("");
  console.log(f.slice(0, 35).padEnd(36), flag(ours).padEnd(11), flag(g).padEnd(13), String(heads.length).padEnd(7), String(refs).padEnd(6), ((Date.now() - t0) / 1000).toFixed(1));
}
