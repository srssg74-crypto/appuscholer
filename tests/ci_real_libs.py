"""CI only (needs the real internet): load every page with the real CDN libraries and the live policy.
Run by .github/workflows/real-libs.yml. Not part of the local suite, which has no outside network."""
import sys, base64
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m+'  ')
    if not c: fails.append(m)
# a one-page PDF with the words "Hello Appuscholar"
PDF=b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 52>>stream
BT /F1 18 Tf 20 60 Td (Hello Appuscholar) Tj ET
endstream endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
trailer<</Root 1 0 R>>
%%EOF"""
B64=base64.b64encode(PDF).decode()
WATCH="""window.__v=[];document.addEventListener('securitypolicyviolation',e=>window.__v.push(e.violatedDirective+' '+e.blockedURI));"""
with sync_playwright() as p:
    b=p.chromium.launch()
    for page in ['index.html','auth.html','admin.html','kit.html','form.html']:
        ctx=b.new_context(service_workers='block'); ctx.add_init_script(WATCH); pg=ctx.new_page()
        errs=[]; pg.on('console',lambda m,errs=errs: errs.append(m.text) if m.type=='error' else None)
        pg.goto('http://localhost:8765/'+page); pg.wait_for_timeout(6000)
        v=pg.evaluate('window.__v')
        ok(not v,page+': the policy blocked nothing '+str(v[:4]))
        sri=[e for e in errs if 'integrity' in e.lower()]
        ok(not sri,page+': no integrity failures '+str(sri[:2]))
        if page=='index.html':
            have=pg.evaluate("()=>({pdf:typeof pdfjsLib,mammoth:typeof mammoth,chart:typeof Chart,pptx:typeof PptxGenJS,worker:String(pdfjsLib&&pdfjsLib.GlobalWorkerOptions.workerSrc||'')})")
            ok(have['pdf']=='object' and have['mammoth']=='object' and have['chart']=='function' and have['pptx']=='function','all four libraries loaded with their hashes '+str(have))
            ok(have['worker'].startswith('blob:'),'the PDF worker was fetched with its hash and is running from a blob')
            txt=pg.evaluate("""async b=>{const bin=Uint8Array.from(atob(b),c=>c.charCodeAt(0));const pdf=await pdfjsLib.getDocument({isEvalSupported:false,data:bin}).promise;
                const pg=await pdf.getPage(1);const t=await pg.getTextContent();return t.items.map(i=>i.str).join(' ')}""",B64)
            ok('Hello Appuscholar' in txt,'a real PDF opens and its text is read: '+txt)
            pl=pg.evaluate("async()=>{try{const P=await plibLoad();return !!(P&&P.PDFDocument)}catch(e){return String(e)}}")
            ok(pl is True,'pdf-lib loads on demand with its hash ('+str(pl)+')')
            for u in ['https://unpkg.com/chart.js@4.4.4/dist/chart.umd.min.js','https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js','https://unpkg.com/pptxgenjs@3.12.0/dist/pptxgen.bundle.js']:
                r=pg.evaluate("""u=>new Promise(res=>{const s=document.createElement('script');s.integrity=APPU_SRI[u];s.crossOrigin='anonymous';s.src=u;s.onload=()=>res(true);s.onerror=()=>res(false);document.head.appendChild(s)})""",u)
                ok(r,'spare copy loads with its hash: '+u)
            v=pg.evaluate('window.__v'); ok(not v,'still nothing blocked after the PDF and the spare copies '+str(v[:4]))
        ctx.close()
    b.close()
print('\n%d failed'%len(fails)); sys.exit(1 if fails else 0)
