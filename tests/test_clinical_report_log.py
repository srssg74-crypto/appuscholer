"""D7 out-of-range clinical reports: judgement stays with the human, append-only, no names or values stored."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
REASON='Mildly low haemoglobin, participant is a known vegetarian; clinician agreed it is not significant.'
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Report log study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety in first-year students'};studySet(o)")
    J("subOpen('collect','D7')"); pg.wait_for_timeout(200)
    ok(J("subState('D7').s")!='dn','D7 not done at start')
    J("crOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('crCode').value='P-014';document.getElementById('crName').value='haemoglobin';document.getElementById('crReason').value=%s;document.getElementById('crBy').value='Dr. Shweta Gaur';crSave()"%json.dumps(REASON))
    ok(J("(studyGet().cr||{entries:[]}).entries.length")==1 and J("studyGet().cr.entries[0].decision")=='ns','entry saved with the student judgement')
    ok(J("subState('D7').s")=='dn','D7 done after one judged entry')
    J("document.getElementById('crCode').value='P-021';document.getElementById('crName').value='FEV1';document.getElementById('crDec').value='sig';document.getElementById('crReason').value=%s;document.getElementById('crBy').value='Ravi';crSave()"%json.dumps('Low FEV1 with breathlessness reported, referred to the participant doctor today.'))
    ok(J("studyGet().cr.entries.length")==1,'significant entry refused without a named clinician')
    J("document.getElementById('crClin').value='Dr. Anil Verma, chest physician';crSave()")
    ok(J("studyGet().cr.entries.length")==2,'significant entry saved once a clinician is named')
    rec=json.dumps(J("studyGet().cr"))
    ok('"value"' not in rec and 'haemoglobin' in rec,'test name stored, no value field')
    J("document.getElementById('crDec').value='sig';crWarn()")
    ok('doctor' in J("document.getElementById('crWarn').textContent"),'significant decision shows the referral warning')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
