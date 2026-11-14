"""Fix from the 2026-11-14 review, finding 6: the reveal button for an enrolled participant used
to be built as onclick="enReveal('<code>')" with the code only HTML-entity-escaped. That escaping
stops the string breaking the surrounding HTML attribute, but the browser decodes entities in an
attribute value before handing it to the JS parser, so a code containing a quote could still break
out of the JS string literal and run arbitrary script. The button is now a plain data attribute
read by a delegated click listener, so the code is never turned into executable JS text."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='Reveal safety study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety'};designSet('ec',{status:'approved',apprNo:'IEC/2026/14',apprDate:'2026-11-01'});studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alN').value='10';alRefresh()"%json.dumps(REASON))
    J("document.getElementById('alMethod').value='simple';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Meena Sharma';document.getElementById('alHolder').value='Coordinator';document.getElementById('alArms').value='A,B';document.getElementById('alBlind').value='both';alSave()")
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    seed_hex=J("AL_PENDING.seedHex")
    J("document.getElementById('alSeedSaved').checked=true;document.getElementById('alPubNote').value='Emailed the commitment hash to Dr. Gaur on registration day.';alRegister()"); pg.wait_for_timeout(300)
    d=tempfile.mkdtemp(); seedf=os.path.join(d,'seed.txt'); open(seedf,'w').write('Seed (hex): %s\n'%seed_hex)
    J("document.getElementById('enRoleAck').checked=true")
    pg.set_input_files('#enSeed',seedf); pg.wait_for_timeout(600)

    # a participant code built to break out of onclick="enReveal('<code>')" if it were still built that way
    window_before = J("window.__pwned")
    EVIL = "x');window.__pwned=true;('"
    J("document.getElementById('enCode').value=%s;enEnrol()"%json.dumps(EVIL))
    pg.wait_for_timeout(300)
    ok(J("!!(studyGet().alloc.enrol||[]).find(e=>e.code===%s)"%json.dumps(EVIL)),'the participant with the crafted code is enrolled')
    ok(J("window.__pwned")!=True,'rendering the enrolled list does not execute injected script just by being on screen')

    # the delegated reveal button still works for an ordinary code, and for the crafted one
    J("document.getElementById('enCode').value='P-NORM';enEnrol()"); pg.wait_for_timeout(200)
    btn_count_normal=J("document.querySelectorAll('[data-reveal-code=\"P-NORM\"]').length")
    ok(btn_count_normal==1,'the reveal button for a normal code renders as a data attribute, no inline onclick with the code in it')
    J("document.querySelector('[data-reveal-code=\"P-NORM\"]').click()"); pg.wait_for_timeout(300)
    ok(J("document.getElementById('enMsg').textContent").startswith('Arm for P-NORM'),"clicking the delegated button still reveals the right participant's arm")
    ok(not J("document.getElementById('alDlg').innerHTML").__contains__("onclick=\"enReveal("),'no reveal button in the rendered dialog is built from an inline onclick string anymore')

    evil_btn=J("[...document.querySelectorAll('button')].some(x=>x.getAttribute('data-reveal-code')===%s)"%json.dumps(EVIL))
    ok(evil_btn,'the crafted code still gets a working reveal button, just via the safe attribute')
    J("[...document.querySelectorAll('button')].find(x=>x.getAttribute('data-reveal-code')===%s).click()"%json.dumps(EVIL))
    pg.wait_for_timeout(300)
    ok(J("window.__pwned")!=True,'clicking the reveal button for the crafted code does not execute the injected script')
    ok('Arm for' in J("document.getElementById('enMsg').textContent"),'reveal still functions for the crafted code, safely')

    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
