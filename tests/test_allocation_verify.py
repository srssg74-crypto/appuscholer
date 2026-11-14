"""Stage 8: verification recomputes the list from the seed and checks it against the logged hash and the master list; analysis lock needs the factors as covariates and a passed verification, and is written once."""
import sys, os, json, tempfile
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
    J("openSaveAsProject();document.getElementById('sapName').value='Verify study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety in first-year students'};o.design={type:'experimental',pop:'First-year students in two colleges',sampling:'Convenience'};designSet('ec',{status:'approved',apprNo:'IEC/2026/12',apprDate:'2026-11-01'});studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alFactors').value='baseline anxiety';document.getElementById('alN').value='12';alRefresh()"%json.dumps(REASON))
    J("document.getElementById('alMethod').value='perm';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Meena Sharma';document.getElementById('alHolder').value='Coordinator';document.getElementById('alArms').value='A,B';alSave()")
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    seed_hex=J("AL_PENDING.seedHex")
    J("document.getElementById('alSeedSaved').checked=true;alRegister()"); pg.wait_for_timeout(300)
    d=tempfile.mkdtemp()
    seedf=os.path.join(d,'seed.txt'); open(seedf,'w').write('Seed (hex): %s\n'%seed_hex)
    pg.set_input_files('#enSeed',seedf); pg.wait_for_timeout(600)
    arms=J("AL_LIST")
    master=os.path.join(d,'master_list.csv')
    open(master,'w').write('envelope_no,arm,study_id\n'+''.join('%d,%s,x\n'%(i+1,a) for i,a in enumerate(arms)))
    # tampered master list: one row swapped
    tampered=os.path.join(d,'tampered.csv')
    t=list(arms); t[0]='B' if t[0]=='A' else 'A'
    open(tampered,'w').write('envelope_no,arm,study_id\n'+''.join('%d,%s,x\n'%(i+1,a) for i,a in enumerate(t)))
    pg.set_input_files('#enVerSeed',seedf); pg.set_input_files('#enVerMaster',tampered); J("enVerify()"); pg.wait_for_timeout(600)
    ok(J("studyGet().alloc.verify.ok")==False and J("studyGet().alloc.verify.masterOk")==False,'a tampered master list fails verification')
    J("document.getElementById('alCov').value='baseline anxiety';alLock()"); pg.wait_for_timeout(200)
    ok(J("!studyGet().alloc.lock"),'lock refused after a failed verification')
    wrong=os.path.join(d,'wrong.txt'); open(wrong,'w').write('Seed (hex): %s\n'%('ee'*32))
    pg.set_input_files('#enVerSeed',wrong); J("enVerify()"); pg.wait_for_timeout(400)
    ok(J("studyGet().alloc.verify.seedOk")==False,'a wrong seed fails verification')
    pg.set_input_files('#enVerSeed',seedf); pg.set_input_files('#enVerMaster',master); J("enVerify()"); pg.wait_for_timeout(600)
    ok(J("studyGet().alloc.verify.ok")==True and J("studyGet().alloc.verify.masterOk")==True,'the right seed and master list verify')
    ok(any(e['kind']=='verified' for e in J("studyGet().alloc.log")) and any(e['kind']=='verification failed' for e in J("studyGet().alloc.log")),'both results are in the log')
    J("document.getElementById('alCov').value='first-year students';alLock()"); pg.wait_for_timeout(200)
    ok(J("!studyGet().alloc.lock"),'lock refused when a stratifying factor is not named as a covariate')
    J("document.getElementById('alCov').value='baseline anxiety, first-year students';alLock()"); pg.wait_for_timeout(300)
    lk=J("studyGet().alloc.lock")
    ok(lk and lk['verifiedAtLock'] and len(lk['fingerprint'])==64,'lock written with a fingerprint after verification')
    J("alLock()"); pg.wait_for_timeout(200)
    ok(sum(1 for e in J("studyGet().alloc.log") if e['kind']=='analysis locked')==1,'a second lock is not written')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
