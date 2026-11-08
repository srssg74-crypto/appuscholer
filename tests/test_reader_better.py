"""Reader improvements (build 2026.11.08s): search in the paper, zoom, attach PDF, highlight box geometry, phone fit."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
PAGES=['Participants were 96 nurses recruited from two hospitals.','Stress was higher on night shifts. Sleep loss predicted burnout.','Sleep and stress: a small single-city sample is a limitation.']
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors,{'width':390,'height':780}); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Better';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("(async()=>{await shPut({id:'pB',title:'Nurse stress',file:'n.pdf',size:1,added:'2026-11-08',pages:%s,total:3,notes:[],cells:{}})})()"%json.dumps(PAGES)); pg.wait_for_timeout(400)
    J("shOpenAt('pB',1)"); pg.wait_for_timeout(700)
    # search
    J("shInSearch('sleep stress')"); pg.wait_for_timeout(400)
    t=J("document.getElementById('shBody').innerText")
    ok('2 pages with these words' in t and 'p. 3' in t,'search lists the pages that have both words')
    J("shInSearch('burnout')"); pg.wait_for_timeout(300)
    ok('1 page with these words' in J("document.getElementById('shBody').innerText") and J("SH.page")==2,'search jumps to the page that has the word')
    ok(J("document.getElementById('shText').innerHTML").count('<u ')>=1,'the word is underlined on the page')
    J("shInSearch('zebra')"); ok('No page has all of those words' in J("document.getElementById('shBody').innerText"),'no match said plainly')
    # zoom
    z0=J("SH.zoom"); J("shZoom(0.25)"); ok(J("SH.zoom")==z0+0.25,'zoom in'); J("shZoom(-5)"); ok(J("SH.zoom")==0.75,'zoom stops at 75%'); J("shZoom(9)"); ok(J("SH.zoom")==3,'and at 300%'); J("shZoom(-9)");J("shZoom(0.25)")
    # attach for a paper without a file
    J("SH.img=true;shRender()"); pg.wait_for_timeout(600)
    ok('Attach the PDF' in J("document.getElementById('shImg').innerText"),'paper without a file offers to attach it')
    # phone fit
    ok(J("document.documentElement.scrollWidth")<=J("window.innerWidth")+1,'no sideways scroll at phone width')
    # box geometry from synthetic text items (viewport transform: y flipped, scale 2)
    items=[{"str":"Participants were ","transform":[10,0,0,10,20,250],"width":90,"height":10},{"str":"96 nurses recruited from","transform":[10,0,0,10,110,250],"width":120,"height":10}]
    r=json.loads(J("JSON.stringify(shQuoteBoxes(%s,'96 nurses',t=>[2*t[0],0,0,-2*t[3],2*t[4],2*(300-t[5])]))"%json.dumps(items)))
    ok(len(r)==1 and abs(r[0]['x']-220)<1 and r[0]['w']>80 and r[0]['w']<100,'box starts at the quote start and covers part of the item %s'%r)
    ok(J("shQuoteBoxes(%s,'not in this page',t=>t)"%json.dumps(items))==[],'quote not on the page: no box, no error')
    r2=json.loads(J("JSON.stringify(shQuoteBoxes(%s,'were 96 nurses',t=>[t[0],0,0,t[3],t[4],t[5]]))"%json.dumps(items)))
    ok(len(r2)==2,'a quote across two items gets two boxes')
    # attach a PDF to an older paper
    J("(async()=>{await shPut({id:'pA',title:'Old one',file:'o.pdf',size:1,added:'2026-11-08',pages:['Participants were 96 nurses.'],total:1,notes:[],cells:{}})})()"); pg.wait_for_timeout(300)
    J("SH.img=true;shOpenAt('pA',1)"); pg.wait_for_timeout(700)
    pg.set_input_files("#shImg input[type=file]","/tmp/attach_t.pdf"); pg.wait_for_timeout(1200)
    ok(J("(async()=>(await shFileGet('pA'))!==null)()"),'attached PDF is kept for the old paper')
    ok(J("!!document.querySelector('#shImg canvas')"),'and the page picture appears')
    J("shOpenAt('pB',1)"); pg.wait_for_timeout(500)
    pg.set_input_files("#shImg input[type=file]","/tmp/attach_t.pdf"); pg.wait_for_timeout(1000)
    ok(J("(async()=>(await shFileGet('pB'))===null)()"),'a file with fewer pages than the paper is refused')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
