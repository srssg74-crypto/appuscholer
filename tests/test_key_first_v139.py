"""Version 139: on a first visit, closing the welcome window opens the key window before the tour; the tour follows after it closes; a student who already has a key goes straight to the tour."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 390, 'height': 800})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    pg.evaluate("LS.rm('appu_demo');LS.rm('appu_kw_first');PROV_ORDER.forEach(x=>{LS.rm('appu_key_'+x);LS.rm('appu_enc_'+x)});window._tourCalls=0;tourStart=function(){window._tourCalls++};const d=document.getElementById('welcomeDlg');d._tour=0;tourAfterWelcome();d.showModal()")
    pg.evaluate("document.getElementById('welcomeDlg').close()"); pg.wait_for_timeout(900)
    ok(pg.evaluate("!!document.getElementById('keyWizDlg')&&document.getElementById('keyWizDlg').open"), 'key window opens first')
    ok(pg.evaluate("window._tourCalls")==0, 'tour waits while the key window is open')
    pg.evaluate("document.getElementById('keyWizDlg').close()"); pg.wait_for_timeout(900)
    ok(pg.evaluate("window._tourCalls")==1, 'tour starts after the key window closes')
    pg.evaluate("window._tourCalls=0;LS.set('appu_key_gemini','AIza'+'x'.repeat(35));const d=document.getElementById('welcomeDlg');d._tour=0;tourAfterWelcome();d.showModal();d.close()"); pg.wait_for_timeout(900)
    ok(pg.evaluate("window._tourCalls")>=1 and not pg.evaluate("document.getElementById('keyWizDlg').open"), 'with a key already saved: straight to the tour, no key window')
    ok(not [e for e in errs if e[0]=='pageerror'], 'no page errors')
    b.close()
sys.exit(1 if fails else 0)
