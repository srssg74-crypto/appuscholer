"""Does my study hold together? Code checks on the AI's findings: quote must be in the document, line from code,
severity rules, all ten checks, set-aside list, no change to the document."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright

fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

filler = ' '.join(['Students in Jaipur colleges report stress before examinations and this affects sleep.'] * 30)
DOC = ('<h1>Exam anxiety and sleep</h1><p>Introduction. ' + filler + '</p>'
       '<p>Few Indian studies have measured sleep quality alongside exam anxiety in nursing students.</p>'
       '<p>Research question: does exam anxiety predict poor sleep quality in first-year nursing students?</p>'
       '<p>Method. A cross-sectional survey of 120 students used the GAD-7 and the PSQI.</p>'
       '<p>Results. Anxiety and sleep quality were correlated, r = .32, p &lt; .001.</p>'
       '<p>Conclusion. Exam anxiety causes poor sleep, so colleges must start sleep programmes.</p>')
AI = {"design": "quantitative survey",
 "chain": [{"step":"problem","line":2,"quote":"Students in Jaipur colleges report stress before examinations","status":"clear","note":"Stated."},
           {"step":"gap","line":3,"quote":"Few Indian studies have measured sleep quality","status":"clear","note":"Stated."},
           {"step":"question","line":4,"quote":"does exam anxiety predict poor sleep quality","status":"clear","note":"Clear."},
           {"step":"method","line":5,"quote":"A cross-sectional survey of 120 students","status":"weak","note":"No sampling method."},
           {"step":"results","line":6,"quote":"r = .32","status":"clear","note":""},
           {"step":"conclusion","line":7,"quote":"Exam anxiety causes poor sleep","status":"weak","note":"Causal claim."}],
 "checks": [{"id":"RC%02d" % i,"status":"not_found","basis":"ok"} for i in range(1,11) if i not in (5,8,9)]
          + [{"id":"RC08","status":"found","basis":"causal claim"},{"id":"RC05","status":"found","basis":"design"}],
 "findings": [
   {"id":"F01","check":"RC08","lens":"evidence","type":"unsupported_inference","title":"Causal conclusion from a correlation","severity":"critical","status":"confirmed","confidence":"high",
    "line":99,"quote":"Exam anxiety causes poor sleep, so colleges must start sleep programmes","problem":"A cross-sectional correlation cannot show cause.","impact":"Main conclusion overreaches.","recommendation":"Say the two are associated."},
   {"id":"F02","check":"RC05","lens":"method","type":"misalignment","title":"Predict needs more than a correlation","severity":"major","status":"potential","confidence":"medium",
    "line":4,"quote":"does exam anxiety predict poor sleep quality","problem":"x","impact":"y","recommendation":"z"},
   {"id":"F03","check":"RC09","lens":"consistency","type":"scope_drift","title":"Made-up quote","severity":"critical","status":"likely","confidence":"high",
    "line":3,"quote":"the sample was 200 students","problem":"x","impact":"y","recommendation":"z"},
   {"id":"F04","check":"RC09","lens":"consistency","type":"scope_drift","title":"Ellipsis","severity":"minor","status":"likely","confidence":"low",
    "line":3,"quote":"Few Indian studies ... nursing students","problem":"x","impact":"y","recommendation":"z"}]}

with sync_playwright() as p:
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 1280, 'height': 900})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    pg.evaluate("h=>setEditorHTML(h)", DOC); pg.wait_for_timeout(300)
    before = pg.evaluate("editor.innerHTML")
    pg.evaluate("a=>{window.__prompt='';window.callAI=async(p)=>{window.__prompt=p;return '```json\\n'+JSON.stringify(a)+'\\n```'}}", AI)
    pg.evaluate("cohOpen()"); pg.wait_for_timeout(200)
    ok(pg.is_visible('#cohDlg'), 'window opens')
    pg.select_option('#cohDesign', 'quantitative survey or correlational')
    pg.click('#cohRunBtn'); pg.wait_for_timeout(600)
    v = pg.evaluate("JSON.parse(LS.get(cohKey()))")
    pr = pg.evaluate("window.__prompt")
    ok('[1] Exam anxiety and sleep' in pr and 'RC10' in pr and 'quantitative survey' in pr and 'EXACTLY' in pr, 'prompt numbers lines, names ten checks, design and the exact-quote rule')
    ids = [f['id'] for f in v['ok']]
    ok(ids == ['F01', 'F02'], 'two findings pass the quote check: %s' % ids)
    rj = {f['id']: f['why'] for f in v['rejected']}
    ok(rj == {'F03': 'notfound', 'F04': 'ellipsis'}, 'made-up and ellipsis quotes are set aside: %s' % rj)
    f1 = v['ok'][0]; f2 = v['ok'][1]
    lines = pg.evaluate("cohLines(editor.innerText)")
    ok(lines[f1['line']-1].startswith('Conclusion'), 'line number comes from the document, not the AI (%s)' % f1['line'])
    ok(f1['severity'] == 'critical', 'confirmed and high stays critical')
    ok(f2['severity'] == 'moderate' and f2['rule'] == 'potential_cap', 'possible finding is lowered from major')
    ck = {c['id']: c['status'] for c in v['checks']}
    ok(len(ck) == 10 and ck['RC08'] == 'found' and ck['RC09'] == 'missing' and ck['RC05'] == 'found', 'ten checks present, missing one marked: %s' % ck)
    t = pg.inner_text('#cohOut')
    ok('Causal conclusion from a correlation' in t and 'Set aside: 2 findings' in t and 'Lowered to moderate' in t, 'screen shows findings, set-aside list and rule notes')
    ok('Problem' in t and 'Conclusion' in t and 'Ten checks' in t, 'screen shows the chain and the checks')
    ok(pg.evaluate("editor.innerHTML") == before, 'document is not changed')
    # jump to the quoted line
    pg.evaluate("cohGo(%d)" % f1['line']); pg.wait_for_timeout(200)
    sel = pg.evaluate("String(getSelection())")
    ok(sel.startswith('Exam anxiety causes poor sleep'), 'line link selects the quoted words: %r' % sel[:40])
    # reopen shows last result; save report
    pg.evaluate("cohOpen()"); pg.wait_for_timeout(200)
    ok('Last check' in pg.inner_text('#cohOut'), 'last result is shown when reopened')
    with pg.expect_download() as dl:
        pg.evaluate("cohSaveMd()")
    md = open(dl.value.path(), encoding='utf-8').read()
    ok('### F01 (critical' in md and 'Set aside' in md and 'MIT licence' in md, 'report saves with findings, set-aside list and credit')
    # garbled AI answer
    pg.evaluate("window.callAI=async()=>'Sorry, I cannot.'")
    pg.click('#cohRunBtn'); pg.wait_for_timeout(300)
    ok('did not answer in the expected form' in pg.inner_text('#cohOut'), 'non-JSON answer is reported, not shown as a result')
    pg.evaluate("document.getElementById('cohDlg').close()")
    # too short
    pg.evaluate("setEditorHTML('<p>Only a few words here.</p>')")
    pg.evaluate("cohOpen()"); pg.click('#cohRunBtn'); pg.wait_for_timeout(200)
    ok('too short to check' in pg.inner_text('#cohOut'), 'short document is refused without an AI call')
    bad = [e for e in errs if e[0] == 'pageerror']
    ok(not bad, 'no page errors %s' % bad[:3])
    b.close()
sys.exit(1 if fails else 0)
