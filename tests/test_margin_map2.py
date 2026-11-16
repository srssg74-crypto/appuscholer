"""Margin map, part 2: Methods and Results move sets with their code checks, and the margin map for a paper on
the reading shelf (section text cut from the pages, notes kept per paper, no jump into the editor)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

DOC = ('<h2>Method</h2><p>A cross-sectional design suited the question. We sampled 120 nursing students by convenience.</p>'
       '<p>Anxiety was measured with the GAD-7. Students filled the forms in class.</p>'
       '<h2>Results</h2><p>Table 1 shows the sample. Anxiety was linked with poor sleep. This suggests hostels matter.</p>'
       '<p>Anxiety and sleep were correlated, r = .32, p &lt; .001.</p>')
RES = {"runs":[{"from":1,"to":1,"move":"R1","label":"Points to the sample table","quote":"Table 1 shows the sample"},
               {"from":2,"to":2,"move":"R2","label":"Says anxiety links to sleep, no figures","quote":"Anxiety was linked with poor sleep"},
               {"from":3,"to":3,"move":"R3","label":"Reads meaning into hostels","quote":"This suggests hostels matter"},
               {"from":4,"to":4,"move":"R2","label":"Gives the correlation","quote":"Anxiety and sleep were correlated"}]}
METH = {"runs":[{"from":1,"to":1,"move":"M1","label":"Justifies a cross-sectional design","quote":"A cross-sectional design suited"},
                {"from":2,"to":2,"move":"M2","label":"Convenience sample of 120 students","quote":"We sampled 120 nursing students"},
                {"from":3,"to":3,"move":"M3","label":"Names the GAD-7","quote":"Anxiety was measured with the GAD-7"},
                {"from":4,"to":4,"move":"M4","label":"Forms filled in class","quote":"Students filled the forms in class"}]}

with sync_playwright() as p:
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 1280, 'height': 900})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    pg.evaluate("h=>setEditorHTML(h)", DOC); pg.wait_for_timeout(300)
    ok(pg.evaluate("[mmGuess('Method'),mmGuess('3. Results'),mmGuess('Materials and methods'),mmGuess('Results and Discussion')]") == ['meth','res','meth','disc'], 'section names recognised')
    pg.evaluate("r=>{window.__p='';window.callAI=async(p)=>{window.__p=p;return JSON.stringify(r)}}", RES)
    pg.evaluate("mmOpen()"); pg.wait_for_timeout(200)
    ok(pg.input_value('#mmKind') == 'res', 'Results picked first and recognised')
    pg.click('#mmRunBtn'); pg.wait_for_timeout(400)
    ok('Yang and Allison (2003), results moves' in pg.evaluate("window.__p"), 'results move set in the prompt')
    t = pg.inner_text('#mmOut')
    ok('One part reports results without any number' in t, 'a results part with no number is flagged')
    ok('comments on the results' in t and 'check your target journal' in t, 'comments in Results are noted')
    ok('Not found in this section' not in t, 'R2 present, nothing required missing')
    pg.evaluate("document.getElementById('mmDlg').close()")
    pg.evaluate("r=>{window.callAI=async()=>JSON.stringify(r)}", METH)
    pg.evaluate("mmOpen()"); pg.select_option('#mmSec', '0'); pg.evaluate("mmSecChange()")
    ok(pg.input_value('#mmKind') == 'meth', 'Methods recognised')
    pg.click('#mmRunBtn'); pg.wait_for_timeout(400)
    t = pg.inner_text('#mmOut')
    ok('M5 Data analysis' in t and 'M6 Credibility' in t, 'missing analysis and credibility parts are listed: %s' % t[:300])
    pg.evaluate("document.getElementById('mmDlg').close()")

    # reading shelf paper
    pg.evaluate("""async()=>{const pages=['Title of paper\\nIntroduction\\nStress is common. It harms sleep. We ask why.\\nMethods\\nWe sampled 80 adults. We used the PSQI.',
        'Discussion\\nSleep and stress were linked. This matches Lee (2019). Our sample was small. Clinics could screen. Future work should follow people longer.\\nReferences\\nLee 2019.'];
      const p={id:'shMM',title:'A test paper',pages:pages,sections:[{kind:'introduction',title:'Introduction',page:1,subs:[]},{kind:'methods',title:'Methods',page:1,subs:[]},{kind:'discussion',title:'Discussion',page:2,subs:[]},{kind:'references',title:'References',page:2,subs:[]}]};
      await shPut(p);SH.cur=p}""")
    txt = pg.evaluate("shSectionText(SH.cur,2)")
    ok(txt.startswith('Sleep and stress were linked') and 'References' not in txt and 'Lee 2019.' not in txt, 'discussion text cut from the pages: %r' % txt[:80])
    ok(pg.evaluate("shSectionText(SH.cur,1)") == 'We sampled 80 adults. We used the PSQI.', 'methods text cut on the same page')
    html = pg.evaluate("shSectionsHTML(SH.cur)")
    ok(html.count('shMarginMap(') == 3, 'margin map button on introduction, methods and discussion only')
    DISC = {"runs":[{"from":1,"to":1,"move":"D2","label":"States stress and sleep go together","quote":"Sleep and stress were linked"},
                    {"from":3,"to":3,"move":"D6","label":"Admits the small sample","quote":"Our sample was small"}]}
    pg.evaluate("r=>{window.callAI=async()=>JSON.stringify(r)}", DISC)
    pg.evaluate("shMarginMap(2)"); pg.wait_for_timeout(200)
    ok(pg.input_value('#mmKind') == 'disc' and 'Discussion: Discussion' in pg.inner_text('#mmSec'), 'shelf section opens as a discussion')
    pg.click('#mmRunBtn'); pg.wait_for_timeout(400)
    t = pg.inner_text('#mmOut')
    ok('States stress and sleep go together' in t and 'show in document' not in t, 'paper notes shown without editor links')
    ok(pg.evaluate("!!LS.get(pkey('appu_mm_paper_shMM_2'))") or pg.evaluate("Object.keys(localStorage).some(k=>k.indexOf('appu_mm_paper_shMM_')>=0)"), 'kept per paper')
    pg.evaluate("document.getElementById('mmDlg').close()")
    pg.evaluate("mmOpen()"); pg.wait_for_timeout(200)
    ok(pg.evaluate("window._mmPaper") is None and 'Results' in pg.inner_text('#mmSec'), 'opening from the Words panel goes back to the document')
    bad = [e for e in errs if e[0] == 'pageerror']
    ok(not bad, 'no page errors %s' % bad[:3])
    b.close()
sys.exit(1 if fails else 0)
