"""Margin map: sections and sentences from the document, AI notes checked by code (move in set, quote in the
first sentence, no overlap), missing moves worked out by code, page view, jump to text, saved page."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

DOC = ('<h1>Exam anxiety and sleep</h1><h2>Introduction</h2><p>Exam anxiety is common in Indian colleges. It harms sleep.</p>'
       '<h2>Discussion</h2>'
       '<p>Exam anxiety predicted poorer sleep in first-year nursing students. This link was stronger in hostel residents.</p>'
       '<p>Our result agrees with Kumar et al. (2019), who found the same pattern in Delhi. It differs from a Kerala study, e.g. in effect size.</p>'
       '<p>One reason may be noise and shared rooms in hostels. The sample came from one college only.</p>'
       '<p>Colleges could screen students for anxiety before exams. Future studies should follow students over a full year.</p>')
AI = {"runs": [
  {"from":1,"to":2,"move":"RES","label":"States anxiety predicts poor sleep, worse in hostels","quote":"Exam anxiety predicted poorer sleep"},
  {"from":3,"to":4,"move":"COMP","label":"Sets the result beside Delhi and Kerala studies","quote":"Our result agrees with Kumar et al. (2019)"},
  {"from":4,"to":4,"move":"EXPL","label":"overlapping","quote":"It differs from a Kerala study"},
  {"from":5,"to":5,"move":"EXPL","label":"Offers hostel noise as a reason","quote":"One reason may be noise"},
  {"from":6,"to":6,"move":"LIM","label":"Admits a single-college sample","quote":"The sample came from three colleges"},
  {"from":7,"to":7,"move":"X9","label":"bad move","quote":"Colleges could screen students"},
  {"from":8,"to":8,"move":"REC","label":"Asks for a year-long follow-up","quote":"Future studies should follow students"}]}

with sync_playwright() as p:
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 1280, 'height': 900})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    pg.evaluate("h=>setEditorHTML(h)", DOC); pg.wait_for_timeout(300)
    before = pg.evaluate("editor.innerHTML")
    secs = pg.evaluate("mmSections().map(s=>[s.title,s.sents.length,s.sents.map(x=>x.p)])")
    ok([x[0] for x in secs] == ['Introduction', 'Discussion'] and secs[1][1] == 8, 'sections and sentences found: %s' % secs)
    ok(secs[1][2] == [2,2,3,3,4,4,5,5], 'paragraph numbers kept per sentence')
    ok(pg.evaluate("mmSplit('As Kumar et al. found, e.g. in Delhi. Next one.').length") == 2, 'et al. and e.g. do not split a sentence')
    pg.evaluate("a=>{window.__p='';window.callAI=async(p)=>{window.__p=p;return JSON.stringify(a)}}", AI)
    pg.evaluate("mmOpen()"); pg.wait_for_timeout(200)
    ok(pg.input_value('#mmSec') == '1' and pg.input_value('#mmKind') == 'disc', 'Discussion picked and recognised as a discussion')
    pg.click('#mmRunBtn'); pg.wait_for_timeout(500)
    pr = pg.evaluate("window.__p")
    ok('Moreno and Swales (2018)' in pr and '[8] Future studies' in pr and '¶ [3]' in pr, 'prompt carries the move set, numbered sentences and paragraph marks')
    v = pg.evaluate("JSON.parse(LS.get(mmKey(1)))")
    ok([r['move'] for r in v['runs']] == ['RES', 'COMP', 'EXPL', 'REC'], 'four notes pass: %s' % [r['move'] for r in v['runs']])
    why = sorted(r['why'] for r in v['rejected'])
    ok(why == ['move', 'overlap', 'quote'], 'bad quote, unknown move and overlap are set aside: %s' % why)
    ok(v['missing'] == ['LIM', 'EV'], 'missing moves come from code, including the limitation the AI claimed with a false quote: %s' % v['missing'])
    t = pg.inner_text('#mmOut')
    ok('Not found in this section' in t and 'Limitations of this study' in t and 'Sets the result beside Delhi and Kerala studies' in t, 'page shows notes and missing parts')
    ok(pg.evaluate("document.querySelectorAll('#mmOut .mm-note').length") == 4, 'four margin notes drawn')
    ok(pg.evaluate("editor.innerHTML") == before, 'document is not changed')
    # learning mode
    pg.click('#mmQuizBtn'); pg.wait_for_timeout(100)
    ok(pg.evaluate("document.querySelectorAll('#mmOut select.mm-q').length") == 4 and 'States anxiety predicts' not in pg.inner_text('#mmOut'), 'test mode hides the notes and asks')
    pg.select_option('#mmQ1', 'RES'); pg.wait_for_timeout(100)
    pg.select_option('#mmQ3', 'EXPL'); pg.wait_for_timeout(100)
    tq = pg.inner_text('#mmOut')
    ok('Answered 2 of 4, 1 right.' in tq and 'You chose: Explains results or their effects' in tq and 'Sets the result beside Delhi' in tq, 'answers marked right and wrong, note revealed after answering')
    pg.click('#mmQuizBtn'); pg.wait_for_timeout(100)
    ok(pg.evaluate("document.querySelectorAll('#mmOut .mm-q').length") == 0, 'back to all notes')
    pg.evaluate("mmGo(5)"); pg.wait_for_timeout(200)
    ok(pg.evaluate("String(getSelection())").startswith('One reason may be noise'), 'show in document selects the sentence')
    pg.evaluate("mmOpen()"); pg.wait_for_timeout(200)
    ok(pg.evaluate("document.querySelectorAll('#mmOut .mm-note').length") == 4, 'saved map shows again when reopened')
    with pg.expect_download() as dl:
        pg.evaluate("mmSaveHtml()")
    html = open(dl.value.path(), encoding='utf-8').read()
    ok('<!doctype html>' in html and 'Asks for a year-long follow-up' in html and 'show in document' not in html, 'saved page has the notes and no app links')
    # text changed: the old map is not shown
    pg.evaluate("document.getElementById('mmDlg').close()")
    pg.evaluate("editor.querySelectorAll('p')[4].textContent+=' A new sentence was added here.'")
    pg.evaluate("mmOpen()"); pg.wait_for_timeout(200)
    ok(pg.evaluate("document.querySelectorAll('#mmOut .mm-note').length") == 0, 'a changed section does not show a stale map')
    pg.evaluate("window.callAI=async()=>'no json here'"); pg.click('#mmRunBtn'); pg.wait_for_timeout(300)
    ok('did not answer in the expected form' in pg.inner_text('#mmOut'), 'non-JSON answer reported')
    bad = [e for e in errs if e[0] == 'pageerror']
    ok(not bad, 'no page errors %s' % bad[:3])
    b.close()
sys.exit(1 if fails else 0)
