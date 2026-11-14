"""Fix from the 2026-11-14 review, finding 8: alMakeCommit() checked the ethics record before
letting a commitment candidate be created, but alRegister() never checked it again. Ethics
approval can be edited or withdrawn in Design & Ethics any time while a commitment sits pending
(the student may take a while to save the seed and publish the hash), so a plan could end up
registered -- enrolment unlocked -- with no ethics approval actually standing at the moment it
mattered. alRegister() now re-checks alEthics() and refuses to register until it passes again,
without discarding the pending commitment or its already-saved seed."""
import sys, os, json
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
    J("openSaveAsProject();document.getElementById('sapName').value='Ethics gate study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety'};designSet('ec',{status:'approved',apprNo:'IEC/2026/16',apprDate:'2026-11-01'});studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alN').value='10';alRefresh()"%json.dumps(REASON))
    J("document.getElementById('alMethod').value='simple';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Rao';document.getElementById('alHolder').value='Coordinator';document.getElementById('alArms').value='A,B';document.getElementById('alBlind').value='both';alSave()")

    # ethics approved: commitment can be made
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    ok(J("!!AL_PENDING"),'a commitment candidate is created while ethics is approved')
    J("document.getElementById('alSeedSaved').checked=true;document.getElementById('alPubNote').value='Emailed the commitment hash to Dr. Gaur on registration day.'")

    # ethics withdrawn after the candidate was created, before registration
    J("designSet('ec',{status:'nohuman'})")
    J("alRegister()"); pg.wait_for_timeout(300)
    ok(not J("!!(studyGet().alloc&&studyGet().alloc.commit)"),'registration is refused once the ethics record no longer supports a randomised allocation')
    ok(J("!!AL_PENDING"),'the pending commitment is not thrown away just because ethics was withdrawn')
    msg1=J("document.getElementById('alMsg').textContent")
    ok(len(msg1)>0,'the refusal is explained on screen: '+msg1)

    # ethics restored: the SAME pending commitment registers, no new seed needed
    seed_before=J("AL_PENDING.seedHex")
    J("designSet('ec',{status:'approved',apprNo:'IEC/2026/16',apprDate:'2026-11-01'})")
    J("alRegister()"); pg.wait_for_timeout(300)
    cm=J("studyGet().alloc.commit")
    ok(cm and not J("!!AL_PENDING"),'registration succeeds once ethics is approved again')

    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
