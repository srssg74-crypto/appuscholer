"""Version 131 tester pass: a student who opens Appuscholar from the test kit (?kit=1) gets in with no
access code or account until KIT_PASS_END; everyone else still meets the access gate; after the end
date the pass stops working. Runs WITHOUT the harness's test code, as a real first-time student would."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

ROOT = harness.BASE.rsplit('/', 1)[0] + '/'
LATE = "(()=>{const D=Date,t=new D('2027-01-02T10:00:00').getTime();window.Date=class extends D{constructor(...a){super(...(a.length?a:[t]))}static now(){return t}}})();"

def fresh(p, late=False):
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, service_workers='block')
    harness.prepare(ctx)
    if late: ctx.add_init_script(LATE)
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    return b, pg, errs

gate = "document.getElementById('loginDlg').open"
with sync_playwright() as p:
    b, pg, errs = fresh(p)
    pg.goto(ROOT + 'index.html?kit=1'); pg.wait_for_timeout(2500)
    ok(not pg.evaluate(gate), 'kit link opens the app with no access-code box')
    ok(pg.evaluate("document.getElementById('licenseBadge').textContent") == 'Test version', 'header says Test version')
    ok('kit=1' not in pg.url, 'the kit marker is removed from the address bar')
    pg.goto(ROOT + 'index.html'); pg.wait_for_timeout(2000)
    ok(not pg.evaluate(gate), 'reopening the plain link on the same phone still gets in')
    ok(not errs, 'no page errors %s' % errs[:2])
    b.close()

    b, pg, errs = fresh(p)
    pg.goto(ROOT + 'index.html'); pg.wait_for_timeout(2500)
    ok(pg.evaluate(gate), 'without the kit link the access gate still shows')
    b.close()

    b, pg, errs = fresh(p, late=True)
    pg.goto(ROOT + 'index.html?kit=1'); pg.wait_for_timeout(2500)
    ok(pg.evaluate(gate), 'after the end date the kit link no longer skips the gate')
    b.close()

    b, pg, errs = fresh(p)
    pg.goto(ROOT + 'kit.html'); pg.wait_for_timeout(800)
    ok(pg.evaluate("/const APP='[^']*\\?kit=1'/.test(document.documentElement.innerHTML)"), 'kit buttons point at the tester link')
    b.close()
sys.exit(1 if fails else 0)
