"""Stage 9: methods text is drafted from recorded values only, with brackets where the record is silent; CONSORT items reflect the record, including 20a/20b from the plan's blinding field."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='Write study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety in first-year students'};o.design={type:'experimental',pop:'First-year students in two colleges',sampling:'Convenience'};designSet('ec',{status:'approved',apprNo:'IEC/2026/12',apprDate:'2026-11-01'});studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alFactors').value='baseline anxiety';document.getElementById('alN').value='60';alRefresh()"%json.dumps(REASON))
    J("document.getElementById('alMethod').value='perm';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Meena Sharma';document.getElementById('alHolder').value='Coordinator';document.getElementById('alArms').value='Intervention,Control';document.getElementById('alParams').value='blocks of 4, 6 and 8';document.getElementById('alBlind').value='both';alSave()")
    txt=J("alWriteText(studyGet())")
    ok('permuted blocks' in txt and 'Intervention and Control' in txt,'methods text names the method and the arms')
    ok('[Allocation was not concealed' not in txt and 'central, computer-generated list' in txt,'concealment sentence matches the plan')
    ok('[Name]' in txt or 'Dr. Meena Sharma' in txt,'list maker appears from the record')
    ok('undefined' not in txt and 'null' not in txt,'no undefined or null leaks into the text')
    items=J("alConsort(studyGet())")
    st={i[0]:i[2] for i in items}
    ok(st['17a'] and st['17b'] and st['18'],'17a, 17b and 18 are ticked from the plan')
    ok(st['20a'] and st['20b'],'20a and 20b tick when the plan records double blinding')
    ok(st['21a'] is False,'21a waits for the analysis lock')
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    J("document.getElementById('alSeedSaved').checked=true;alRegister()"); pg.wait_for_timeout(300)
    txt2=J("alWriteText(studyGet())")
    ok('SHA-256 commitment' in txt2 and 'before enrolment' in txt2,'commitment sentence appears once registered')
    ok('did not randomise' in J("alWriteText({alloc:{plan:{method:'none'}}})"),'non-randomised study gets the no-randomisation text')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
