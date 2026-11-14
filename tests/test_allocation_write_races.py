"""Fix from the 2026-11-14 review, finding 10: enLoadSeed(), enVerify() and alLock() each captured
the study record at the top of the function, did several awaits (reading a file, hashing), and
then wrote that stale copy back at the end. Anything else that wrote to the study in that window
-- a deviation logged from another tab, an enrolment -- was silently lost, overwritten by the
stale copy. All three now re-read the study immediately before their final write. This test
widens the await window (by delaying crypto.subtle.digest(), which every hashing path here --
alHash, ALG.sha, and so the AlStream keystream and alCheckSeed -- routes through) and performs a
concurrent write during it, then checks that write survived."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='Race study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety'};designSet('ec',{status:'approved',apprNo:'IEC/2026/17',apprDate:'2026-11-01'});studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alN').value='10';alRefresh()"%json.dumps(REASON))
    J("document.getElementById('alMethod').value='simple';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Rao';document.getElementById('alHolder').value='Coordinator';document.getElementById('alArms').value='A,B';document.getElementById('alBlind').value='both';alSave()")
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    seed_hex=J("AL_PENDING.seedHex")
    J("document.getElementById('alSeedSaved').checked=true;document.getElementById('alPubNote').value='Emailed the commitment hash to Dr. Gaur on registration day.';alRegister()"); pg.wait_for_timeout(300)

    # widen the await window: delay crypto.subtle.digest by 150ms per call, for the rest of this page
    J("window.__origDigest=crypto.subtle.digest.bind(crypto.subtle);crypto.subtle.digest=function(algo,data){const orig=window.__origDigest;return new Promise(res=>setTimeout(()=>res(orig(algo,data)),150))};true")

    d=tempfile.mkdtemp(); seedf=os.path.join(d,'seed.txt'); open(seedf,'w').write('Seed (hex): %s\n'%seed_hex)
    J("document.getElementById('enRoleAck').checked=true")
    pg.set_input_files('#enSeed',seedf)  # kicks off enLoadSeed(), now with several 150ms-delayed hashes
    pg.wait_for_timeout(100)  # still inside the delayed awaits
    J("document.getElementById('alDevWhat').value='Switched holder mid-enrolment';document.getElementById('alDevWhy').value='The original holder became unavailable and a backup took over immediately.';alDevSave()")
    pg.wait_for_timeout(2000)  # let enLoadSeed's several delayed hashes finish and its write land
    rec=J("studyGet().alloc")
    ok(len(rec.get('deviations',[]))==1,'the deviation logged during the race is not lost by the later write from enLoadSeed')
    ok(any(e['kind']=='list built' for e in rec['log']),'the write from enLoadSeed itself still lands')
    ok(J("AL_SEED")==seed_hex,'the seed is still loaded correctly after the race')

    # same widened window for enVerify (also hashes via crypto.subtle.digest)
    J("window.__origDigest2=window.__origDigest;crypto.subtle.digest=function(algo,data){const orig=window.__origDigest2;return new Promise(res=>setTimeout(()=>res(orig(algo,data)),150))};true")
    master=os.path.join(d,'master.csv')
    arms=J("(async()=>await alSimple(ALG.fromHex(%s),10,['A','B']))()"%json.dumps(seed_hex))
    open(master,'w').write('envelope_no,arm,study_id\n'+''.join('%d,%s,x\n'%(i+1,a) for i,a in enumerate(arms)))
    pg.set_input_files('#enVerSeed',seedf); pg.set_input_files('#enVerMaster',master)
    J("enVerify()")
    pg.wait_for_timeout(100)
    J("document.getElementById('alDevWhat').value='Second concurrent note during verification';document.getElementById('alDevWhy').value='Testing that verification does not clobber a deviation logged while it runs.';alDevSave()")
    pg.wait_for_timeout(2000)
    rec2=J("studyGet().alloc")
    ok(len(rec2.get('deviations',[]))==2,'the second deviation, logged during the enVerify race window, is not lost either')
    ok(rec2.get('verify',{}).get('ok')==True,'the verification result itself still lands correctly')

    # alLock: still delayed, its own hash (fingerprint) gives one more await window
    J("document.getElementById('alCov').value='';alLock()")
    pg.wait_for_timeout(50)
    J("document.getElementById('alDevWhat').value='Third note during locking';document.getElementById('alDevWhy').value='Testing that locking does not clobber a deviation logged while it runs.';alDevSave()")
    pg.wait_for_timeout(1000)
    rec3=J("studyGet().alloc")
    ok(len(rec3.get('deviations',[]))==3,'a deviation logged during the alLock await is not lost')
    ok(rec3.get('lock') and len(rec3['lock']['fingerprint'])==64,'the lock itself still lands correctly')

    # restore the native digest and double-check alLock's race-hardened "no second lock" guard
    J("crypto.subtle.digest=window.__origDigest;true")
    before=J("(studyGet().alloc.log||[]).filter(e=>e.kind==='analysis locked').length")
    J("alLock()"); pg.wait_for_timeout(300)
    after=J("(studyGet().alloc.log||[]).filter(e=>e.kind==='analysis locked').length")
    ok(before==1 and after==1,'calling alLock again after it is already locked never writes a second lock entry')

    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
