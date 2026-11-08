"""Agree / doubt taps and My thought on highlight cards, and the B5 tally (build 2026.11.08y)."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='Taps';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("citSaveLib([{author:'Lee, A.',year:'2019',title:'Sleep duration and academic performance in university students',type:'Journal article',style:'apa',dir:'more'},{author:'Rao, C.',year:'2021',title:'Night shifts and burnout in hospital nurses across India',type:'Journal article',style:'apa',dir:'less'}])")
    L=json.loads(J("JSON.stringify(citGetLib())"))
    A,B=L[0]['cid'],L[1]['cid']
    notes="[{id:'n1',page:1,quote:'Sleep predicted burnout',col:'blue',note:'',at:'x'},{id:'n2',page:1,quote:'small sample',col:'red',note:'',at:'x'}]"
    J("(async()=>{const r={id:'pT',title:'Sleep duration and academic performance in university students',file:'a.pdf',size:1,added:'2026-11-08',pages:['Sleep predicted burnout. A small sample was used.'],total:1,notes:%s,cells:{}};shLinkLib(r);await shPut(r);await shRefresh()})()"%notes); pg.wait_for_timeout(500)
    J("shOpenAt('pT',1)"); pg.wait_for_timeout(700)
    t=J("document.getElementById('shBody').innerText")
    ok('I agree' in t and 'I doubt' in t and 'My thought' in t,'cards show the three buttons')
    J("shStance('n1','agree')"); pg.wait_for_timeout(300); J("shStance('n2','doubt')"); pg.wait_for_timeout(300)
    lib=json.loads(J("JSON.stringify(citGetLib()[0])"))
    ok(lib.get('reads')=={'agree':1,'doubt':1},'counts written to the library paper %s'%lib.get('reads'))
    J("shStance('n2','doubt')"); pg.wait_for_timeout(300)
    ok(json.loads(J("JSON.stringify(citGetLib()[0].reads)"))=={'agree':1,'doubt':0},'tapping again takes it back')
    J("shThought('n1')"); pg.wait_for_timeout(300)
    J("document.getElementById('shTh').value='Fits my own sleep data';shThoughtSave('n1')"); pg.wait_for_timeout(500)
    ok('Fits my own sleep data' in J("document.getElementById('shBody').innerText"),'my thought is saved and shown on the card')
    # B5
    rows=[{"cid":A,"paper":"Lee (2019). Sleep","theme":"Sleep"},{"cid":B,"paper":"Rao (2021). Night","theme":"Sleep"}]
    J("(()=>{const o=studyGet();logSaveRows('matrix',%s)})()"%json.dumps(rows))
    J("subOpen('lit','B5')"); pg.wait_for_timeout(700)
    t=J("document.getElementById('subMain')?document.getElementById('subMain').innerText:document.body.innerText")
    ok('Direction: More 1, Less 1' in t and 'They conflict' in t,'B5 theme tally counts the direction chips and flags the conflict')
    ok('agreed 1' in t,'B5 shows my taps')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
