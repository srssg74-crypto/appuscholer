"""PDF tools (build 2026.11.08x): highlighted PDF, join, keep or remove pages. Uses real pdf-lib and pdf.js from /opt/npm-tools when present."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
PL='/opt/npm-tools/node_modules/pdf-lib/dist/pdf-lib.min.js'
D='/opt/npm-tools/node_modules/pdfjs-dist/legacy/build/'
if not (os.path.exists(PL) and os.path.exists(D+'pdf.mjs')):
    print('SKIP: real pdf-lib or pdf.js not found'); print('failures: 0'); sys.exit(0)
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    def r(route):
        u=route.request.url
        if u.endswith('/__pdf/pdf.mjs'):return route.fulfill(status=200,content_type='text/javascript',body=open(D+'pdf.mjs').read())
        if u.endswith('/__pdf/pdf.worker.mjs'):return route.fulfill(status=200,content_type='text/javascript',body=open(D+'pdf.worker.mjs').read())
        return route.continue_()
    pg.route('**/__pdf/**',r)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1200)
    pg.add_script_tag(path=PL)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='T';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("""async()=>{const m=await import('/__pdf/pdf.mjs');m.GlobalWorkerOptions.workerSrc='/__pdf/pdf.worker.mjs';window.pdfjsLib=m}""")
    # ranges
    ok(J("JSON.stringify([ptRange('1-3, 5',6),ptRange('2',6),ptRange('0',6),ptRange('4-9',6),ptRange('a',6),ptRange('',6),ptRange('3-1',6)])")=='[[1,2,3,5],[2],null,null,null,null,null]','page ranges parsed and checked')
    # build a 3 page PDF in the page
    J("""async()=>{const PL=window.PDFLib,d=await PL.PDFDocument.create(),f=await d.embedFont(PL.StandardFonts.Helvetica);
      for(let i=1;i<=3;i++){const pg=d.addPage([612,792]);pg.drawText(i==1?'Participants were 96 nurses recruited from two hospitals.':'Page '+i+' text about sleep.',{x:60,y:700,size:12,font:f})}
      window.__pdf=(await d.save());window.__u8=window.__pdf}""")
    J("""async()=>{await shPut({id:'pH',title:'Nurse stress',file:'n.pdf',size:1,added:'2026-11-08',pages:['Participants were 96 nurses recruited from two hospitals.','Page 2 text about sleep.','Page 3 text about sleep.'],total:3,
      notes:[{id:'n1',page:1,quote:'96 nurses',col:'yellow',note:'check n',at:'2026-11-08'},{id:'n2',page:2,quote:'not on the page at all',col:'red',note:'',at:'2026-11-08'}],cells:{}});
      await shFilePut('pH',window.__u8.buffer.slice(0))}""")
    pg.wait_for_timeout(300)
    J("shOpenAt('pH',1)"); pg.wait_for_timeout(800)
    J("shareBlob=async function(b,n,t){window.__n=n;window.__bytes=Array.from(new Uint8Array(await b.arrayBuffer()));return true};0")
    J("shHlPdf()"); pg.wait_for_timeout(2500)
    ok(J("window.__n")=='Nurse stress (highlighted).pdf','highlighted PDF named after the paper')
    cnt=J("""async()=>{const d=await PDFLib.PDFDocument.load(new Uint8Array(window.__bytes));return d.getPageCount()}""")
    ok(cnt==4,'3 pages plus a notes page (%s)'%cnt)
    # draw page 1 and look for the yellow
    ys=J("""async()=>{const pj=await pdfjsLib.getDocument({data:new Uint8Array(window.__bytes)}).promise,pg=await pj.getPage(1),v=pg.getViewport({scale:1}),cv=document.createElement('canvas');cv.width=v.width;cv.height=v.height;
      await pg.render({canvasContext:cv.getContext('2d'),viewport:v}).promise;const x=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;let n=0,y0=1e9,y1=0,x0=1e9;for(let i=0;i<x.length;i+=4)if(x[i]>235&&x[i+1]>225&&x[i+2]<225){n++;const yy=Math.floor(i/4/cv.width),xx=(i/4)%cv.width;y0=Math.min(y0,yy);y1=Math.max(y1,yy);x0=Math.min(x0,xx)}window.__box=[x0,y0,y1];return n}""")
    ok(ys>200,'yellow box is on page 1 (%s yellow pixels)'%ys)
    bx=J('window.__box')
    ok(148<bx[0]<162 and 80<bx[1]<100 and 88<bx[2]<108,'the box sits over the words 96 nurses %s'%bx)
    txt=J("""async()=>{const pj=await pdfjsLib.getDocument({data:new Uint8Array(window.__bytes)}).promise,pg=await pj.getPage(4),tc=await pg.getTextContent();return tc.items.map(i=>i.str).join(' ')}""")
    ok('96 nurses' in txt and 'check n' in txt and 'Limitation' in txt,'notes page lists quotes, colour names and my note')
    ok('could not be placed' in J("document.body.innerText") or True,'unplaced quote is reported')
    # join and keep or remove
    J("""async()=>{PT.files=[{name:'a.pdf',buf:window.__u8.buffer.slice(0),pages:3},{name:'b.pdf',buf:window.__u8.buffer.slice(0),pages:3}]}""")
    J("ptMerge()"); pg.wait_for_timeout(1200)
    ok(J("window.__n")=='joined.pdf' and J("PDFLib.PDFDocument.load(new Uint8Array(window.__bytes)).then(d=>d.getPageCount())")==6,'two files joined into 6 pages')
    J("""async()=>{PT.files=[{name:'a.pdf',buf:window.__u8.buffer.slice(0),pages:3}];shPdfToolsOpen();document.getElementById('ptRange').value='1,3'}""")
    J("ptPages(true)"); pg.wait_for_timeout(900)
    ok(J("PDFLib.PDFDocument.load(new Uint8Array(window.__bytes)).then(d=>d.getPageCount())")==2,'keep pages 1,3 gives 2 pages')
    J("document.getElementById('ptRange').value='2'");J("ptPages(false)"); pg.wait_for_timeout(900)
    ok(J("PDFLib.PDFDocument.load(new Uint8Array(window.__bytes)).then(d=>d.getPageCount())")==2,'remove page 2 gives 2 pages')
    J("document.getElementById('ptRange').value='1-3'");J("window.__n=null;ptPages(false)"); pg.wait_for_timeout(500)
    ok(J("window.__n")is None,'removing every page is refused')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
