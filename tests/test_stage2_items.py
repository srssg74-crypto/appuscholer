"""B2 to B7 say what the chosen review type asks of them; red and purple highlights appear in B5, B6, B7 (build 2026.11.08z)."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='S2';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    def page(id):
        J("subOpen('lit','%s')"%id); pg.wait_for_timeout(500)
        return J("document.getElementById('subMain')?document.getElementById('subMain').innerText:document.body.innerText")
    ok('Choose your review type in B1' in page('B6'),'no type chosen: B6 points to B1')
    J("wPatch('B1','type','scop')")
    t=page('B6'); ok('For your review type' in t and 'Required' in t,'scoping review: B6 shows its row')
    t=page('B3'); ok('Round 1' in t and 'Round 2' in t,'B3 shows all of its rows')
    ok('For your review type' in page('B2'),'B2 shows its row')
    J("citSaveLib([{author:'Lee, A.',year:'2019',title:'Sleep paper long enough title here',type:'Journal article',style:'apa',hls:[{id:'a',col:'red',page:3,t:'Only one hospital was studied.',pid:'x'},{id:'b',col:'purple',page:4,t:'Stress is a transaction between person and environment.',pid:'x'},{id:'c',col:'blue',page:2,t:'blue should not appear',pid:'x'}]}])")
    cid=json.loads(J("JSON.stringify(citGetLib()[0].cid)"))
    J("logSaveRows('matrix',%s)"%json.dumps([{"cid":cid,"paper":"Lee (2019)","theme":"Sleep"}]))
    t=page('B6'); ok('Only one hospital was studied' in t and 'blue should not appear' not in t,'B6 lists red cards only')
    t=page('B7'); ok('transaction between person and environment' in t and 'Only one hospital' not in t,'B7 lists purple cards only')
    t=page('B5'); ok('Sleep' in t and 'Only one hospital' in t and 'transaction between' in t,'B5 lists both under the theme')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
