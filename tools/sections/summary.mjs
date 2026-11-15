import fs from "fs"; import { createRequire } from "module";
const S = createRequire(import.meta.url)("./sections.js");
const pdfjs = await import((process.env.PDFJS || "/opt/npm-tools/node_modules/pdfjs-dist/legacy/build/pdf.mjs"));
const dir = (process.env.PDF_DIR || "/mnt/user-data/attachments/d540b351-a2df-5fa6-9a88-226a4c6e6a4f") + "/";
const files = fs.readdirSync(dir).filter(f => /s12889|s12879|pmed|ijerph|s12890|Procrastination|0263027|s12884|1177_|12888_|Childhood|From_prevalence|s12931|s13018|e187|Paper_4/.test(f));
const want = ["introduction","methods","results","discussion","references"];
let tot = {}; want.forEach(k=>tot[k]=0); let n=0;
for (const f of files) {
  const pdf = await pdfjs.getDocument({ data: new Uint8Array(fs.readFileSync(dir+f)), useSystemFonts:true, verbosity:0 }).promise;
  const pages=[]; for (let k=1;k<=Math.min(pdf.numPages,60);k++){const p=await pdf.getPage(k);pages.push((await p.getTextContent()).items);}
  const r = S.detect(pages); const got = new Set(r.sections.map(s=>s.kind)); n++;
  want.forEach(k=>{ if(got.has(k)) tot[k]++; });
  console.log(f.slice(9,50).padEnd(42), want.map(k=>got.has(k)?k[0].toUpperCase():"-").join(""), "heads", r.headings.length, "pages", pdf.numPages);
}
console.log("papers", n, tot);
