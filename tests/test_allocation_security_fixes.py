"""Fixes from the 2026-11-14 review: list hash not brute-forceable, commitment hash recomputed and re-rolls logged, a publish note required before registration."""
import sys, os, json, time
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
    J("openSaveAsProject();document.getElementById('sapName').value='Security fix study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety'};designSet('ec',{status:'approved',apprNo:'IEC/2026/12',apprDate:'2026-11-01'});studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alN').value='10';alRefresh()"%json.dumps(REASON))
    J("document.getElementById('alMethod').value='simple';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Meena Sharma';document.getElementById('alHolder').value='Coordinator';document.getElementById('alArms').value='A,B';document.getElementById('alBlind').value='both';alSave()")

    # finding 2: re-rolling the seed is logged, not invisible
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    first_hash=J("AL_PENDING.hash")
    J("alMakeCommit()"); pg.wait_for_timeout(300)  # re-roll before registering
    second_hash=J("AL_PENDING.hash")
    ok(first_hash!=second_hash,'re-rolling produces a different candidate seed')
    rolls=[e for e in J("studyGet().alloc.log") if e['kind']=='commitment created']
    ok(len(rolls)==2,'both commitment attempts are logged, even the discarded one')
    ok('re-created' in rolls[1]['text'],'the second entry says it is a re-creation')

    # finding 2: a forged pending hash is refused at registration (hash is recomputed, not trusted)
    J("AL_PENDING.hash='00'.repeat(32)")
    J("document.getElementById('alSeedSaved').checked=true;document.getElementById('alPubNote').value='Emailed to supervisor.';alRegister()"); pg.wait_for_timeout(300)
    ok(not J("!!studyGet().alloc.commit"),'a forged commitment hash is refused, not trusted')

    # finding 2: registration requires a publish note
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    seed_hex=J("AL_PENDING.seedHex")
    J("document.getElementById('alSeedSaved').checked=true;document.getElementById('alPubNote').value='';alRegister()"); pg.wait_for_timeout(300)
    ok(not J("!!studyGet().alloc.commit"),'registration refused without a publish note')
    J("document.getElementById('alPubNote').value='Emailed the hash to Dr. Gaur, 14 Nov 2026.';alRegister()"); pg.wait_for_timeout(300)
    cm=J("studyGet().alloc.commit")
    ok(cm and cm.get('publishedTo'),'registration succeeds with a publish note, and it is stored')

    # finding 1: the list hash cannot be reproduced without the seed (not brute-forceable from the record alone)
    d=__import__('tempfile').mkdtemp()
    seedf=os.path.join(d,'seed.txt'); open(seedf,'w').write('Seed (hex): %s\n'%seed_hex)
    J("document.getElementById('enRoleAck').checked=true")
    pg.set_input_files('#enSeed',seedf); pg.wait_for_timeout(600)
    ok(J("AL_SEED")==seed_hex and J("typeof AL_LIST")=='undefined','seed is loaded but the built list is not kept as a standing variable')
    built=[e for e in J("studyGet().alloc.log") if e['kind']=='list built'][-1]
    alist=J("(async()=>await alSimple(ALG.fromHex(%s),10,['A','B']))()"%json.dumps(seed_hex))
    plain_sha=J("alHash(new TextEncoder().encode(JSON.stringify(%s)))"%json.dumps(alist))
    ok(built['hash']!=plain_sha,'the stored list hash is not a plain, unkeyed SHA-256 of the list')
    # brute force over the small space of 2-arm 10-length lists should NOT find a match without the seed
    import itertools
    cand_hashes=set()
    for bits in itertools.product(['A','B'],repeat=10):
        cand_hashes.add(J("alHash(new TextEncoder().encode(JSON.stringify(%s)))"%json.dumps(list(bits))))
        if len(cand_hashes)>50: break  # keep the probe fast; any match at all would be the bug
    ok(built['hash'] not in cand_hashes,'no unkeyed brute-force guess over candidate lists matches the stored hash')
    # finding 3: loading the seed for enrolment requires the role-separation acknowledgment, and it is logged
    J("AL_SEED=null;AL_BUILT_N=0")
    d2=__import__('tempfile').mkdtemp(); seedf2=os.path.join(d2,'seed2.txt'); open(seedf2,'w').write('Seed (hex): %s\n'%seed_hex)
    J("document.getElementById('enRoleAck').checked=false")
    pg.set_input_files('#enSeed',seedf2); pg.wait_for_timeout(400)
    ok(J("AL_SEED")==None,'loading the seed is refused until the role-separation box is ticked')
    J("document.getElementById('enRoleAck').checked=true")
    pg.set_input_files('#enSeed',seedf2); pg.wait_for_timeout(600)
    ok(J("AL_SEED")==seed_hex,'loading proceeds once the box is ticked')
    acks=[e for e in J("studyGet().alloc.log") if e['kind']=='seed loaded for enrolment']
    ok(len(acks)>=1,'the acknowledgment is written to the log, not silent')

    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
