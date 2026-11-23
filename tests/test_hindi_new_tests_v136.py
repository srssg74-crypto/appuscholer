"""Version 136: the four new Statistics Lab tests and their guide branches read in Hindi when the language is Hindi, and in English again after switching back."""
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
    b, pg = harness.new_page(p, errs, {'width': 1366, 'height': 900})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    pg.evaluate("LS.set('appu_lang','hi');applyLang();document.getElementById('statsDlg').showModal();document.getElementById('tgPanel').style.display='block'")
    pg.wait_for_timeout(300)
    opts = pg.evaluate("[...document.querySelectorAll('#statsTest option')].map(o=>o.textContent.trim())")
    ok(any('लक्ष्य अनुपात' in o for o in opts) and any('गिनती वाला परिणाम' in o for o in opts) and any('दो-समूह' in o for o in opts) and any('ratings की' in o for o in opts), 'the four new options show in Hindi')
    pg.evaluate("window._tg={goal:'predict'};tgRender()")
    ok('गिनती' in pg.inner_text('#tgPanel'), 'guide: the count answer is in Hindi')
    pg.evaluate("window._tg={goal:'predict',prdOut:'count'};tgRender()")
    t = pg.inner_text('#tgPanel')
    ok('परिणाम एक गिनती है' in t and 'dispersion' in t, 'guide: Poisson reason and assumptions in Hindi')
    pg.evaluate("window._tg={goal:'counts',cntDes:'prop'};tgRender()")
    ok('लक्ष्य अनुपात' in pg.inner_text('#tgPanel'), 'guide: binomial branch in Hindi')
    pg.evaluate("document.getElementById('statsTest').value='binom';statsFieldsRender()")
    ok('लक्ष्य अनुपात (0 और 1 के बीच)' in pg.inner_text('#statsFields'), 'field labels in Hindi')
    ok('जैसे yes' in (pg.evaluate("document.getElementById('sf_pos').getAttribute('placeholder')") or ''), 'placeholder in Hindi')
    pg.evaluate("LS.set('appu_lang','en');applyLang();statsFieldsRender()")
    ok('Target proportion (between 0 and 1)' in pg.inner_text('#statsFields'), 'switching back restores English')
    pg.evaluate("window._tg={goal:'counts',cntDes:'prop'};tgRender()")
    ok('Exact binomial test' in pg.inner_text('#tgPanel') and 'लक्ष्य' not in pg.inner_text('#tgPanel'), 'guide back in English')
    bad = [e for e in errs if e[0] == 'pageerror']
    ok(not bad, 'no page errors %s' % bad[:3])
    b.close()
sys.exit(1 if fails else 0)
