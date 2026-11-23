"""Version 133: on a phone the page goes quiet once loaded (the bottom bar used to rebuild 16 times a second,
which made taps unreliable on iPhones), and the consent screen has finger-sized tick boxes and buttons.
Runs as a first-time student from the kit, without the harness's test code."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
ROOT = harness.BASE.rsplit('/', 1)[0] + '/'
with sync_playwright() as p:
    dev = dict(p.devices['iPhone 13']); dev.pop('default_browser_type', None); dev['viewport'] = {'width': 390, 'height': 664}
    b = p.chromium.launch(); ctx = b.new_context(**dev, service_workers='block')
    harness.prepare(ctx)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.goto(ROOT + 'index.html?kit=1'); pg.wait_for_timeout(3000)
    pg.evaluate("window.__mut=0;new MutationObserver(m=>window.__mut+=m.length).observe(document.body,{subtree:true,childList:true})")
    pg.wait_for_timeout(3000)
    n = pg.evaluate("__mut")
    ok(n < 5, 'page is quiet while the consent screen waits: %d changes in 3 s' % n)
    sz = pg.evaluate("[...document.querySelectorAll('#termsChecks input')].map(i=>i.getBoundingClientRect().width)")
    ok(all(w >= 22 for w in sz), 'tick boxes are at least 22 px: %s' % sz)
    rows = pg.evaluate("[...document.querySelectorAll('#termsChecks label')].map(l=>l.getBoundingClientRect().height)")
    ok(all(h >= 44 for h in rows), 'each consent row is a 44 px tap target: %s' % rows)
    ok(pg.evaluate("getComputedStyle(document.querySelector('#termsDlg .dlg-body>div')).overflowY") == 'visible', 'one scroll area on a phone, not a box inside a box')
    go = pg.evaluate("(()=>{const r=termsGo.getBoundingClientRect();return r.bottom<=innerHeight&&r.top>=0})()")
    ok(go, 'Continue stays on screen')
    pg.tap('label:has(#termsAge) span'); pg.tap('label:has(#termsAgree) span'); pg.tap('#termsGo'); pg.wait_for_timeout(600)
    ok(not pg.evaluate("termsDlg.open"), 'tapping the two rows and Continue moves on')
    ok(not errs, 'no page errors %s' % errs[:2])
    b.close()
sys.exit(1 if fails else 0)
