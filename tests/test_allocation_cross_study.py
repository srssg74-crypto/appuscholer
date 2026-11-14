"""Finding 4 (review, 2026-11-14): allocation state must not bleed across studies when the active project changes."""
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
    # Study A: full register + load seed + enrol
    J("openSaveAsProject();document.getElementById('sapName').value='Study A';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    idA=J("getActiveProjectId()")
    J("const o=studyGet();o.idea={topic:'Study A topic'};designSet('ec',{status:'approved',apprNo:'IEC/A/1',apprDate:'2026-11-01'});studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alN').value='10';alRefresh()"%json.dumps(REASON))
    J("document.getElementById('alMethod').value='simple';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='M';document.getElementById('alHolder').value='H';document.getElementById('alArms').value='A,B';document.getElementById('alBlind').value='both';alSave()")
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    seedA=J("AL_PENDING.seedHex")
    J("document.getElementById('alSeedSaved').checked=true;document.getElementById('alPubNote').value='Emailed to Dr. Gaur.';alRegister()"); pg.wait_for_timeout(300)
    d=tempfile.mkdtemp(); sf=os.path.join(d,'seedA.txt'); open(sf,'w').write('Seed (hex): %s\n'%seedA)
    J("document.getElementById('enRoleAck').checked=true")
    pg.set_input_files('#enSeed',sf); pg.wait_for_timeout(600)
    J("document.getElementById('enCode').value='A-01';enEnrol()"); pg.wait_for_timeout(200)
    ok(J("AL_SEED")==seedA,'study A has its seed loaded')

    # Switch to a brand-new Study B, with no allocation of its own yet
    J("document.getElementById('alDlg').close()")
    J("openSaveAsProject();document.getElementById('sapName').value='Study B';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    idB=J("getActiveProjectId()")
    ok(idA!=idB,'studies A and B are distinct projects')
    ok(J("AL_SEED")==None and J("AL_BUILT_N")==0,"study A's seed is cleared from memory on switching to study B")
    ok(not J("!!(studyGet().alloc&&studyGet().alloc.commit)"),"study B's own record carries no commitment copied from study A or scratch")
    ok(not J("!!(studyGet().alloc&&studyGet().alloc.enrol&&studyGet().alloc.enrol.length)"),"study B's own record carries no enrolment copied from study A or scratch")

    # Enrolling in B without a commitment of its own is not even offered as an option
    J("alOpen()"); pg.wait_for_timeout(200)
    ok(J("!document.getElementById('enCode')"),'study B has no enrolment field until it registers its own commitment')
    J("document.getElementById('alDlg').innerHTML.indexOf('Register the commitment first')>=0")
    has_enrol_route=J("!!document.getElementById('enCode')")
    ok(not has_enrol_route,'no route to enrol exists for study B before its own commitment is registered')

    # Switching back to A: A's own record is intact and unaffected
    J("document.getElementById('alDlg').close();setActiveProject('%s')"%idA); pg.wait_for_timeout(300)
    ok(J("(studyGet().alloc.enrol||[]).some(e=>e.code==='A-01')"),"study A's own enrolment is still there after the round trip")
    ok(J("AL_SEED")==None,"switching back to A does not silently restore A's seed in memory either")
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
