"""Blinding field in the allocation plan: required for a randomised plan, and feeds the methods text and CONSORT 20a/20b."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='Blinding study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety in first-year students'};studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alN').value='40';alRefresh()"%json.dumps(REASON))
    J("document.getElementById('alMethod').value='perm';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Meena Sharma';document.getElementById('alHolder').value='Coordinator';document.getElementById('alArms').value='A,B';alSave()")
    ok(not J("!!(studyGet().alloc&&studyGet().alloc.plan)"),'randomised plan without a blinding choice is not saved')
    J("document.getElementById('alBlind').value='part';alSave()")
    a=J("studyGet().alloc")
    ok(a and a['plan']['blind']=='part','plan saved once blinding is chosen')
    ok(J("subState('C11').s")=='dn','C11 done once blinding is set')
    txt=J("alWriteText(studyGet())")
    ok('Participants were blinded' in txt,'methods text reflects participant-only blinding')
    items={i[0]:i[2] for i in J("alConsort(studyGet())")}
    ok(items['20a'] is True and items['20b'] is False,'20a ticks for participant blinding, 20b does not')
    J("document.getElementById('alBlind').value='both';alSave()")
    items2={i[0]:i[2] for i in J("alConsort(studyGet())")}
    ok(items2['20a'] and items2['20b'],'double blind ticks both 20a and 20b')
    txt2=J("alWriteText(studyGet())")
    ok('double blind' in txt2,'methods text names double blinding')
    J("document.getElementById('alMethod').value='none';document.getElementById('alConc').value='';document.getElementById('alBlind').value='';alSave()")
    ok(J("studyGet().alloc.plan.method")=='none','non-randomised plan still saves without a blinding choice')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
