"""Reading shelf matrix: statistics the paper prints are offered under matching columns; a tap adds text and page to the cell."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
P1="Participants (N = 120) were students. Mean anxiety was M = 4.2, SD = 1.1."
P2="Sleep predicted anxiety, r = -.41, p < .001. The groups differed, t(118) = 2.31, p = .023, d = 0.42."
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Mx';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("shOpen()"); pg.wait_for_timeout(400)
    J("LS.set('appu_shelf_cols',JSON.stringify(['Sample size','Method','Effect size','p-value']))")
    J("(async()=>{await shPut({id:'m1',title:'Paper one',file:'a.pdf',size:9,added:'2026-11-15',pages:%s,total:2,notes:[],cells:{},sections:[]});await shRefresh();SH.tab='matrix';shRender()})()"%json.dumps([P1,P2])); pg.wait_for_timeout(600)
    ok(J("shColKinds('Sample size')")==['n'] and J("shColKinds('Method')")==[],'column names map to kinds; Method maps to none')
    ok(J("shColKinds('Effect size')")==['effect'] and J("shColKinds('p-value')")==['p'],'effect and p-value columns map')
    t=J("document.getElementById('shBody').innerText")
    ok('The paper prints:' in t,'chips are offered')
    chips=J("Array.from(document.querySelectorAll('#shBody td button')).filter(x=>x.title.startsWith('Add to the cell')).map(x=>x.textContent.replace(/\\s+/g,' ').trim())")
    ok(len(chips)==4 and 'N = 120 p.1' in chips[0],'one chip for n, one for d, two for p: %s'%chips)
    J("Array.from(document.querySelectorAll('#shBody td button')).find(x=>x.textContent.indexOf('N = 120')>=0).click()"); pg.wait_for_timeout(400)
    ok(J("SH.papers[0].cells['Sample size']")=='N = 120 (p. 1)','tap puts the exact text and page into the cell')
    J("Array.from(document.querySelectorAll('#shBody td button')).find(x=>x.textContent.indexOf('N = 120')>=0).click()"); pg.wait_for_timeout(300)
    ok(J("SH.papers[0].cells['Sample size']")=='N = 120 (p. 1)','a second tap does not repeat it')
    J("shCell('m1',1,'Survey');true"); pg.wait_for_timeout(200)
    ok(J("shStatSuggest(SH.papers[0],'Method').length")==0,'a column that is not a statistic gets no chips')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
