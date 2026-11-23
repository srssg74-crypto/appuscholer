"""Version 134: Google AI Studio now gives keys starting with "AQ." (old "AIza" keys stopped in Sept 2026).
The key wizard accepts them as Gemini keys, sends them in the x-goog-api-key header, and explains Google's
ACCESS_TOKEN_TYPE_UNSUPPORTED refusal plainly. The key below is made up."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
FAKE = 'AQ.Ab8Rtest-fake-key_' + 'x' * 40
seen = {}
def gem(mode):
    def h(route):
        seen['hdr'] = route.request.headers.get('x-goog-api-key'); seen['url'] = route.request.url
        if mode == 'ok':
            return route.fulfill(status=200, content_type='application/json', body=json.dumps({'candidates': [{'content': {'parts': [{'text': 'OK'}]}}]}))
        return route.fulfill(status=401, content_type='application/json', body=json.dumps({'error': {'code': 401, 'status': 'UNAUTHENTICATED', 'details': [{'reason': 'ACCESS_TOKEN_TYPE_UNSUPPORTED'}]}}))
    return h
with sync_playwright() as p:
    for mode in ['ok', 'refused']:
        errs = []
        b, pg = harness.new_page(p, errs, {'width': 390, 'height': 844})
        pg.context.route('**/generativelanguage.googleapis.com/**', gem(mode))
        pg.goto(harness.BASE); pg.wait_for_timeout(1500)
        pg.evaluate("keyWizOpen()"); pg.fill('#kwIn', FAKE); pg.evaluate("keyWizCheck()")
        if mode == 'ok':
            ok('Gemini' in pg.inner_text('#kwWho') and not pg.evaluate("kwGo.disabled"), 'an AQ. key is recognised as a Google Gemini key')
            ok('AQ.' in pg.get_attribute('#kwIn', 'placeholder'), 'the box tells students a Google key starts with AQ.')
        pg.click('#kwGo'); pg.wait_for_timeout(1500)
        out = pg.inner_text('#kwOut')
        if mode == 'ok':
            ok('AI is on' in out and pg.evaluate("localStorage.getItem('appu_key_gemini')") == FAKE, 'test passes and the key is saved: %r' % out)
            ok(seen.get('hdr') == FAKE and 'key=' not in seen.get('url', ''), 'the key travels in the x-goog-api-key header, not the address')
        else:
            ok('known problem' in out and 'Groq' in out, "Google's refusal is explained with a way forward: %r" % out[:90])
        ok(not [e for e in errs if e[0] == 'pageerror'], 'no page errors (%s)' % mode)
        b.close()
    # going out to Google and coming back
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 390, 'height': 844})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    pg.evaluate("window.open=()=>null;keyWizOpen()")
    ok('back arrow' in pg.inner_text('#keyWizDlg .kw-back'), 'the window tells students how to come back from Google')
    pg.click('#keyWizDlg .btn-purple.btn-sm'); pg.wait_for_timeout(200)
    pg.reload(); pg.wait_for_timeout(3500)
    ok(pg.evaluate("!!document.getElementById('keyWizDlg')&&keyWizDlg.open"), 'after a reload the key window is open again')
    ok(pg.evaluate("document.activeElement&&document.activeElement.id")=='kwIn', 'the key box is ready to paste into')
    pg.evaluate("keyWizDlg.querySelector('button[aria-label]').click()"); pg.wait_for_timeout(200)
    pg.reload(); pg.wait_for_timeout(3500)
    ok(not pg.evaluate("!!document.getElementById('keyWizDlg')&&keyWizDlg.open"), 'closing the window with the cross stops it coming back')
    ok(not [e for e in errs if e[0] == 'pageerror'], 'no page errors (return)')
    b.close()
sys.exit(1 if fails else 0)
