"""AI rewrite shown as tracked changes; each change can be switched off; Accept inserts only the changes left on."""
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
    pg.evaluate("setEditorHTML('<p>The students was very anxious before there exams in the college.</p>')")
    pg.evaluate("""()=>{const p=editor.querySelector('p'),r=document.createRange();r.selectNodeContents(p);const s=getSelection();s.removeAllRanges();s.addRange(r);savedRange=r.cloneRange()}""")
    pg.evaluate("setSug('The students were very anxious before their exams at the college.')")
    n = pg.evaluate("document.querySelectorAll('#aiOut button.trk').length")
    ok(n == 3, 'three changes shown as buttons (%s)' % n)
    t = pg.inner_text('#aiOut')
    ok('3 changes, 3 on' in t, 'count line shown')
    ok(pg.evaluate("window._sug") == 'The students were very anxious before their exams at the college.', 'all on gives the AI text')
    idx = pg.evaluate("[...document.querySelectorAll('#aiOut button.trk')].map(b=>+b.dataset.i)")
    pg.evaluate("trkToggle(%d)" % idx[2])
    ok(pg.evaluate("window._sug") == 'The students were very anxious before their exams in the college.', 'switching one off keeps the original words there: %r' % pg.evaluate("window._sug"))
    ok('3 changes, 2 on' in pg.inner_text('#aiOut'), 'count updates')
    pg.evaluate("acceptAI()"); pg.wait_for_timeout(200)
    ok(pg.evaluate("editor.innerText.trim()") == 'The students were very anxious before their exams in the college.', 'Accept inserts only the changes left on')
    # all off leaves the text alone
    pg.evaluate("""()=>{const p=editor.querySelector('p'),r=document.createRange();r.selectNodeContents(p);const s=getSelection();s.removeAllRanges();s.addRange(r);savedRange=r.cloneRange()}""")
    pg.evaluate("setSug('The pupils were really anxious before their exams in the college.')"); pg.evaluate("trkAll(false)")
    before = pg.evaluate("editor.innerHTML")
    pg.evaluate("acceptAI()"); pg.wait_for_timeout(200)
    ok(pg.evaluate("editor.innerHTML") == before, 'all off leaves the document untouched')
    # no selection: plain text
    pg.evaluate("savedRange=null; setSug('A new sentence continues the paragraph here for the reader.')")
    ok(pg.evaluate("document.querySelectorAll('#aiOut button.trk').length") == 0 and pg.evaluate("window._trk") is None, 'Continue writing (no selection) stays plain')
    bad = [e for e in errs if e[0] == 'pageerror']
    ok(not bad, 'no page errors %s' % bad[:3])
    b.close()
sys.exit(1 if fails else 0)
