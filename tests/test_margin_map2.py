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
       '<h2>Results</h2><p>Table 1 shows the sample. Anxiety was linked with poor sleep. This proves hostels cause poor sleep.</p>'
       '<p>Anxiety and sleep were correlated, r = .32, p &lt; .001.</p>')
RES = {"runs":[{"from":1,"to":1,"move":"R3","label":"Points to the sample table","quote":"Table 1 shows the sample"},
               {"from":2,"to":2,"move":"R4","label":"Says anxiety links to sleep, no figures","quote":"Anxiety was linked with poor sleep"},
               {"from":3,"to":3,"move":"R7","label":"Reads meaning into hostels","quote":"This proves hostels cause poor sleep"},
               {"from":4,"to":4,"move":"R4","label":"Gives the correlation","quote":"Anxiety and sleep were correlated"}]}
METH = {"runs":[{"from":1,"to":1,"move":"C1.3","label":"Justifies a cross-sectional design","quote":"A cross-sectional design suited"},
                {"from":2,"to":2,"move":"C2.1","label":"Convenience sample of 120 students","quote":"We sampled 120 nursing students"},
                {"from":3,"to":3,"move":"C2.4","label":"Names the GAD-7","quote":"Anxiety was measured with the GAD-7"},
                {"from":4,"to":4,"move":"C2.3","label":"Forms filled in class","quote":"Students filled the forms in class"}]}

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
    ok('Seven parts of a Results section' in pg.evaluate("window.__p"), 'results move set in the prompt')
    t = pg.inner_text('#mmOut')
    ok('One part reports results without any number' in t, 'a results part with no number is flagged')
    ok('comments on the results' in t and 'check your target journal' in t, 'comments in Results are noted')
    ok('Strong cause words' in t, 'causal wording in the meaning part is flagged')
    ok('Not found in this section' not in t, 'R4 present, nothing required missing')
    pg.evaluate("document.getElementById('mmDlg').close()")
    pg.evaluate("r=>{window.callAI=async()=>JSON.stringify(r)}", METH)
    pg.evaluate("mmOpen()"); pg.select_option('#mmSec', '0'); pg.evaluate("mmSecChange()")
    ok(pg.input_value('#mmKind') == 'meth', 'Methods recognised')
    pg.click('#mmRunBtn'); pg.wait_for_timeout(400)
    t = pg.inner_text('#mmOut')
    ok('C3.2 Describes the data analysis (experts: present in 96%)' in t and 'C1.1 Refers to previous works (experts: present in 100%)' in t and 'C1.4' not in t.split('Not found')[1].split('If this')[0], 'missing DRaC steps listed with expert shares, optional steps not demanded')
    ok('Move 2, describing the study · C2.4 · Describes the tools' in t, 'note names the move and step')
    pg.click('#mmQuizBtn'); pg.wait_for_timeout(100)
    ok(pg.evaluate("document.querySelectorAll('#mmOut select.mm-q optgroup').length") >= 3, 'test-myself options grouped by move')
    pg.click('#mmQuizBtn')
    # introduction groups
    INTRO = {"runs":[{"from":1,"to":1,"move":"I1A","label":"Says exam anxiety is common","quote":"Exam anxiety is common"}]}
    v = pg.evaluate("r=>mmValidate(r,{title:'Introduction',sents:[{p:1,t:'Exam anxiety is common in colleges.'},{p:1,t:'It harms sleep.'},{p:1,t:'We ask why.'}]},'intro')", INTRO)
    ok(v['missing'] == ['T2', 'T3'], 'introduction needs one step from each CARS move: %s' % v['missing'])
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
    DISC = {"runs":[{"from":1,"to":1,"move":"RES","label":"States stress and sleep go together","quote":"Sleep and stress were linked"},
                    {"from":3,"to":3,"move":"LIM","label":"Admits the small sample","quote":"Our sample was small"}]}
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
    LIT = {"runs":[{"from":1,"to":2,"move":"L1","label":"Summarises Delhi and Kerala studies","quote":"Kumar (2019) found anxiety"}]}
    v = pg.evaluate("r=>mmValidate(r,{title:'Review of literature',sents:[{p:1,t:'Kumar (2019) found anxiety in Delhi students.'},{p:1,t:'Rao (2020) found the same in Kerala.'},{p:1,t:'Both used the GAD-7.'}]},'lit')", LIT)
    ok(pg.evaluate("mmGuess('Chapter 2: Review of Literature')") == 'lit' and v['missing'] == ['K2'], 'literature review recognised; summary-only review lacks a stance: %s' % v['missing'])
    MED = {"runs":[{"from":1,"to":1,"move":"B1","label":"Anxiety predicts poor sleep","quote":"Anxiety predicted poor sleep"},{"from":2,"to":2,"move":"B3","label":"Unlike Delhi study","quote":"Unlike a Delhi study"},{"from":3,"to":3,"move":"B2","label":"Small single-college sample","quote":"Our sample was small"}]}
    v = pg.evaluate("r=>mmValidate(r,{title:'Discussion',sents:[{p:1,t:'Anxiety predicted poor sleep in students.'},{p:1,t:'Unlike a Delhi study, the link was strong.'},{p:1,t:'Our sample was small and from one college.'}]},'discmed')", MED)
    ok(v['back'] == 1 and v['missing'] == ['B4', 'B5'], 'medical order: out-of-order part and missing parts found: %s %s' % (v['back'], v['missing']))
    D2 = {"runs":[{"from":1,"to":1,"move":"RES","label":"Main result","quote":"This is the first study to show"},{"from":2,"to":2,"move":"LIM","label":"Small sample","quote":"Our sample was small and may carry selection bias"}]}
    v = pg.evaluate("r=>mmValidate(r,{title:'Discussion',sents:[{p:1,t:'This is the first study to show the link in India.'},{p:1,t:'Our sample was small and may carry selection bias.'}]},'disc')", D2)
    ok(v['first'] == [1] and v['lim3'] == ['confound'], 'first-claim found; limitations missing confounding (small sample counts as chance): %s %s' % (v['first'], v['lim3']))
    bad = [e for e in errs if e[0] == 'pageerror']
    ok(not bad, 'no page errors %s' % bad[:3])
    b.close()
sys.exit(1 if fails else 0)
