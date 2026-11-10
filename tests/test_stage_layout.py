"""Stages 1-4 give the step and tool the wider column; writing and review give it to the draft (build 2026.11.10n)."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='L';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    W=lambda s:(J("apGoStage('%s')"%s),pg.wait_for_timeout(500),J("document.querySelector('.tool-main').getBoundingClientRect().width"))[2]
    wi,wl,wd,wc,ww,wr=[W(s) for s in ['idea','lit','design','collect','writing','review']]
    ok(min(wi,wl,wd,wc)>max(ww,wr)+80,'tool column is wider in stages 1-4 (%d,%d,%d,%d vs %d,%d)'%(wi,wl,wd,wc,ww,wr))
    ok(J("document.getElementById('docPane').getBoundingClientRect().width")>=560,'draft stays wide in writing')
    W('idea'); ok(J("document.getElementById('docPane').getBoundingClientRect().width")>=420,'draft stays usable in stage 1')
    J("LS.set('appu_dock_w_tool','350')"); W('lit'); ok(abs(J("document.querySelector('.tool-main').getBoundingClientRect().width")-350)<12,'a dragged width wins for stages 1-4')
    ww2=W('writing'); ok(abs(ww2-ww)<12,'and does not change the writing stages')
    ok(not [e for e in errors if 'Failed to load resource' not in str(e)],'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
