"""Gates C3 (sample size needs its basis) and C4 (unconfirmed scale permission is never free)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("openSaveAsProject();document.getElementById('sapName').value='Gate study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety'};o.design={type:'correlational',pop:'college students',n:'85',vars:[{name:'Anxiety',role:'outcome',type:'score',scale:'GAD7'},{name:'Sleep hours',role:'predictor',type:'score',scale:'own'}]};studySet(o)")
    ok(J("ssComplete(studyGet().design)")==False and J("subState('C3').s")=='ns','a typed number alone does not complete C3')
    # power calculator: correlation r=.30, power .80 -> 85 (checked in code in the ledger)
    J("pwOpen();document.getElementById('pwTest').value='corr';pwTestChange();document.getElementById('pwSolve').value='n';try{pwSolveChange()}catch(e){}")
    J("document.getElementById('pwEffect').value='0.30';document.getElementById('pwPow').value='0.80';document.getElementById('pwAlpha').value='0.05';document.getElementById('pwDrop').value='0';pwRun()")
    ok(J("window._pwLast&&window._pwLast.n")==85,'power calculator gives 85 for r = .30: %s'%J("window._pwLast&&window._pwLast.n"))
    J("pwUse()")
    ok(J("!(studyGet().design.ss||{}).effSrc"),'use refused without the effect-size source')
    J("document.getElementById('pwEffSrc').value='r = .30 in Sharma et al. (2021)';pwUse()")
    ok(J("ssComplete(studyGet().design)")==True and J("subState('C3').s")=='dn','with inputs and source, C3 is done')
    ok('Sharma et al. (2021)' in J("ssDraftText(studyGet().design)"),'draft text carries the source: '+J("ssDraftText(studyGet().design)")[:160])
    J("const o=studyGet();o.design.n='120';studySet(o)")
    ok(J("ssComplete(studyGet().design)")==False,'changing the number away from the calculation reopens C3')
    # dropout: recruit number is accepted
    J("document.getElementById('pwDrop').value='15';pwRun();document.getElementById('pwEffSrc').value='r = .30 in Sharma et al. (2021)';pwUse()")
    ok(J("studyGet().design.n")=='100' and J("ssComplete(studyGet().design)")==True,'with 15 percent dropout the plan takes the recruit number: '+str(J("studyGet().design.n")))
    # other bases need a reason
    J("const o=studyGet();o.design.ss={basis:'qual',why:'short'};studySet(o)")
    ok(J("ssComplete(studyGet().design)")==False,'qualitative basis needs a 20+ character reason')
    J("const o=studyGet();o.design.ss={basis:'qual',why:'Twelve interviews: narrow aim, specific sample, strong dialogue (Malterud et al. 2016)'};studySet(o)")
    ok(J("ssComplete(studyGet().design)")==True,'qualitative basis with reason completes C3')
    # plan dialog keeps the basis
    J("spOpen()"); pg.wait_for_timeout(200)
    ok(J("document.getElementById('spSsBasis').value")=='qual','plan dialog shows the basis')
    J("spSave()")
    ok(J("studyGet().design.ss.basis")=='qual' and J("ssComplete(studyGet().design)")==True,'saving the plan keeps the basis')
    # C4
    ok(J("scaleCheck().ok")==True and J("subState('C4').s")=='dn','GAD-7 (free) passes C4')
    J("const o=studyGet();o.design.vars.push({name:'Life satisfaction',role:'predictor',type:'score',scale:'SWLS'});studySet(o)")
    ok(J("scaleCheck().ok")==False and J("subState('C4').s")!='dn','restricted SWLS without wording blocks C4: '+json.dumps(J("scaleCheck().issues")))
    J("slOpen();slPick('SWLS')"); pg.wait_for_timeout(200)
    J("()=>{document.getElementById('slPasteTxt').value=[1,2,3,4,5].map(i=>'Statement '+i).join('\\n');slSaveText('SWLS')}")
    J("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    ok(J("scaleCheck().ok")==True,'SWLS with wording from the owner page passes')
    ok(J("SCALE_LINKS.find(x=>x.short==='MSPSS').access")=='unknown' and J("SCALE_LINKS.find(x=>x.short==='EPDS').access")=='unknown','MSPSS and EPDS shown as permission not confirmed')
    J("slOpen()"); pg.wait_for_timeout(200)
    ok('Permission not confirmed' in J("document.getElementById('slList').innerText"),'catalogue shows the not-confirmed label')
    J("document.querySelectorAll('dialog[open]').forEach(d=>d.close());subOpen('design','C3')"); pg.wait_for_timeout(200)
    pg.screenshot(path='/tmp/claude-0/-home-claude/d540b351-a2df-5fa6-9a88-226a4c6e6a4f/scratchpad/gate-c3.png')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
