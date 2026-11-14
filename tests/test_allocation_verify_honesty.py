"""Fix from the 2026-11-14 review, finding 11, part 2: enVerify's listOk rebuilds the list from the
very seed alCheckSeed just confirmed, then compares it against the hash the app itself logged when
building that same list - under ordinary use this cannot fail once seedOk already passed, so on
its own it proves nothing beyond seedOk. The master list upload is the only check here that comes
from outside the app's own record. Verification is now only described as checking an outside
source when a master list was actually given; without one, the "verified" message says plainly
that only the app's own record was checked against itself."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='Verify honesty study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety'};designSet('ec',{status:'approved',apprNo:'IEC/2026/19',apprDate:'2026-11-01'});studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alN').value='12';alRefresh()"%json.dumps(REASON))
    J("document.getElementById('alMethod').value='perm';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Rao';document.getElementById('alHolder').value='Coordinator';document.getElementById('alArms').value='A,B';document.getElementById('alBlind').value='both';alSave()")
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    seed_hex=J("AL_PENDING.seedHex")
    J("document.getElementById('alSeedSaved').checked=true;document.getElementById('alPubNote').value='Emailed the commitment hash to Dr. Gaur on registration day.';alRegister()"); pg.wait_for_timeout(300)
    d=tempfile.mkdtemp(); seedf=os.path.join(d,'seed.txt'); open(seedf,'w').write('Seed (hex): %s\n'%seed_hex)
    J("document.getElementById('enRoleAck').checked=true")
    pg.set_input_files('#enSeed',seedf); pg.wait_for_timeout(600)

    # verify with the seed only, no master list
    pg.set_input_files('#enVerSeed',seedf)
    J("document.getElementById('enVerMaster').value=''")  # ensure no master file selected
    J("enVerify()"); pg.wait_for_timeout(600)
    v1=J("studyGet().alloc.verify")
    ok(v1['ok']==True,'verification still passes on the seed alone')
    ok(v1.get('external')==False,'the record is explicit that no outside master list was checked')
    # enVerify's transient enMsg is overwritten by its own trailing alRender() call (pre-existing,
    # unrelated to this fix), so the persistent status to check is alVerHTML's rendered text
    dlg_html1=J("document.getElementById('alDlg').innerHTML")
    ok('no master list was checked' in dlg_html1.lower(),"the rendered status flags that this verification only checked the app's own record: not found")

    # now verify again WITH a correct master list -- this is the one check that is actually external
    seedf2=os.path.join(d,'seed2.txt'); open(seedf2,'w').write('Seed (hex): %s\n'%seed_hex)
    arms=J("(async()=>await alPermBlocks(ALG.fromHex(%s),12,['A','B']))()"%json.dumps(seed_hex))
    master=os.path.join(d,'master.csv'); open(master,'w').write('envelope_no,arm,study_id\n'+''.join('%d,%s,x\n'%(i+1,a) for i,a in enumerate(arms)))
    pg.set_input_files('#enVerSeed',seedf2); pg.set_input_files('#enVerMaster',master)
    J("enVerify()"); pg.wait_for_timeout(600)
    v2=J("studyGet().alloc.verify")
    ok(v2['ok']==True and v2.get('external')==True,'with a correct master list, verification is marked as externally checked')
    dlg_html2=J("document.getElementById('alDlg').innerHTML")
    ok('no master list was checked' not in dlg_html2.lower(),'once a master list is actually checked, the rendered status no longer carries the self-check-only caveat')

    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
