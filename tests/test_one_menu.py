"""One project menu and one AI control (build 2026.11.10l)."""
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
    vis=lambda sel: J("[...document.querySelectorAll('%s')].filter(e=>e.offsetParent).length"%sel)
    ok(J("document.querySelectorAll('.sidebar-pin').length")==0,'sidebar no longer repeats the project buttons')
    ok(J("!document.getElementById('aiKeyBtn')"),'gold AI button gone; one AI control left')
    ok(vis('#projectBar .btn-new')==1 and vis('#projectBar > button')==1,'project bar: one visible button plus the menu')
    pg.click('#projMenu summary'); pg.wait_for_timeout(200)
    t=J("document.getElementById('projMenu').innerText")
    ok('Research Projects' in t and 'Save as research project' in t and 'Backup' in t,'menu holds the three actions')
    pg.click('#projMenu button:has-text("Research Projects")'); pg.wait_for_timeout(400)
    ok(J("!!document.querySelector('#projectsDlg[open], dialog[open]')"),'Research Projects opens from the menu')
    J("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    pg.click('.prov-toggle'); pg.wait_for_timeout(200)
    ok(J("!!document.getElementById('provSetBtn')"),'AI menu has Key and settings')
    n=J("document.querySelectorAll('#provMenu .ptab[data-p]').length"); ok(n>=5,'provider list still there (%d)'%n)
    pg.click('#provSetBtn'); pg.wait_for_timeout(500)
    ok(J("!!document.querySelector('dialog[open]')"),'Key and settings opens a dialog')
    J("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    J("LS.set('appu_lang','hi');applyLang()"); pg.wait_for_timeout(300)
    ok('प्रोजेक्ट' in J("document.querySelector('#projMenu summary').innerText"),'Hindi menu label')
    ok(not [e for e in errors if 'Failed to load resource' not in str(e)],'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
