"""Numeric missing-value codes (Version 131): a 99 or -9 meaning "no answer" must not enter the mean.
The app points out values that look like such codes; the student decides; the decision is logged."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
CSV='id,group,age,stress,q1\n'+'\n'.join([
 '1,Hostel,19,27,4','2,Home,21,22,5','3,Hostel,99,31,3','4,Home,20,20,9','5,Hostel,22,25,2',
 '6,Home,18,-9,4','7,Hostel,23,29,1','8,Home,19,19,5','9,Hostel,20,26,3','10,Home,99,23,2'])
CLEAN='group,stress\nHostel,27\nHome,22\nHostel,31\nHome,20\nHostel,25\nHome,24\nHostel,29\nHome,19\nHostel,26\nHome,23'
TOTALS='id,total\n'+'\n'.join('%d,%d'%(i,v) for i,v in enumerate([45,99,60,72,88,51,67,94,30,77],1))
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js,*a: pg.evaluate(js,*a)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(2000)
    J("window.genFirstOn=()=>false;window.__t=[];window.showToast=m=>window.__t.push(m);0")
    load=lambda t: J("t=>{document.getElementById('statsPaste').value=t;statsParse();return window._statsData.notes}",t)
    def mean(col):
        return J("""c=>{const d=window._statsData,i=d.cols.findIndex(x=>x.name===c);const v=d.rows.map(r=>r[i]).filter(x=>x!=='').map(Number);return [v.length,v.reduce((a,b)=>a+b,0)/v.length]}""",col)
    n=load(CSV); sus=n.get('suspect',{})
    ok('age' in sus and sus['age'][0]['code']=='99' and sus['age'][0]['n']==2,'age: 99 (twice) is pointed out '+str(sus.get('age')))
    ok('stress' in sus and sus['stress'][0]['code']=='-9','stress: -9 among positive scores is pointed out')
    ok('q1' in sus and sus['q1'][0]['code']=='9','q1: 9 on a 1–5 item is pointed out')
    ok('id' not in sus,'id column raises nothing')
    ok(mean('age')[0]==10,'before any decision the values are left as they are (nothing changed silently)')
    box=J("document.getElementById('statsCols').innerText")
    ok('Treat 99 as missing' in box and 'It is a real value' in box,'the choice is offered in the Statistics Lab')
    # decide
    J("mcDecide('age','99','missing')")
    nn,m=mean('age'); ok(nn==8 and abs(m-20.25)<1e-9,'after "Treat 99 as missing": age has 8 values, mean 20.25 (was %s)'%m)
    ok('age' not in (J("window._statsData.notes").get('suspect') or {}),'the age warning goes away')
    ok('Treated as missing by your codes: age (99 × 2)' in J("document.getElementById('statsCols').innerText"),'the parse note says which cells became missing')
    log=J("JSON.stringify(logRows(studyGet(),'clean'))")
    ok('age: 99 treated as missing' in log,'the decision is written to the cleaning log')
    # keep
    J("mcDecide('q1','9','keep')")
    ok('q1' not in (J("window._statsData.notes").get('suspect') or {}) and mean('q1')[0]==10,'"It is a real value" keeps 9 and stops asking')
    ok('q1: 9 kept as a real value' in J("JSON.stringify(logRows(studyGet(),'clean'))"),'keeping is logged too')
    # declared code survives a reload of the same column name
    load(CSV); ok(mean('age')[0]==8,'the code is remembered when the data are loaded again')
    # a test uses the cleaned column
    J("""()=>{const s=document.getElementById('statsTest');s.value='desc';statsFieldsRender();document.getElementById('sf_dv').value=String(window._statsData.cols.findIndex(c=>c.name==='age'));statsRunNow()}""")
    apa=J("window._statsAPA||''")
    ok('20.25' in apa or 'M = 20.25' in apa or '20.3' in apa,'descriptive statistics use the cleaned age: '+apa[:120])
    # manual add and remove
    J("()=>{document.getElementById('mcCol').value='stress';document.getElementById('mcVal').value='-9';mcAdd()}")
    ok(mean('stress')[0]==9,'a code can be added by hand (stress -9)')
    J("mcDecide('stress','-9','remove')"); ok(mean('stress')[0]==10,'and removed again')
    J("()=>{document.getElementById('mcVal').value='abc';mcAdd()}"); ok(any('must be a number' in t for t in J("window.__t")),'a code that is not a number is refused')
    # no false alarms
    n=load(CLEAN); ok(not n.get('suspect'),'clean data (the test kit sample) raises nothing')
    n=load(TOTALS); ok(not n.get('suspect'),'a real 99 among totals of 30–94 is not pointed out')
    # Hindi
    J("window.__lg=window.getLang;window.getLang=()=>'hi'");load(CSV)
    ok('खाली (उत्तर नहीं) मानें' in J("document.getElementById('statsCols').innerText"),'the choice reads in Hindi')
    J("window.getLang=window.__lg")
    # escaping
    load('id,"a<b>c"\n'+'\n'.join('%d,%d'%(i,v) for i,v in enumerate([1,2,3,4,5,2,3,999],1)))
    ok(not J("!!document.querySelector('#statsCols b b, #statsCols b > b')") and J("!document.querySelector('#statsCols c')"),'column names are shown as text')
    ok(not [e for e in errors if 'favicon' not in e],'no page errors '+str(errors[:3]))
    b.close()
print('FAILED',len(fails)); sys.exit(1 if fails else 0)
