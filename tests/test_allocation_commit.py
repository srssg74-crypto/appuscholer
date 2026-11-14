"""C11 commitment (stage 5): hash-only record, seed kept out of the record, plan locked after registration, enrolment gate."""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
REASON='Two intact sections of one college, so chance keeps the groups close on baseline anxiety.'
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Commit study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety in first-year students'};o.design={type:'experimental',pop:'First-year students in two colleges',sampling:'Convenience'};studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alFactors').value='baseline anxiety';alRefresh()"%json.dumps(REASON))
    J("document.getElementById('alMethod').value='perm';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Meena Sharma';document.getElementById('alHolder').value='Coordinator';alSave()")
    ok(J("alEnrolOK(studyGet())")==False,'enrolment blocked before commitment')
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    ok(J("AL_PENDING!==null") and J("!studyGet().alloc.commit"),'pending commitment is not in the record until registered')
    ok('alSeedSaved' in J("document.getElementById('alDlg').innerHTML"),'seed checkbox shown')
    seed_hex=J("AL_PENDING.seedHex"); pend_hash=J("AL_PENDING.hash")
    ok(hashlib.sha256(b'appuscholar-commit-v1:'+bytes.fromhex(seed_hex)).hexdigest()==pend_hash,'hash equals SHA-256(prefix + seed) as the spec says')
    J("document.getElementById('alSeedSaved').checked=false;alRegister()"); pg.wait_for_timeout(200)
    ok(J("!studyGet().alloc.commit"),'registration refused without saving the seed file')
    J("document.getElementById('alSeedSaved').checked=true;alRegister()"); pg.wait_for_timeout(300)
    a=J("studyGet().alloc")
    ok(a.get('commit') and len(a['commit']['hash'])==64,'commitment stored as a 64-character hash')
    ok(J("studyGet().alloc.commit.hash")==pend_hash,'stored hash is the one generated')
    ok(J("alEnrolOK(studyGet())")==True,'enrolment allowed after registration')
    rec=json.dumps(J("studyGet()"))
    ok('Seed (hex)' not in rec and 'seedHex' not in rec,'seed is not in the study record')
    ok(J("typeof AL_PENDING")=='object' and J("AL_PENDING")==None,'pending seed cleared after registration')
    ok(any(e['kind']=='registered' for e in a['log']),'registration written to the log')
    J("document.getElementById('alMethod').value='mini';alSave()")
    ok(J("studyGet().alloc.plan.method")=='perm','registered plan cannot be changed (hard stop)')
    ok(J("document.getElementById('alMsg').textContent").startswith('This plan was registered'),'hard stop message shown')
    J("alMakeCommit()"); pg.wait_for_timeout(200)
    ok(J("AL_PENDING===null"),'no second commitment is started once registered')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
