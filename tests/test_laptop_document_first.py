"""Laptop layout (1292x673): the document gets room, the second row of writing tools is folded, Focus gives the whole screen (build 2026.11.10v)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors,viewport={'width':1292,'height':673}); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    H=lambda: J("(()=>{const e=document.getElementById('editor').getBoundingClientRect();return [Math.round(e.height),Math.round(e.width)]})()")
    h,w=H(); ok(h>=200 and w>=500,'editor is %dx%d at 1292x673 (was about 100x388)'%(w,h))
    ok(J("getComputedStyle(document.getElementById('draftFirstBtn')).display")=='none','second row of writing tools is folded')
    J("tbMoreToggle(true)"); ok(J("getComputedStyle(document.getElementById('draftFirstBtn')).display")!='none','More opens it')
    J("tbMoreToggle(false)")
    pg.click('#focusBtn'); pg.wait_for_timeout(300)
    h2,w2=H(); ok(h2>=h+80 and w2>=900,'Focus gives the document %dx%d'%(w2,h2))
    ok(J("getComputedStyle(document.querySelector('.tool-sidebar')).display")=='none','side panel hidden in Focus')
    ok('Back' in J("document.getElementById('focusBtn').innerText"),'Focus button says how to return')
    pg.click('#focusBtn'); pg.wait_for_timeout(300)
    ok(J("getComputedStyle(document.querySelector('.tool-sidebar')).display")!='none','panels come back')
    ok(not [e for e in errors if 'Failed to load resource' not in str(e)],'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
