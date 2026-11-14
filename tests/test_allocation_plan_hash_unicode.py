"""Fix from the 2026-11-14 review, finding 7: the registered plan's hash (bound into the v2
commitment) used JSON.stringify in the browser, which keeps non-ASCII text (Hindi maker/holder
names, Hindi notes) as literal UTF-8. Python's json.dumps defaults to ensure_ascii=True, escaping
the same text to \\uXXXX sequences and hashing to a different value. A commitment made from a
bilingual plan -- the normal case in this app -- could never have been reproduced or checked by
the standalone Python engine. randomise.py's _canonical() now passes ensure_ascii=False so both
sides hash the same plan to the same value. This test drives the real app UI with Hindi maker and
holder names and checks the plan hash it actually registers against the Python engine's own
plan_hash() for the identical plan dict."""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
REASON='Two intact sections of one college, so chance keeps the groups close on baseline anxiety.'
MAKER='डॉ. मीना शर्मा'
HOLDER='समन्वयक'
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Unicode plan hash study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety'};designSet('ec',{status:'approved',apprNo:'IEC/2026/15',apprDate:'2026-11-01'});studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alN').value='10';alRefresh()"%json.dumps(REASON))
    J("document.getElementById('alMethod').value='simple';document.getElementById('alConc').value='central';document.getElementById('alMaker').value=%s;document.getElementById('alHolder').value=%s;document.getElementById('alArms').value='A,B';document.getElementById('alBlind').value='both';alSave()"%(json.dumps(MAKER),json.dumps(HOLDER)))
    plan=J("studyGet().alloc.plan")
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    app_plan_hash=J("AL_PENDING.planHash")

    py=subprocess.run([sys.executable,'-c','''
import sys, json
sys.path.insert(0, "tools/randomise")
import randomise as R
plan = json.loads(sys.argv[1])
print(R.plan_hash(plan))
''', json.dumps(plan)], cwd=os.path.join(os.path.dirname(__file__),'..'), capture_output=True, text=True)
    ok(py.returncode==0, 'the Python engine ran cleanly: '+py.stderr)
    py_plan_hash=py.stdout.strip()
    ok(app_plan_hash==py_plan_hash, 'the app\'s plan hash for a Hindi maker/holder plan matches the Python engine: app=%s py=%s'%(app_plan_hash,py_plan_hash))

    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
