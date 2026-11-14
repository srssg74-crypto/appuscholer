"""Fix from the 2026-11-14 review, finding 11, part 1: reloading the seed with a smaller n than
the number already enrolled left previously-enrolled positions outside the newly-built, shorter
list, so Reveal silently returned no arm for them. enLoadSeed() now refuses to rebuild smaller
than the current enrolment count."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='N mismatch study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety'};designSet('ec',{status:'approved',apprNo:'IEC/2026/18',apprDate:'2026-11-01'});studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alN').value='20';alRefresh()"%json.dumps(REASON))
    J("document.getElementById('alMethod').value='simple';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Rao';document.getElementById('alHolder').value='Coordinator';document.getElementById('alArms').value='A,B';document.getElementById('alBlind').value='both';alSave()")
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    seed_hex=J("AL_PENDING.seedHex")
    J("document.getElementById('alSeedSaved').checked=true;document.getElementById('alPubNote').value='Emailed the commitment hash to Dr. Gaur on registration day.';alRegister()"); pg.wait_for_timeout(300)

    d=tempfile.mkdtemp(); seedf=os.path.join(d,'seed.txt'); open(seedf,'w').write('Seed (hex): %s\n'%seed_hex)
    J("document.getElementById('enRoleAck').checked=true;document.getElementById('enN').value='20'")
    pg.set_input_files('#enSeed',seedf); pg.wait_for_timeout(600)
    ok(J("AL_BUILT_N")==20,'the list is first built at n=20')

    # enrol 15 participants, positions 1..15
    for i in range(15):
        J("document.getElementById('enCode').value='P-%03d';enEnrol()"%(i+1))
    ok(len(J("studyGet().alloc.enrol"))==15,'15 participants enrolled against the n=20 list')

    # try to reload the seed with a smaller n than enrolled -- this used to silently break Reveal
    # for positions 11-15
    J("AL_SEED=null;AL_BUILT_N=0;document.getElementById('enN').value='10';document.getElementById('enRoleAck').checked=true")
    pg.set_input_files('#enSeed',seedf); pg.wait_for_timeout(600)
    ok(J("AL_SEED")==None,'reloading with n smaller than the 15 already enrolled is refused')
    ok('already' in J("document.getElementById('enMsg').textContent").lower() or '15' in J("document.getElementById('enMsg').textContent"),'the refusal explains why: '+J("document.getElementById('enMsg').textContent"))

    # reloading with n equal to or larger than enrolled still works, and Reveal still works for
    # a late position (a second copy of the same seed file, since Chromium does not re-fire
    # 'change' when set_input_files is given the identical path twice)
    seedf2=os.path.join(d,'seed2.txt'); open(seedf2,'w').write('Seed (hex): %s\n'%seed_hex)
    J("document.getElementById('enN').value='20';document.getElementById('enRoleAck').checked=true")
    pg.set_input_files('#enSeed',seedf2); pg.wait_for_timeout(600)
    ok(J("AL_SEED")==seed_hex and J("AL_BUILT_N")==20,'reloading at the original n=20 still works')
    J("enReveal('P-015')"); pg.wait_for_timeout(300)
    ok(J("document.getElementById('enMsg').textContent").startswith('Arm for P-015'),'Reveal for the last enrolled participant (position 15) still works, not silently undefined')

    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
