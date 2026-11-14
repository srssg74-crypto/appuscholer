"""Second review, finding 10: enReveal (made async on this branch), alMakeCommit and alRegister still
wrote back a copy of the study taken before their awaits. The reviewer's repro: slow the HMAC, reveal
P1, enrol P2 while the list is rebuilding; P2 vanished when the reveal resolved. Likewise a card edit
during alMakeCommit was reverted. Both must now survive, and a study switch mid-await must write
nothing into the newly active study. Second review, finding 2: a forged AL_PENDING.planHash must not
register."""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
REASON='Two intact sections of one college, so chance keeps the groups close on baseline anxiety.'
SLOW_SIGN="window.__origSign=window.__origSign||crypto.subtle.sign.bind(crypto.subtle);crypto.subtle.sign=function(){const a=arguments,orig=window.__origSign;return new Promise(res=>setTimeout(()=>res(orig.apply(null,a)),%d))};true"
SLOW_DIGEST="window.__origDigest=window.__origDigest||crypto.subtle.digest.bind(crypto.subtle);crypto.subtle.digest=function(){const a=arguments,orig=window.__origDigest;return new Promise(res=>setTimeout(()=>res(orig.apply(null,a)),%d))};true"
RESTORE="if(window.__origSign)crypto.subtle.sign=window.__origSign;if(window.__origDigest)crypto.subtle.digest=window.__origDigest;true"
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Race study 2';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety'};designSet('ec',{status:'approved',apprNo:'IEC/2026/18',apprDate:'2026-11-01'});studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alN').value='30';alRefresh()"%json.dumps(REASON))
    J("document.getElementById('alMethod').value='simple';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Rao';document.getElementById('alHolder').value='Coordinator';document.getElementById('alArms').value='A,B';document.getElementById('alBlind').value='both';alSave()")

    # --- alMakeCommit: a card edit during the hashing awaits must survive ---
    J(SLOW_DIGEST%150)
    # pg.evaluate awaits a returned promise, so these in-flight calls end with ;true to return at once
    J("alMakeCommit();true")  # two delayed digests inside
    pg.wait_for_timeout(50)
    J("const o=studyGet();o.alloc.card.n=99;studySet(o)")  # concurrent edit
    pg.wait_for_timeout(800)
    ok(J("studyGet().alloc.card.n")==99,'a card edit made during alMakeCommit is not reverted by its write')
    ok(J("!!AL_PENDING"),'the pending commitment was still created')
    ok(any(e['kind']=='commitment created' for e in J("studyGet().alloc.log")),'the commitment-created log entry still lands')
    J(RESTORE)

    # --- finding 2: a forged planHash on AL_PENDING must not register ---
    real_plan_hash=J("AL_PENDING.planHash")
    J("(async()=>{AL_PENDING.planHash='00'.repeat(32);const seed=ALG.fromHex(AL_PENDING.seedHex),ph=ALG.fromHex(AL_PENDING.planHash),pre=new TextEncoder().encode('appuscholar-commit-v2:');const buf=new Uint8Array(pre.length+64);buf.set(pre);buf.set(seed,pre.length);buf.set(ph,pre.length+32);AL_PENDING.hash=await alHash(buf)})()")
    pg.wait_for_timeout(200)
    J("document.getElementById('alSeedSaved').checked=true;document.getElementById('alPubNote').value='Emailed the commitment hash to Dr. Gaur on registration day.';alRegister()"); pg.wait_for_timeout(400)
    ok(not J("!!studyGet().alloc.commit"),'a pending commitment whose planHash is not the hash of the stored plan is refused (it used to register with planHash 0000...)')
    ok(J("AL_PENDING")==None,'the forged pending object is discarded')
    msg=J("document.getElementById('alMsg').textContent")
    ok('plan hash' in msg.lower(),'the refusal names the plan hash: '+msg)

    # a genuine commitment registers, and its recorded planHash is the real plan hash
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    seed_hex=J("AL_PENDING.seedHex")
    J("document.getElementById('alSeedSaved').checked=true;document.getElementById('alPubNote').value='Emailed the commitment hash to Dr. Gaur on registration day.';alRegister()"); pg.wait_for_timeout(300)
    ok(J("!!studyGet().alloc.commit") and J("studyGet().alloc.commit.planHash")==real_plan_hash,'a genuine commitment registers with the real plan hash')

    # --- enReveal: an enrolment during the reveal's rebuild must survive (the reviewer's repro) ---
    d=tempfile.mkdtemp(); seedf=os.path.join(d,'seed.txt'); open(seedf,'w').write('Seed (hex): %s\n'%seed_hex)
    J("document.getElementById('enRoleAck').checked=true;document.getElementById('enN').value='30'")
    pg.set_input_files('#enSeed',seedf); pg.wait_for_timeout(800)
    ok(J("AL_SEED!==null && AL_BUILT_N===30"),'seed loaded, list of 30')
    J("document.getElementById('enCode').value='P1';enEnrol()")
    # the stream is HMAC-keyed once, then one SHA-256 digest per 32 bytes of randomness (eight for 30
    # positions), so the await window to widen is digest: 30 ms each gives a rebuild of ~250 ms
    J(SLOW_DIGEST%30)
    J("enReveal('P1');true")
    pg.wait_for_timeout(20)
    J("document.getElementById('enCode').value='P2';enEnrol()")
    codes_during=[e['code'] for e in J("studyGet().alloc.enrol")]
    pg.wait_for_timeout(1500)
    codes_after=[e['code'] for e in J("studyGet().alloc.enrol")]
    ok(codes_during==['P1','P2'],'P2 is enrolled while the reveal is in flight: '+json.dumps(codes_during))
    ok(codes_after==['P1','P2'],'P2 is still enrolled after the reveal resolves (it used to be dropped): '+json.dumps(codes_after))
    ok(any(e['kind']=='reveal' for e in J("studyGet().alloc.log")),'the reveal itself is still logged')
    shown=J("document.getElementById('enMsg').textContent")
    ok(shown.startswith('Arm for P1'),'the arm is still shown: '+repr(shown))
    J(RESTORE)

    # --- a study switch during a reveal writes nothing into the new study and shows no arm ---
    J(SLOW_DIGEST%30)
    J("enReveal('P2');true")
    pg.wait_for_timeout(20)
    before_other=J("(()=>{openSaveAsProject();document.getElementById('sapName').value='Other study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){};return JSON.stringify(studyGet().alloc||null)})()")
    pg.wait_for_timeout(1500)
    after_other=J("JSON.stringify(studyGet().alloc||null)")
    ok(before_other==after_other,'the in-flight reveal from the first study wrote nothing into the newly opened study')
    ok(not J("document.getElementById('enMsg')&&document.getElementById('enMsg').textContent.startsWith('Arm for P2')"),'the arm for P2 is not shown after the switch')
    J(RESTORE)
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
