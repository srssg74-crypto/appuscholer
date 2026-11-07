"""Fact check beside the AI summary on the Reading shelf (build 2026.11.08b)."""
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
    J("window.__p={title:'s',pages:AP_SAMPLE.slice()}")
    good="Aim: exam worry. Method: 60 recruited, 58 analysed. Finding: d = 0.61."
    h=J("shFactCheck(__p,%r)"%good)
    ok('Every number in the AI summary appears' in h,'true numbers pass')
    ok('58 analysed' in h and 'Exam Worry Scale' in h,'sample and scale shown from the paper')
    h2=J("shFactCheck(__p,'Method: 120 students, alpha 0.93.')")
    ok('120' in h2 and '0.93' in h2 and 'not in the paper text' in h2,'invented numbers are flagged')
    ok(J("shFactCheck({title:'x',pages:['','']},'No numbers here.')").find('Every number')>0,'empty PDF does not crash')
    ok(not errors,'no page errors: %s'%errors)
    b.close()
print('failures:',len(fails))
