"""Document header: Outline label, AI-written parts label, one Viva menu (build 2026.11.10m)."""
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
    pg.evaluate("showTool('words')"); pg.wait_for_timeout(300)
    ok('Outline' in J("document.querySelector('.docbar').innerText") and 'Book' not in J("document.querySelector('.docbar').innerText"),'Book is now Outline')
    ok('Show AI-written parts' in J("document.getElementById('aiHighlightBtn').innerText"),'AI text renamed')
    ok(J("[...document.querySelectorAll('.toolbar button')].filter(b=>/Viva/.test(b.innerText)).length")==1,'viva buttons sit inside one menu')
    pg.click('#vivaMenuBtn'); pg.wait_for_timeout(300)
    t=J("document.getElementById('vivaChooseDlg').innerText"); ok('One examiner question' in t and 'Full mock viva' in t,'chooser offers both')
    pg.click('#vivaBtn'); pg.wait_for_timeout(500)
    ok(J("!!document.getElementById('vivaDlg')&&document.getElementById('vivaDlg').open")or J("!!document.querySelector('dialog[open]')"),'one-question viva opens')
    J("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    pg.click('#vivaMenuBtn'); pg.wait_for_timeout(300); pg.click('#mvBtn'); pg.wait_for_timeout(500)
    ok(J("!!document.querySelector('dialog[open]')"),'mock viva opens')
    J("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    J("LS.set('appu_lang','hi');applyLang()"); pg.wait_for_timeout(300)
    ok('अभ्यास' in J("document.getElementById('vivaMenuBtn').innerText"),'Hindi viva menu label')
    ok(not [e for e in errors if 'Failed to load resource' not in str(e)],'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
