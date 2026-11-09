"""Word and LaTeX downloads sit in one Download menu (build 2026.11.09c)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    ok(J("document.getElementById('dlMenu').open")==False,'menu starts closed')
    pg.click('#dlMenu summary'); ok(J("document.getElementById('dlMenu').open")==True,'opens on click')
    ok(J("document.getElementById('dlMenu').innerText.includes('Download (Word)') && document.getElementById('dlMenu').innerText.includes('LaTeX file')"),'Word and LaTeX inside')
    J("window.__w=0;downloadDoc=function(){window.__w++};0")
    pg.click("#dlMenu button[data-i18n='download_btn']"); ok(J("window.__w")==1 and J("document.getElementById('dlMenu').open")==False,'Word item runs and closes the menu')
    J("LS.set('appu_lang','hi');applyLang()"); pg.wait_for_timeout(300)
    ok('डाउनलोड' in J("document.querySelector('#dlMenu summary').innerText"),'Hindi label')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
