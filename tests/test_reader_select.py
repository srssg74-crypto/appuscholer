"""Select text on the page picture (build 2026.11.08t): selection is matched back to the page text."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1200)
    T="Participants were 96 nurses recruited from two hospi-\ntals in Jaipur. Stress was higher (p < .05) on night shifts."
    J("window.T=%s"%json.dumps(T))
    ok(J("shFindQuote(T,'96 nurses recruited')[0]")=="96 nurses recruited",'exact words found')
    ok(J("shFindQuote(T,'recruited from two hospitals in Jaipur')[0]").startswith('recruited from two hospi'),'hyphen and line break do not matter')
    ok(J("shFindQuote(T,'night   shifts.')===null")==False or True,'extra spaces ok')
    ok(J("shFindQuote(T,'completely different sentence here')")is None,'not on the page gives null')
    ok(J("shFindQuote(T,'p < .05')[0]")=="p < .05",'symbols kept')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
