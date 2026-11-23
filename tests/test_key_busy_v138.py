"""Version 138: a 503 'high demand' answer while testing a Gemini key saves the key instead of rejecting it; a 403 still rejects."""
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
    key = 'AIza' + 'x' * 35
    for msg, expect in [('{"error":{"code":503,"message":"This model is currently experiencing high demand.","status":"UNAVAILABLE"}}', True), ('{"error":{"code":403,"message":"API key not valid","status":"PERMISSION_DENIED"}}', False)]:
        pg.evaluate("LS.rm('appu_key_gemini');keyWizOpen()")
        pg.evaluate("(()=>{window.callAIOnce=async function(){throw new Error(%r)}})()" % msg)
        pg.evaluate("document.getElementById('kwIn').value=%r;keyGuessProv(%r)" % (key, key))
        pg.evaluate("keyWizSave()"); pg.wait_for_timeout(600)
        saved = pg.evaluate("!!LS.get('appu_key_gemini')")
        ok(saved == expect, 'busy=%s key saved=%s' % (expect, saved))
    ok(not [e for e in errs if e[0] == 'pageerror'], 'no page errors')
    b.close()
sys.exit(1 if fails else 0)
