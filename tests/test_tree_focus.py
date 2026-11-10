"""The left tree opens the current stage and folds the others (build 2026.11.10k)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors,{'width':1366,'height':768}); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='T';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    open_=lambda: J("STAGES.filter(s=>{const g=document.querySelector('.stage-group[data-stage=\"'+s+'\"]');return g&&!g.classList.contains('collapsed')})")
    for st in ['idea','lit','design','collect','writing','review']:
        J("apGoStage('%s')"%st); pg.wait_for_timeout(250)
        ok(open_()==[st],'only %s is open (%s)'%(st,open_()))
    J("toggleStageGroup('idea')"); ok(set(open_())=={'review','idea'},'a stage can still be opened by hand')
    J("showTool('words')"); pg.wait_for_timeout(200); ok(open_()==['writing'],'opening a tool focuses its stage')
    ok(J("document.querySelectorAll('.stage-group').length")>=5,'all stage groups still in the tree')
    ok(not [e for e in errors if 'Failed to load resource' not in str(e)],'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
