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

    # --- second review, finding 14: the arm check itself ---
    # crArmWarn reads the registered plan's arms; swap them in place to test each label set
    def warn(arms,text):
        return J("(()=>{const o=studyGet();o.alloc.plan.arms=%s;studySet(o);return crArmWarn(%s)})()"%(json.dumps(arms),json.dumps(text)))
    ok(warn('A,B','Mildly high fasting sugar, a known vegetarian; clinician agreed it is not significant.')==False,'default arms A,B: an ordinary English sentence containing the word "a" is NOT flagged (this used to flag every sentence)')
    ok(warn('A,B','Participant is in arm A and stressed about exams.')==True,'default arms: "arm A" is flagged')
    ok(warn('A,B','He is in the B group, says the RA.')==True,'default arms: "B group" is flagged')
    ok(warn('A,B','Took a BP reading at 9 am.')==False,'default arms: "a BP" is not flagged')
    ok(warn('उपचार,नियंत्रण','प्रतिभागी उपचार समूह में है।')==True,'Hindi arm names are flagged when named (\\b without the u flag never matched Devanagari)')
    ok(warn('उपचार,नियंत्रण','प्रतिभागी का उपचारक बदला।')==False,'a longer Hindi word that merely starts with the arm label is not flagged')
    ok(warn('Drug+,Placebo','Switched to Drug+ after week 2.')==True,'a label ending in punctuation (Drug+) is flagged')
    ok(warn('Intervention,Control','We controlled for age and sex.')==False,'"controlled" does not match the arm "Control"')
    # third review: group words need their own left boundary, matras are part of a word, short labels need context
    ok(warn('A,B','The study could harm a participant if continued.')==False,'"harm a" is not "arm A"')
    ok(warn('A,B','The alarm a nurse heard went off twice.')==False,'"alarm a" is not "arm A"')
    ok(warn('A,B','His condition a week later was stable.')==False,'"condition a" is not arm A')
    ok(warn('कम,ज़्यादा','रक्त में कमी देखी गई।')==False,'a Devanagari vowel sign is part of the word: "कमी" does not contain the arm "कम"')
    ok(warn('मल,कुछ','कोमल त्वचा पर दाने।')==False,'"कोमल" does not contain the arm "मल"')
    ok(warn('कम,ज़्यादा','कम समूह का प्रतिभागी है।')==True,'"कम समूह" is flagged')
    ok(warn('Yes,No','There was no fever on day three.')==False,'a two-letter label that is an English word ("No") is not flagged bare')
    ok(warn('Yes,No','Moved to the No arm by mistake.')==True,'but "the No arm" is flagged')
    J("(()=>{const o=studyGet();o.alloc.plan.arms='Intervention,Control';studySet(o)})()")

    # logging an entry while "none" is ticked clears it, and that clearing is logged
    J("(()=>{const o=studyGet();o.cr={entries:[],none:true,log:[]};studySet(o);crRender()})()")
    J("document.getElementById('crCode').value='P-040';document.getElementById('crName').value='TSH';document.getElementById('crReason').value='Slightly raised TSH, clinician reviewed, not relevant to the study question.';document.getElementById('crBy').value='Dr. Rao';crSave()")
    cr=J("studyGet().cr")
    ok(cr['none']==False and len(cr['entries'])==1,'an entry saved while none was ticked clears none')
    ok(any(e['kind']=='none unticked' and 'automatically' in e['text'] for e in cr['log']),'the automatic clearing is logged, so the toggle history has no gap')

    # an old record with none:true AND entries (made before the guard) is not accepted as complete
    J("(()=>{const o=studyGet();o.cr.none=true;studySet(o)})()")
    ok(J("crOk()")==False,'crOk refuses a record that has "nothing out of range" ticked alongside entries')
    J("(()=>{const o=studyGet();o.cr.none=false;studySet(o)})()")
    ok(J("crOk()")==True,'and accepts it once the tick is cleared')

    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
