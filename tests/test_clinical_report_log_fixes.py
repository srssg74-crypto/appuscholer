"""Review finding 14: D7 report log inconsistencies.
The "nothing out of range" checkbox must not contradict logged entries, every valid toggle
is logged, and free-text fields (D7 reason, allocation deviation what/why) get a soft warning
when they name a registered allocation arm -- a real way unblinding/PII data can leak into
the record. Saving still succeeds either way (soft check, not a hard block)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='D7 log fixes study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety in first-year students'};studySet(o)")
    # register an allocation plan + commitment with arms 'Intervention'/'Control', so armWarn has
    # something to catch and the deviation log section (which needs a.commit) renders.
    J("const o=studyGet();o.design={type:'experimental',pop:'First-year students',sampling:'Convenience'};designSet('ec',{status:'approved',apprNo:'IEC/2026/12',apprDate:'2026-11-01'});studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value='Two intact sections, chance keeps groups close on baseline anxiety.';document.getElementById('alMethod').value='simple';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Meena Sharma';document.getElementById('alHolder').value='Coordinator';document.getElementById('alArms').value='Intervention,Control';document.getElementById('alBlind').value='both';alSave()")
    ok(J("!!studyGet().alloc.plan")==True,'allocation plan with Intervention/Control arms saved')
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    J("document.getElementById('alSeedSaved').checked=true;document.getElementById('alPubNote').value='Emailed the commitment hash to Dr. Gaur.';alRegister()"); pg.wait_for_timeout(300)
    ok(J("!!studyGet().alloc.commit")==True,'commitment registered (deviation log section needs this to render)')

    # --- D7 clinical report (its own dialog, #crDlg) ---
    J("crOpen()"); pg.wait_for_timeout(200)
    # 1. ticking "nothing out of range" with no entries yet: should succeed and log it
    J("document.getElementById('crNone').checked=true;crNoneSet(true)")
    ok(J("studyGet().cr.none")==True,'none ticked with no entries: allowed')
    ok(J("(studyGet().cr.log||[]).length")==1 and J("studyGet().cr.log[0].kind")=='none ticked','tick is logged')
    # untick it so we can log an entry
    J("document.getElementById('crNone').checked=false;crNoneSet(false)")
    ok(J("studyGet().cr.none")==False,'none unticked')
    ok(J("(studyGet().cr.log||[]).length")==2 and J("studyGet().cr.log[1].kind")=='none unticked','untick is logged too')

    # 2. log a real entry, then try to tick "none" -- must be refused (self-contradiction)
    J("document.getElementById('crCode').value='P-030';document.getElementById('crName').value='FBS';document.getElementById('crReason').value='Mildly high fasting sugar, clinician reviewed and not concerning for this study.';document.getElementById('crBy').value='Dr. Rao';crSave()")
    ok(J("studyGet().cr.entries.length")==1,'entry saved')
    logLenBefore=J("(studyGet().cr.log||[]).length")
    J("document.getElementById('crNone').checked=true;crNoneSet(true)")
    ok(J("studyGet().cr.none")==False,'none ticked while entries exist is refused')
    ok(J("document.getElementById('crNone').checked")==False,'checkbox is reset back to unticked by the refusal')
    ok(J("(studyGet().cr.log||[]).length")==logLenBefore,'the refused attempt is not logged as a toggle')
    msg=J("document.getElementById('crMsg').textContent")
    ok(len(msg)>0 and 'already' in msg.lower(),'refusal explains why: '+msg)

    # 3. a reason naming a registered arm gets armWarn, but still saves
    J("document.getElementById('crCode').value='P-031';document.getElementById('crName').value='BP';document.getElementById('crReason').value='High BP, participant is in the Intervention group and stressed about exams.';document.getElementById('crBy').value='Dr. Rao';crSave()")
    ok(J("studyGet().cr.entries.length")==2,'entry naming an arm still saves (soft check only)')
    ok(J("studyGet().cr.entries[1].armWarn")==True,'entry naming a registered arm is flagged armWarn')
    ok(J("studyGet().cr.entries[0].armWarn")!=True,'the earlier, arm-free entry is not flagged')
    warnTxt=J("document.getElementById('crMsg').textContent")
    ok(len(warnTxt)>0,'a warning message is shown after saving an arm-naming reason')
    crHtml=J("document.getElementById('crDlg').innerHTML")
    ok('⚠' in crHtml,'the rendered D7 log shows a warning badge for the flagged entry')

    # --- allocation deviation log (#alDlg) ---
    # re-render: alDlg's markup was built before the commitment was registered, and alDevHTML()
    # only renders once a.commit is set.
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alDevWhat').value='Gave the Control group list to the wrong research assistant.';document.getElementById('alDevWhy').value='The folder was mislabeled and picked up by mistake during a busy morning.';alDevSave()")
    devs=J("studyGet().alloc.deviations")
    ok(len(devs)==1 and devs[0]['armWarn']==True,'deviation naming an arm in "what" is flagged armWarn')
    devHtml=J("document.getElementById('alDlg').innerHTML")
    ok('⚠' in devHtml,'the rendered deviation log shows a warning badge')
    J("document.getElementById('alDevWhat').value='Enrolled a participant one day late.';document.getElementById('alDevWhy').value='The clinic was closed that day for a public holiday.';alDevSave()")
    devs=J("studyGet().alloc.deviations")
    ok(len(devs)==2 and devs[1].get('armWarn') is not True,'a deviation with no arm name is not flagged')

    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
