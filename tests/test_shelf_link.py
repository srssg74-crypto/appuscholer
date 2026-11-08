"""Reading shelf and library on one paper list (build 2026.11.08m)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Shelf';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("citSaveLib([{author:'Lee, A.',year:'2019',title:'Sleep duration and academic performance in university students',type:'Journal article',style:'apa',scr:{st:'included',why:'core paper'}},{author:'Rao, C.',year:'2021',title:'Short title',type:'Journal article',style:'apa'}])")
    m=J("(shLibMatch('Sleep Duration and Academic Performance in University Students.')||{}).year")
    ok(m=='2019','title match ignores case and full stops')
    ok(J("shLibMatch('Sleep duration')")is None,'a short or partial title does not match')
    ok(J("shLibMatch('Sleep duration and academic performance in university students: a cohort study')!==null"),'a long title that contains the library title matches')
    rec="{id:'p1',title:'Sleep duration and academic performance in university students',file:'a.pdf',size:1,added:'2026-11-08',pages:['x'],total:1,notes:[],cells:{}}"
    J("(async()=>{const r=%s;shLinkLib(r);await shPut(r);await shRefresh()})()"%rec); pg.wait_for_timeout(600)
    L=json.loads(J("JSON.stringify(citGetLib())"))
    ok(L[0].get('shelf')=='p1','library entry knows its PDF is on the shelf')
    J("shOpen()"); pg.wait_for_timeout(800)
    t=J("document.getElementById('shBody').innerText")
    ok('In your library: Included' in t and 'core paper' in t,'shelf shows the library status and the why-line')
    ok('PDF on Reading shelf' in J("document.getElementById('citLib').innerText"),'library card says the PDF is on the shelf')
    J("(async()=>{const r={id:'p2',title:'Scanned thing',file:'b.pdf',size:2,added:'2026-11-09',pages:['y'],total:1,notes:[],cells:{}};await shPut(r);await shRefresh()})()"); pg.wait_for_timeout(600)
    ok('Not found in your library' in J("document.getElementById('shBody').innerText"),'unmatched PDF says so')
    cid=L[1]['cid']
    J("shLink('p2','%s')"%cid); pg.wait_for_timeout(600)
    L=json.loads(J("JSON.stringify(citGetLib())"))
    ok(L[1].get('shelf')=='p2','manual link written to the library entry')
    J("shLink('p2','')"); pg.wait_for_timeout(600)
    L=json.loads(J("JSON.stringify(citGetLib())"))
    ok(not L[1].get('shelf'),'unlinking clears it')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
