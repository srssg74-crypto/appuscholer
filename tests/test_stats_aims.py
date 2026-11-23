"""Version 127: the Statistics Lab starts from the student's aim; the test list narrows and a reason is shown."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
data = "group,score\\n" + "\\n".join("%s,%d" % ('Hostel' if i % 2 else 'Home', 20 + (i * 7) % 15) for i in range(30))
with sync_playwright() as p:
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 1366, 'height': 860})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    pg.evaluate("document.getElementById('statsDlg').showModal()")
    pg.evaluate("document.getElementById('statsPaste').value='%s';statsParse()" % data); pg.wait_for_timeout(500)
    ok(pg.evaluate("document.querySelectorAll('#slAims .sl-aim').length") == 6, 'six aims shown above the test list')
    pg.click('.sl-aim:nth-child(4)'); pg.wait_for_timeout(300)
    vis = pg.evaluate("[...document.getElementById('statsTest').options].filter(o=>!o.hidden).map(o=>o.value)")
    ok(set(vis) == {'pearson', 'spearman', 'pointbis', 'chisq', 'gof', 'binom'} and pg.evaluate("document.getElementById('statsTest').value") == 'pearson', 'Related? narrows to correlation and chi-square, Pearson chosen: %s' % vis)
    ok('Pearson' in pg.inner_text('.sl-why'), 'the reason is shown in one line')
    pg.click('.sl-why a'); pg.wait_for_timeout(300)
    ok(pg.evaluate("[...document.getElementById('statsTest').options].every(o=>!o.hidden)"), 'Show all tests brings the full list back')
    pg.click('.sl-aim:nth-child(2)'); pg.wait_for_timeout(300)
    pg.evaluate("statsRun()"); pg.wait_for_timeout(600)
    ok('t(' in pg.inner_text('#statsResults') or 't =' in pg.inner_text('#statsResults'), 'the chosen test still runs')
    pg.evaluate("toggleLang()"); pg.wait_for_timeout(200); pg.evaluate("slAimsRender()")
    ok('आप क्या जानना चाहते हैं' in pg.inner_text('#slAims'), 'aims in Hindi')
    bad = [e for e in errs if e[0] == 'pageerror']
    ok(not bad, 'no page errors %s' % bad[:3])
    b.close()
sys.exit(1 if fails else 0)
