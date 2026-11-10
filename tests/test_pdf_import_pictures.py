"""PDF import takes pictures out of the PDF and skips flat decorative ones (build 2026.11.10r).
Needs pdf.js from /opt/npm-tools (the app loads it from a CDN, which the sandbox cannot reach); skipped if absent."""
import sys, os, base64, random, tempfile
sys.path.insert(0, os.path.dirname(__file__))
B='/opt/npm-tools/node_modules/pdfjs-dist/legacy/build/'
if not os.path.exists(B+'pdf.mjs'):
    print('SKIP pdf.js not available'); sys.exit(0)
from harness import new_page
from playwright.sync_api import sync_playwright
from reportlab.pdfgen import canvas
from PIL import Image
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
d=tempfile.mkdtemp()
random.seed(3)
photo=Image.new('RGB',(220,220))
photo.putdata([(random.randint(0,255),random.randint(60,200),random.randint(0,255)) for _ in range(220*220)]); photo.save(d+'/photo.png')
Image.new('RGB',(220,220),(210,210,210)).save(d+'/flat.png')
c=canvas.Canvas(d+'/t.pdf')
c.setFont('Helvetica-Bold',20); c.drawString(60,780,'A Made-up Study of Worry and Sleep')
c.setFont('Helvetica',10)
for i in range(6): c.drawString(60,740-i*14,'This is a made-up paragraph line number %d with enough words to fill the line of text.'%i)
c.drawImage(d+'/photo.png',60,400,150,150); c.drawImage(d+'/flat.png',260,400,150,150)
c.save()
data=base64.b64encode(open(d+'/t.pdf','rb').read()).decode()
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    def route(r):
        f=r.request.url.split('/_pdfjs/')[1].split('?')[0]
        r.fulfill(path=B+f,headers={'access-control-allow-origin':'*','content-type':'text/javascript'})
    pg.route('**/_pdfjs/*',route)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("(async()=>{const m=await import('http://localhost:8765/_pdfjs/pdf.mjs');m.GlobalWorkerOptions.workerSrc='http://localhost:8765/_pdfjs/pdf.worker.mjs';window.pdfjsLib=m})()"); pg.wait_for_timeout(1500)
    r=J("""(async()=>{const bin=atob('%s');const u=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);
      const f=new File([u],'Paper.pdf',{type:'application/pdf'});await docImportOne(f,'');const h=getEditorHTML();
      return JSON.stringify({imgs:(h.match(/<img/g)||[]).length,h1:((h.match(/<h1[^>]*>(.*?)<\\/h1>/)||[])[1]||''),cap:/Picture from page 1/.test(h),block:/Pictures in the PDF/.test(h)})})()"""%data)
    import json; r=json.loads(r)
    ok(r['imgs']==1,'one real picture imported, the flat one skipped (%s)'%r['imgs'])
    ok(r['block'] and r['cap'],'pictures sit in a Pictures in the PDF block with their page')
    ok('Made-up Study' in r['h1'],'title is the heading')
    ok(not [e for e in errors if 'Failed to load resource' not in str(e)],'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
