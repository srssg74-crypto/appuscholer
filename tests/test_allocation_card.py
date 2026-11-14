"""C11 allocation card and plan: suggestion after the reason, validation, append-only log, sub-step state."""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
S=tempfile.mkdtemp()+'/'
REASON='Two intact sections of one college, so chance keeps the groups close on baseline anxiety.'
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Allocation study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety in first-year students'};o.design={type:'experimental',pop:'First-year students in two colleges',sampling:'Convenience'};studySet(o)")
    J("subOpen('design','C11')"); pg.wait_for_timeout(200)
    ok(J("subState('C11').s")!='dn','C11 not done at start')
    # review finding 13: this used to be `... or True`, an assertion that could never fail no
    # matter what the page returned. The dialog is created lazily by alOpen() (called next), so
    # the honest check at this point is that it does not exist yet.
    ok(not J("!!document.getElementById('alDlg')"),'allocation dialog does not exist before alOpen() creates it')
    J("alOpen()"); pg.wait_for_timeout(200)
    ok(J("document.getElementById('alRecBox').textContent.indexOf('Write your reason first')>=0"),'no suggestion before the reason')
    J("document.getElementById('alReason').value='short';alRefresh()")
    ok(J("document.getElementById('alRecBox').textContent.indexOf('Suggestion')<0"),'suggestion stays hidden with a short reason')
    J("document.getElementById('alReason').value=%s;document.getElementById('alFactors').value='baseline anxiety';alRefresh()"%json.dumps(REASON))
    ok(J("document.getElementById('alRecBox').textContent.indexOf('Stratified')>=0 || document.getElementById('alRecBox').textContent.indexOf('stratified')>=0"),'one factor suggests stratified blocks after the reason')
    J("document.getElementById('alMethod').value='perm';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='';alSave()")
    ok(not J("!!(studyGet().alloc&&studyGet().alloc.plan)"),'randomised plan without list maker is not saved')
    J("document.getElementById('alMaker').value='Dr. Meena Sharma, supervisor';document.getElementById('alHolder').value='Project coordinator';document.getElementById('alArms').value='A,B';document.getElementById('alBlind').value='both';alSave()")
    a=J("studyGet().alloc")
    ok(a and a['plan']['method']=='perm' and len(a['log'])==1 and a['log'][0]['kind']=='created','first save writes one created entry')
    ok(J("subState('C11').s")=='dn','C11 done with reason and plan')
    J("document.getElementById('alMethod').value='strat';alSave()")
    a=J("studyGet().alloc")
    ok(len(a['log'])==2 and a['log'][1]['kind']=='changed' and 'method perm → strat' in a['log'][1]['text'],'a changed method appends a log entry, earlier entries stay')
    ok(a['log'][0]['method']=='perm','earlier log entry is unchanged')
    J("document.getElementById('alMethod').value='none';document.getElementById('alConc').value='';alSave()")
    ok(J("studyGet().alloc.plan.method")=='none','non-randomised plan saved without concealment')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    pg.screenshot(path=S+'allocation_card.png')
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
