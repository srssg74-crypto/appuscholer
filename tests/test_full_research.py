"""Full research run-through as a student would do it, mostly through the visible controls.
Prints PASS/FAIL for hard checks and OBS lines for friction a student would meet."""
import sys, os, json, random, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page
from playwright.sync_api import sync_playwright
import tempfile
OUT = tempfile.mkdtemp() + '/'
fails = []; obs = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m, flush=True)
    if not c: fails.append(m)
def OBS(m):
    print('OBS  ' + m, flush=True); obs.append(m)

def make_data(path):
    random.seed(7)
    hdr='participant_id,age,gender,course,Residence,Sleep_hours_on_a_usual_n,GAD7_01,GAD7_02,GAD7_03,GAD7_04,GAD7_05,GAD7_06,GAD7_07'
    rows=[]
    for i in range(1,143):
        res=random.choice([1,1,2,2,2])
        sleep=round(min(10,max(3.5,random.gauss(6.6 if res==2 else 6.0,1.1)))*2)/2
        lat=-0.55*(sleep-6.3)+(0.45 if res==1 else 0)+random.gauss(0,0.8)
        items=[max(0,min(3,int(round(1.1+lat*0.6+random.gauss(0,0.6))))) for _ in range(7)]
        rows.append([f'P{i:03d}',str(random.choice([17,18,18,18,19,19,20])),str(random.choice([1,2,2,1,4])),random.choice(['BA I','BSc I','BCom I']),str(res),str(sleep)]+[str(x) for x in items])
    rows[10][7]='';rows[22][9]='';rows[40][5]='65';rows[55][1]='';rows.append(list(rows[30]));rows[80][6:13]=['']*7
    open(path,'w').write(hdr+'\n'+'\n'.join(','.join(r) for r in rows)+'\n')

with sync_playwright() as p:
    make_data(OUT + 'data.csv')
    errors = []
    b, pg = new_page(p, errors)
    J = lambda js: pg.evaluate(js)
    def fill(sel, val):
        loc = pg.locator(sel).first
        loc.fill(val); loc.dispatch_event('change'); loc.dispatch_event('blur')
    def step(st, i):
        J("try{document.getElementById('subDlg').close()}catch(e){}")
        J("subOpen('%s','%s')" % (st, i)); pg.wait_for_timeout(150)
    def state(i): return J("subState('%s').s" % i)
    def needed():
        return J("(()=>{const m=document.getElementById('subMain').innerText;const i=m.indexOf('Still needed');return i<0?'':m.slice(i,i+300)})()")
    def logfill(kind, row, d):
        for k, v in d.items():
            loc = pg.locator('#subMain [onchange^="logCell(\'%s\',%d,\'%s\'"]' % (kind, row, k))
            if loc.count() == 0:
                print('  no cell', kind, row, k); continue
            el = loc.first
            if el.evaluate("e=>e.tagName") == 'SELECT':
                opts = el.evaluate("e=>[...e.options].map(o=>o.value+'|'+o.text)")
                m = [o.split('|')[0] for o in opts if v.lower() in o.lower()]
                el.select_option(m[0] if m else opts[-1].split('|')[0])
            else:
                el.fill(v)
            el.dispatch_event('change')
    def shot(n): pg.screenshot(path=OUT + n + '.png')

    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    # ---------- profile and project, the way a new student starts ----------
    J("LS.set('appu_me',JSON.stringify({name:'Asha Verma',pos:'M.A. Psychology, final year',role:'student',course:'pg'}))")
    J("apHomeShow()"); pg.wait_for_timeout(200)
    J("openNewProjectDirect()"); pg.wait_for_timeout(200)
    fill('#sapName', 'Sleep and exam anxiety')
    J("saveAsProject()"); pg.wait_for_timeout(300)
    J("try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    ok(J("!!getActiveProject()"), 'project created from Home')
    # ---------- A ----------
    J("showTool('idea')")
    fill('#ideaTopic', 'Do sleep hours relate to exam anxiety among first-year undergraduate students in Jaipur colleges, and do hostel students differ from day scholars?')
    fill('#ideaResources', 'Two colleges agreed; about 150 first-year students reachable in class; Google Forms or the app form; supervisor available weekly.')
    fill('#ideaTimeframe', 'Five months, by March')
    step('idea', 'A1')
    J("(()=>{const A={p:{who:'first-year nursing students',what:'exam anxiety',where:'two colleges in Pune'},alt1:'phone use and sleep',alt2:'loneliness in hostels',why:'I can reach these students through my supervisor, and the scale is free.'};a1Set('who',A.p.who);a1Set('what',A.p.what);a1Set('where',A.p.where);lsSet('A1','alt1',A.alt1);lsSet('A1','alt2',A.alt2);lsSet('A1','why',A.why)})()")
    step('idea', 'A1'); ok(state('A1') == 'dn' or 'Still needed' not in needed(), 'A1 complete after topic and alternatives: ' + needed()[:120])
    step('idea', 'A2')
    ta = J("[...document.querySelectorAll('#subMain textarea')].map(t=>(t.getAttribute('onchange')||t.getAttribute('oninput')||'').slice(0,40))")
    print('A2 textareas', ta)
    fill('#subMain textarea >> nth=0', 'Exam anxiety is common among Indian undergraduates and is linked with poorer marks and sleep problems (Sharma, 2021; Kumar & Singh, 2019). First-year students face new hostels, new teaching styles and semester exams at once. Studies on sleep and anxiety come mostly from medical students in large cities (Gupta et al., 2020). Little is known about general undergraduates in Rajasthan colleges, and whether living in a hostel changes the picture.')
    step('idea', 'A2'); print('A2 after:', state('A2'), needed()[:200])
    step('idea', 'A3')
    fill("#subMain textarea[onchange*=\"'aim'\"],#subMain textarea[oninput*=\"'aim'\"]", 'To examine how sleep hours relate to exam anxiety among first-year students, and whether hostel students differ from day scholars.')
    fill("#subMain textarea[onchange*=\"'q'\"],#subMain textarea[oninput*=\"'q'\"]", 'Is shorter sleep associated with higher exam anxiety, and do hostel students report more exam anxiety than day scholars?')
    step('idea', 'A3'); print('A3 after:', state('A3'), needed()[:250])
    # A4: rate every item Fine, decide Go
    step('idea', 'A4')
    n = J("document.querySelectorAll('#subMain input[type=radio]').length")
    for k in range(0, n, 3):
        pg.locator('#subMain input[type=radio]').nth(k).check()
    pg.wait_for_timeout(100)
    print('A4 ta', J("[...document.querySelectorAll('#subMain textarea,#subMain select')].map(t=>t.tagName+':'+(t.getAttribute('onchange')||t.getAttribute('oninput')||'').slice(0,50))"))
    J("(()=>{const s=document.querySelector('#subMain select:not(#subSel)');if(s){s.value=s.options[1].value;s.dispatchEvent(new Event('change'))}})()")
    print('A4 ta2', J("[...document.querySelectorAll('#subMain textarea')].map(t=>(t.getAttribute('onchange')||t.getAttribute('oninput')||'').slice(0,50))"))
    fill("#subMain textarea[onchange*=\"'A4','why'\"],#subMain textarea[oninput*=\"'A4','why'\"]", 'Access is agreed by both principals, the scales are free, and the timeline fits one semester.')
    step('idea', 'A4'); print('A4 after:', state('A4'), needed()[:250])
    shot('a4')
    # ---------- C plan first (A3 needs hypotheses from the plan) ----------
    J("spOpen()"); pg.wait_for_timeout(300)
    sp = J("[...document.querySelectorAll('#spDlg input,#spDlg select,#spDlg textarea')].map(e=>e.tagName+'#'+e.id+'['+(e.placeholder||'').slice(0,30)+']').join(' ')")
    print('SPDLG', sp[:1500])
    shot('plan_empty')
    pg.select_option('#spType', 'survey')
    fill('#spPop', 'First-year BA, BSc and BCom students at two colleges in Jaipur')
    fill('#spSampling', 'Convenience sample of whole first-year sections in both colleges')
    rows = pg.locator('#spVars tbody tr')
    pg.locator('#spVars tbody tr >> nth=0 >> .spName').fill('Exam anxiety')
    pg.locator('#spVars tbody tr >> nth=0 >> .spRole').select_option('outcome')
    pg.locator('#spVars tbody tr >> nth=0 >> .spScale').select_option('GAD7')
    pg.locator('#spVars tbody tr >> nth=1 >> .spName').fill('Sleep hours on a usual night')
    pg.locator('#spVars tbody tr >> nth=1 >> .spRole').select_option('predictor')
    pg.locator('#spVars tbody tr >> nth=1 >> .spScale').select_option('own')
    J("spAddRow()")
    pg.locator('#spVars tbody tr >> nth=2 >> .spName').fill('Residence')
    pg.locator('#spVars tbody tr >> nth=2 >> .spRole').select_option('group')
    pg.locator('#spVars tbody tr >> nth=2 >> .spTypeV').select_option('category')
    pg.locator('#spVars tbody tr >> nth=2 >> .spLevels').fill('Hostel, Day scholar')
    fill('#spHyp', 'H1: Students who sleep fewer hours report higher exam anxiety.\nH2: Hostel students report higher exam anxiety than day scholars.')
    # sample size via the power calculator, from a published effect
    pg.locator('#spDlg button', has_text='Work it out').click(); pg.wait_for_timeout(300)
    ok(J("document.getElementById('powerDlg').open"), 'power calculator opens from the plan')
    J("document.getElementById('pwGuide').open=true")
    pg.locator('input[name=pwQ][value=corr]').check()
    fill('#pgR', '0.25'); pg.locator('#pwGuideBody button', has_text='Work it out').click()
    ok(J("document.getElementById('pwEffect').value") == '0.25', 'r from an earlier study goes into the calculator')
    pw_btns = J("[...document.querySelectorAll('#powerDlg button')].map(b=>b.innerText.trim()).filter(Boolean)")
    print('POWER buttons', pw_btns)
    J("(()=>{const d=document.getElementById('pwDrop');if(d){d.value='10'}})()")
    pg.locator('#powerDlg button', has_text=re.compile('^(Calculate|Work it out|Compute)')).last.click(); pg.wait_for_timeout(400)
    print('POWER out', J("(document.getElementById('pwOut')||{}).innerText||''")[:400])
    shot('power')
    if J("!!document.getElementById('pwEffSrc')"):
        fill('#pwEffSrc', 'r = .25 between sleep and anxiety in students, Gupta et al. (2020)')
        J("pwUse()"); pg.wait_for_timeout(200)
    else:
        OBS('power result has no "use in my plan" box')
    ok(J("!document.getElementById('powerDlg').open"), 'power dialog closes after Use in my plan')
    print('plan n now', J("document.getElementById('spN').value"))
    pg.locator('#spDlg button', has_text='Save').last.click(); pg.wait_for_timeout(300)
    ds = J("studyGet().design")
    ok(ds and ds.get('type') == 'survey' and len(ds.get('vars', [])) == 3, 'plan saved with 3 variables')
    ok(ssc := J("ssComplete(studyGet().design)"), 'C3 sample size has its basis')
    step('idea', 'A3'); print('A3 after plan:', state('A3'), needed()[:200])
    # ---------- B ----------
    step('lit', 'B1')
    J("(()=>{const r=document.querySelector('#subMain input[type=radio]');if(r){r.click()}})()")
    tas = J("[...document.querySelectorAll('#subMain textarea,#subMain select')].map(t=>t.tagName+':'+(t.getAttribute('onchange')||t.getAttribute('oninput')||'').slice(0,40))")
    print('B1 fields', tas)
    J("(()=>{const s=[...document.querySelectorAll('#subMain select')].find(x=>x.id!=='subSel');if(s){s.value=s.options[1].value;s.dispatchEvent(new Event('change'))}})()")
    fill('#subMain textarea >> nth=0', 'A narrative review fits a master\'s thesis: one student, five months, and the question needs background more than pooled numbers.')
    step('lit', 'B1'); print('B1', state('B1'), needed()[:150])
    step('lit', 'B2')
    pg.locator('#subMain button', has_text='Add a row').first.click(); pg.wait_for_timeout(150)
    print('B2 keys', J("[...document.querySelectorAll('#subMain [onchange^=\"logCell\"]')].map(e=>e.type+':'+e.getAttribute('onchange').slice(0,40))"))
    logfill('search', 0, {'date':'2026-11-02','db':'PubMed','q':'("sleep" OR "sleep duration") AND ("exam anxiety" OR "test anxiety") AND student*','lim':'2010-2026, English','hits':'214','kept':'23'})
    step('lit', 'B2'); print('B2', state('B2'), needed()[:150])
    step('lit', 'B6'); print('B6 view', J("document.getElementById('subMain').innerText")[:300].replace('\n', ' '))
    shot('b6')
    # ---------- references typed into the Citation Manager ----------
    J("try{document.getElementById('subDlg').close()}catch(e){}"); J("showTool('cite')")
    refs = [('Sharma, R.', '2021', 'Exam anxiety in Indian undergraduates', 'Indian Journal of Psychology', '58', '2', '101-112'),
            ('Kumar, A., & Singh, P.', '2019', 'Sleep, stress and marks in college students', 'Journal of Indian Academy of Applied Psychology', '45', '1', '33-41'),
            ('Gupta, S., Rao, M., & Jain, K.', '2020', 'Sleep duration and anxiety among medical students in Delhi', 'Indian Journal of Psychiatry', '62', '4', '410-417'),
            ('Spitzer, R. L., Kroenke, K., Williams, J. B. W., & Lowe, B.', '2006', 'A brief measure for assessing generalized anxiety disorder: The GAD-7', 'Archives of Internal Medicine', '166', '10', '1092-1097')]
    for a, y, t, src, v, iss, pp in refs:
        J("citClearForm()")
        fill('#citAuthor', a); fill('#citYear', y); fill('#citTitle', t); fill('#citSource', src); fill('#citVol', v); fill('#citIssue', iss); fill('#citPages', pp)
        J("citAdd()"); pg.wait_for_timeout(120)
    nlib = J("citGetLib().length")
    ok(nlib == 4, 'four references in the library (%s)' % nlib)
    step('lit', 'B3')
    pg.locator('#subMain button', has_text='Bring papers from the library').first.click(); pg.wait_for_timeout(300)
    nrows = J("logRows(studyGet(),'matrix').length")
    ok(nrows == 4, 'source matrix filled from the library (%s rows)' % nrows)
    print('B3 keys', J("[...new Set([...document.querySelectorAll('#subMain [onchange^=\"logCell(\\'matrix\\',0\"]')].map(e=>e.getAttribute('onchange').split(',')[2]))]"))
    themes = ['Prevalence of exam anxiety', 'Sleep and anxiety', 'Sleep and anxiety', 'Measurement']
    for r in range(4):
        logfill('matrix', r, {'design': 'Cross-sectional', 'sample': 'Students', 'measure': 'Self-report', 'finding': 'Shorter sleep went with more anxiety', 'limit': 'Single city', 'stance': 'Supports', 'quote': 'p. 104', 'theme': themes[r]})
    step('lit', 'B3'); print('B3', state('B3'), needed()[:150])
    step('lit', 'B4')
    pg.locator('#subMain button', has_text='Bring papers from the library').first.click(); pg.wait_for_timeout(300)
    print('B4 keys', J("[...new Set([...document.querySelectorAll('#subMain [onchange^=\"logCell(\\'quality\\',0\"]')].map(e=>e.getAttribute('onchange').split(',')[2]))]"))
    for r in range(4):
        logfill('quality', r, {'str': 'Large sample, validated scale', 'weak': 'Convenience sample', 'tool': 'AXIS', 'judge': 'Moderate', 'ret': 'not retracted'})
    step('lit', 'B4'); print('B4', state('B4'), needed()[:200])
    step('lit', 'B5'); print('B5', state('B5'), J("document.getElementById('subMain').innerText")[:400].replace('\n', ' | '))
    step('lit', 'B6')
    pg.locator('#subMain button', has_text=re.compile('Go to the tool')).first.click(); pg.wait_for_timeout(300)
    print('B6 tool visible:', J("(document.querySelector('.tool-panel.active')||{}).dataset.panel"))
    J("gapDlgOpen()"); pg.wait_for_timeout(200)
    print('B4 now', state('B4'))
    print('GAP fields', J("[...document.querySelectorAll('#gapDlg input,#gapDlg textarea,#gapDlg select')].map(e=>e.tagName+'#'+e.id).join(' ')"))
    shot('gap')
    fill('#gapText', 'Population gap: studies on sleep and exam anxiety in India come from medical students in large cities (Gupta et al., 2020). Our PubMed search (214 hits) found none on general first-year undergraduates in Rajasthan, or on hostel versus day scholars.')
    print('GAP buttons', J("[...document.querySelectorAll('#gapDlg button')].map(b=>b.innerText.trim())"))
    pg.locator('#gapDlg button', has_text=re.compile('Save')).last.click(); pg.wait_for_timeout(200)
    step('lit', 'B6'); print('B6', state('B6'), needed()[:150])
    step('lit', 'B5')
    tas = pg.locator('#subMain textarea[onchange^="wB5Note"]')
    for k in range(tas.count()):
        tas.nth(k).fill('Studies agree that shorter sleep goes with more anxiety; samples were medical students, so the size may differ in general colleges.'); tas.nth(k).dispatch_event('change')
        step('lit', 'B5'); tas = pg.locator('#subMain textarea[onchange^="wB5Note"]')
    cbs = pg.locator('#subMain input[type=checkbox][onchange^="wB5Note"]')
    for k in range(cbs.count()):
        cbs.nth(k).check(); step('lit', 'B5'); cbs = pg.locator('#subMain input[type=checkbox][onchange^="wB5Note"]')
    step('lit', 'B5'); print('B5', state('B5'), J("document.getElementById('subMain').innerText").count('papers)'))
    step('lit', 'B7')
    fill('#subMain input[onchange^="wPatch(\'B7\',\'theory\'"]', 'Attentional control theory')
    fill('#subMain input[onchange^="wPatch(\'B7\',\'cite\'"]', 'Eysenck et al., 2007')
    fill('#subMain input[onchange^="wB7Con(0,\'name\'"]', 'Anxiety')
    step('lit', 'B7')
    sel = pg.locator('#subMain select[onchange^="wB7Con(0,\'v\'"]'); print('B7 options', sel.evaluate("e=>[...e.options].map(o=>o.value)"))
    sel.select_option(index=1); sel.dispatch_event('change')
    step('lit', 'B7')
    fill('#subMain input[onchange^="wB7Con(1,\'name\'"]', 'Sleep loss')
    step('lit', 'B7'); sel = pg.locator('#subMain select[onchange^="wB7Con(1,\'v\'"]'); sel.select_option(index=2); sel.dispatch_event('change')
    step('lit', 'B7'); print('B7', state('B7'), needed()[:200])
    print('STAGE A/B', J("['A1','A2','A3','A4','B1','B2','B3','B4','B5','B6','B7'].map(i=>i+':'+subState(i).s).join(' ')"))
    # ---------- C ----------
    step('design', 'C1'); print('C1', state('C1'), needed()[:120])
    step('design', 'C2')
    fill('#subMain textarea[onchange^="lsSet(\'C2\',\'incl\'"],#subMain textarea[oninput^="lsSet(\'C2\',\'incl\'"]', 'First-year undergraduate students, 17 years or older, enrolled in the two colleges, who can read Hindi or English.')
    fill('#subMain textarea[onchange^="lsSet(\'C2\',\'excl\'"],#subMain textarea[oninput^="lsSet(\'C2\',\'excl\'"]', 'Students absent on the day of data collection or already in treatment for anxiety.')
    fill('#subMain textarea[onchange^="lsSet(\'C2\',\'rec\'"],#subMain textarea[oninput^="lsSet(\'C2\',\'rec\'"]', 'In class, through the head of department, two weeks before the semester exams.')
    step('design', 'C2'); print('C2', state('C2'), needed()[:200])
    step('design', 'C4'); print('C4', state('C4'), J("document.getElementById('subMain').innerText")[:200].replace('\n',' | '))
    step('design', 'C5'); print('C5 view', J("document.getElementById('subMain').innerText")[:300].replace('\n',' | '))
    pg.locator('#subMain input[type=radio][onchange*="\'pub\'"]').check(); pg.wait_for_timeout(150)
    print('C5 fields', J("[...document.querySelectorAll('#subMain input,#subMain textarea,#subMain select')].filter(e=>!/^sub/.test(e.id)).map(e=>e.type+':'+(e.getAttribute('onchange')||e.getAttribute('oninput')||'').slice(0,50))"))
    shot('c5')
    # C6 questionnaire
    step('design', 'C6')
    pg.locator('#subMain button', has_text=re.compile('Go to the tool')).first.click(); pg.wait_for_timeout(300)
    print('C6 tool opened dialog?', J("!!(document.getElementById('qnDlg')&&document.getElementById('qnDlg').open)"), 'panel', J("(document.querySelector('.tool-panel.active')||{}).dataset.panel"))
    J("qnOpen()"); pg.wait_for_timeout(300)
    shot('qn')
    print('QN text', J("document.getElementById('qnDlg').innerText")[:1500].replace('\n',' | '))
    fill('#qnIntro', 'This survey asks about your sleep and how you feel before exams. It takes about 8 minutes. Taking part is voluntary and your answers are anonymous.')
    with pg.expect_download() as dl:
        pg.locator('#qnDlg button', has_text='Data template').click()
    tpl = open(dl.value.path(), encoding='utf-8-sig').read()
    print('TEMPLATE header', tpl.split('\n')[0])
    open(OUT + 'template.csv', 'w').write(tpl)
    with pg.expect_download() as dl2:
        pg.locator('#qnDlg button', has_text='Codebook').click()
    print('CODEBOOK', open(dl2.value.path(), encoding='utf-8-sig').read()[:900])
    pg.locator('#qnDlg button', has_text='Save and close').click(); pg.wait_for_timeout(200)
    step('design', 'C6'); print('C6', state('C6'), needed()[:120])
    # C7 analysis plan
    step('design', 'C7')
    pg.locator('#subMain button', has_text='Make rows from my hypotheses').click(); pg.wait_for_timeout(200)
    step('design', 'C7'); print('C7', state('C7'), J("document.getElementById('subMain').innerText")[:900].replace('\n', ' | '))
    shot('c7')
    print('C7 prefilled', J("JSON.stringify(logRows(studyGet(),'aplan').map(r=>[r.dv,r.test,r.es,r.miss]))"))
    logfill('aplan', 0, {'dv': 'GAD-7 total', 'test': 'Pearson r', 'es': 'r', 'miss': 'Prorate'})
    step('design', 'C7')
    logfill('aplan', 1, {'dv': 'GAD-7 total', 'test': 'Welch t-test', 'es': 'Cohen', 'miss': 'Prorate'})
    step('design', 'C7'); print('C7', state('C7'), J("c7Issues(studyGet())"))
    # C8 synopsis
    step('design', 'C8')
    print('C8 front fields', J("[...document.querySelectorAll('#subMain input')].map(e=>(e.getAttribute('onchange')||e.getAttribute('oninput')||'').slice(0,40)+'='+e.value).join(' ; ')"))
    for k, v in [('student', 'Asha Verma'), ('sup', 'Dr. Meena Sharma, Professor'), ('dept', 'Department of Psychology'), ('univ', 'University of Rajasthan, Jaipur')]:
        loc = pg.locator('#subMain input[onchange*="c8Front(\'%s\'"],#subMain input[oninput*="c8Front(\'%s\'"]' % (k, k))
        if loc.count(): loc.first.fill(v); loc.first.dispatch_event('change'); loc.first.dispatch_event('input')
        else: print('  no C8 field', k)
    pg.locator('#subMain button', has_text='Make the synopsis').click(); pg.wait_for_timeout(600)
    g = J("synGaps(studyGet())"); print('synopsis gaps', g)
    print('GAP texts', J("[...editor.querySelectorAll('.draft-ph')].map(x=>x.textContent).join(' || ')")[:1500])
    shot('synopsis')
    # C9 ethics record
    step('design', 'C9')
    pg.locator('#subMain input[type=radio][onchange*="\'route\',\'app\'"]').check(); pg.wait_for_timeout(200)
    step('design', 'C9')
    print('C9 fields', J("[...document.querySelectorAll('#subMain input,#subMain textarea,#subMain select')].filter(e=>!/^sub/.test(e.id)).map(e=>e.type+':'+(e.getAttribute('onchange')||e.getAttribute('oninput')||'').slice(0,45)).join(' ; ')"))
    print('C9 text', J("document.getElementById('subMain').innerText")[:700].replace('\n',' | '))
    shot('c9')
    # C10 consent
    step('design', 'C10')
    pg.locator('#subMain button', has_text='consent').first.click(); pg.wait_for_timeout(300)
    print('C10 button opened ecDlg?', J("document.getElementById('ecDlg').open"))
    J("document.getElementById('ecDlg').showModal();ecRender()"); pg.wait_for_timeout(200)
    print('EC prefill', J("['ecTitle','ecPI','ecWhat','ecRisks2','ecBenefits','ecContact','ecStatus','ecCommittee','ecConsentMode','ecMinors'].map(i=>i+'='+(document.getElementById(i)||{}).value).join(' ; ')"))
    J("document.getElementById('ecDlg').close()")
    # finish C9 with the approval letter
    step('design', 'C9')
    for k, v in [('cm.name', 'Institutional Ethics Committee'), ('cm.inst', 'University of Rajasthan'), ('cm.addr', 'JLN Marg, Jaipur 302004'), ('cm.email', 'iec@uniraj.ac.in'), ('lt.no', 'IEC/PSY/2026/41'), ('lt.date', '2026-10-20')]:
        loc = pg.locator('#subMain input[onchange*="ethicsSet(\'%s\'"]' % k); loc.first.fill(v); loc.first.dispatch_event('change')
        step('design', 'C9')
    print('C9', state('C9'), J("ethicsState(studyGet())"))
    # C10 consent form in the EC dialog
    J("document.getElementById('ecDlg').showModal();ecRender()")
    for i, v in [('ecTitle', 'Sleep hours and exam anxiety in first-year students'), ('ecPI', 'Asha Verma, Department of Psychology, University of Rajasthan'), ('ecWhat', 'One questionnaire of about 20 questions, about 8 minutes, in class'), ('ecRisks2', 'Some questions about worry may cause mild discomfort; you may skip any question'), ('ecBenefits', 'No direct benefit; the results may help colleges plan support before exams'), ('ecContact', 'asha.verma@example.org, and the IEC at iec@uniraj.ac.in')]:
        fill('#' + i, v)
    pg.locator('#ecDlg button', has_text='Generate consent form').click(); pg.wait_for_timeout(300)
    print('consent went into doc:', J("(docsGet().find(d=>d.id===docCurrentId())||{}).title||'?'"))
    print('consent html sample', J("(()=>{const h=getEditorHTML();const i=h.indexOf('Informed Consent');return h.slice(Math.max(0,i-60),i+300)})()"))
    J("try{document.getElementById('ecDlg').close()}catch(e){}")
    step('design', 'C10'); print('C10', state('C10'), needed()[:200])
    print('STAGE C', J("['C1','C2','C3','C4','C5','C6','C7','C8','C9','C10'].map(i=>i+':'+subState(i).s).join(' ')"))
    # ---------- D ----------
    step('collect', 'D1')
    pg.locator('#subMain input[type=checkbox][onchange*="\'words\'"]').check(); step('collect', 'D1')
    pg.locator('#subMain input[type=checkbox][onchange*="\'time\'"]').check(); step('collect', 'D1')
    sel = pg.locator('#subMain select[onchange^="wPick(\'D1\',\'keep\'"]'); sel.select_option(index=1); sel.dispatch_event('change'); step('collect', 'D1')
    for k, v in [('n', '8'), ('date', '2026-11-05'), ('found', 'Two students did not understand item 6 in English'), ('changed', 'Added the Hindi version beside each GAD-7 item')]:
        loc = pg.locator('#subMain [onchange^="wPatch(\'D1\',\'%s\'"]' % k); loc.first.fill(v); loc.first.dispatch_event('change'); step('collect', 'D1')
    print('D1', state('D1'), needed()[:200])
    step('collect', 'D2')
    pg.locator('#subMain button', has_text='Add a row').first.click(); pg.wait_for_timeout(150)
    print('D2 keys', J("[...new Set([...document.querySelectorAll('#subMain [onchange^=\"logCell(\\'recruit\\',0\"]')].map(e=>e.getAttribute('onchange').split(',')[2]))]"))
    logfill('recruit', 0, {'date': '2026-11-20', 'site': 'College A, BA and BSc', 'appr': '160', 'agreed': '146', 'done': '142', 'left': '4'})
    step('collect', 'D2'); print('D2', state('D2'), needed()[:200])
    # data into the Statistics Lab, as a file
    J("document.getElementById('statsDlg').showModal()")
    d0=open(OUT+'data.csv').read().split('\n',1);open(OUT+'data2.csv','w').write(open(OUT+'template.csv').read().split('\n')[0].lstrip('\ufeff')+'\n'+d0[1])
    pg.set_input_files('#statsFile', OUT + 'data2.csv'); pg.wait_for_timeout(800)
    print('DATA CHECK', J("(document.getElementById('dcBox')||{}).innerText||'NONE'")[:1500])
    shot('datacheck')
    J("dcFix('dup')"); pg.wait_for_timeout(300)
    J("dcFix('far',window._dcScan.far[0]&&window._dcScan.far[0].col)"); pg.wait_for_timeout(300)
    J("dcFix('labels')"); pg.wait_for_timeout(300)
    print('DATA CHECK after', J("(document.getElementById('dcBox')||{}).innerText||'NONE'")[:800])
    print('rows', J("window._statsData.rows.length"), 'residence values', J("[...new Set(window._statsData.rows.map(r=>r[window._statsData.headers.indexOf('Residence')]))].join(',')"))
    pg.locator('#studyStatsHint button', has_text='Score the GAD-7').click(); pg.wait_for_timeout(300)
    pg.locator('#slScoreDlg button', has_text='Compute scores').click(); pg.wait_for_timeout(400)
    print('SCORE out', J("document.getElementById('slScoreOut').innerText")[:300])
    J("try{document.getElementById('slScoreDlg').close()}catch(e){}")
    print('HINT', J("document.getElementById('studyStatsHint').innerText")[:700])
    shot('plan_buttons')
    pg.locator('#studyStatsHint button', has_text='H1').click(); pg.wait_for_timeout(700)
    print('H1 fields', J("[...document.querySelectorAll('#statsFields select')].map(s=>s.id+'='+(s.options[s.selectedIndex]||{}).text).join(' ; ')"))
    print('H1 result', J("document.getElementById('statsResults').innerText")[:500].replace('\n', ' | '))
    J("resRecord()"); print('H1 rec', J("document.getElementById('resMsg').textContent"))
    pg.locator('#studyStatsHint button', has_text='H2').click(); pg.wait_for_timeout(700)
    print('H2 fields', J("[...document.querySelectorAll('#statsFields select')].map(s=>s.id+'='+(s.options[s.selectedIndex]||{}).text).join(' ; ')"))
    print('H2 result', J("document.getElementById('statsResults').innerText")[:600].replace('\n', ' | '))
    J("resRecord()"); print('H2 rec', J("document.getElementById('resMsg').textContent"))
    shot('h2')
    J("document.getElementById('statsDlg').close()")
    step('collect', 'D3'); print('D3', state('D3'), J("JSON.stringify(logRows(studyGet(),'clean'))")[:700])
    step('collect', 'D4'); print('D4', state('D4'), J("document.getElementById('subMain').innerText")[500:1300].replace('\n',' | '))
    step('collect', 'D5'); print('D5 view', J("document.getElementById('subMain').innerText")[:200].replace('\n',' | '))
    J("subStatusPick('D5','na')"); step('collect', 'D5'); print('D5', state('D5'), needed()[:120])
    step('collect', 'D6')
    pg.locator('#subMain button', has_text='Make rows from my hypotheses').click(); pg.wait_for_timeout(200)
    print('D6 rows', J("JSON.stringify(logRows(studyGet(),'interp'))")[:900])
    print('D6 after fill', J("JSON.stringify(logRows(studyGet(),'interp').map(r=>[r.res&&r.res.slice(0,60),r.size]))"))
    for r, (m, l) in enumerate([('Sleep hours and anxiety were only weakly related in this sample.', 'One time point; self-reported sleep.'), ('Hostel students reported more exam anxiety than day scholars.', 'Groups were not randomised; hostel students differ in other ways too.')]):
        logfill('interp', r, {'mean': m, 'lim': l})
    step('collect', 'D6'); print('D6', state('D6'), needed()[:200])
    print('STAGE D', J("['D1','D2','D3','D4','D5','D6'].map(i=>i+':'+subState(i).s).join(' ')"))
    # ---------- E ----------
    step('writing', 'E1'); pg.locator('#subMain button', has_text=re.compile('Go to the tool')).first.click(); pg.wait_for_timeout(300)
    print('E1 opens bpDlg', J("!!(document.getElementById('bpDlg')||{}).open"))
    print('BP buttons', J("[...document.querySelectorAll('#bpDlg button')].map(b=>b.innerText.trim()).filter(Boolean).slice(0,12)"))
    shot('bp')
    pg.locator('#bpDlg button', has_text=re.compile('outline|ढाँचा', re.I)).first.click(); pg.wait_for_timeout(500)
    print('book doc', J("(docsGet().find(d=>d.id===docCurrentId())||{}).title"), 'sections', J("editor.querySelectorAll('[data-sec]').length"))
    print('book first text', J("editor.innerText")[:1200].replace('\n',' | '))
    for i in ['E1','E2','E3','E4','E5','E6','E7','E8']:
        step('writing', i); print(i, state(i), needed()[:160].replace('\n',' '))
    shot('book')
    print('H1 stored apa', J("resList(studyGet()).map(r=>r.apa.slice(0,120))"))
    # student writes the abstract and keywords in the book
    J("""(()=>{const h=editor.querySelector('[data-sec="front.abstract"]');const p=document.createElement('p');p.textContent='This study examined sleep hours and exam anxiety among 139 first-year undergraduates at two Jaipur colleges, and compared hostel students with day scholars. Participants reported their usual sleep hours and completed the GAD-7. Shorter sleep went with higher anxiety, r = -.52, 95% CI [-.63, -.39]. Hostel students scored higher than day scholars, Hedges g = 0.60. The design was cross-sectional, so the direction of the link cannot be known. Colleges could add sleep advice to exam preparation, and a follow-up study could measure sleep with diaries.';h.after(p);const k=editor.querySelector('[data-sec="front.keywords"]');const q=document.createElement('p');q.textContent='Keywords: exam anxiety, sleep, GAD-7, undergraduates, India';k.after(q);docSaveBody(getEditorHTML())})()""")
    step('writing', 'E7'); print('E7', state('E7'), needed()[:200])
    # E8 AI-use statement
    step('writing', 'E8'); pg.locator('#subMain button', has_text='AI-use statement').first.click(); pg.wait_for_timeout(300)
    J("aiuBuild()"); print('AIU', J("document.getElementById('aiuOut').value")[:300])
    J("document.getElementById('aiuDlg').close()")
    step('writing', 'E8'); print('E8', state('E8'), needed()[:200], J("JSON.stringify(wGet(studyGet()).aiu||null)")[:100])
    # ---------- F ----------
    for i in ['F1','F2','F3','F4','F5','F6','F7']:
        step('review', i); print(i, state(i), needed()[:160].replace('\n',' '), '| tool:', J("[...document.querySelectorAll('#subMain button')].map(b=>b.innerText.trim()).filter(t=>/tool|Open|Check|Run/.test(t)).join(' / ')")[:200])
    # Word export of the book
    J("docSwitch(bbBookId())")
    with pg.expect_download(timeout=60000) as dl:
        J("downloadDoc()")
    path = dl.value.path(); import zipfile
    z = zipfile.ZipFile(path); x = z.read('word/document.xml').decode('utf8')
    txt = re.sub(r'<[^>]+>', ' ', x); txt = re.sub(r'\s+', ' ', txt)
    print('DOCX size', os.path.getsize(path), 'has TOC', 'TOC \\' in x or 'TOC ' in x, 'refs', 'Spitzer' in txt, 'H2 result', 'Welch' in txt)
    print('DOCX sample', txt[:600])
    open(OUT + 'book.txt', 'w').write(txt)
    import shutil; shutil.copy(path, OUT + 'book.docx')
    shot('final')
    ok(J("['A1','A2','A3','A4','B1','B2','B3','B4','B5','B6','B7','C1','C2','C3','C4','C6','C7','C10','D1','D2','D3','D4','D6','E2','E4','E5'].every(i=>subState(i).s==='dn')"), 'every step a student can finish from the app is done')
    ok(J("subState('C9').s")=='ap', 'ethics approved opens collection')
    ok(J("window._dcScan&&window._dcScan.dup.length===0"), 'the duplicate row was removed by the data check')
    ok(J("logRows(studyGet(),'clean').length")>=3, 'cleaning log filled by the data check and scoring')
    ok(J("resList(studyGet()).every(r=>!/_total|Sleep_hours/.test(r.apa))"), 'recorded results use readable names')
    ok(J("resList(studyGet()).some(r=>/r\\(\\d+\\) = -\\.[45]/.test(r.apa))"), 'H1 correlation recovers after cleaning (r about -.5)')
    ok('Spitzer' in txt and 'Welch' in txt, 'Word book carries the references and the results')
    ok(not [e for e in errors if e[0]=='pageerror'], 'no page errors')
    # a talk from the same study
    m=J("(()=>{const m=tkModel(studyGet(),15);return{t:m.slides.map(x=>x.role||(x.cover?'cover':'')),titles:m.slides.map(x=>x.title),big:m.slides.filter(x=>x.big).map(x=>x.big),warn:m.warn}})()")
    print('TALK', m['t'], m['titles'][:9], m['big'])
    ok(m['t'][0]=='cover' and 'question' in m['t'][:4],'the talk puts the research question on its own slide by slide 3 or 4')
    ok(m['t'].count('result')==2 and all(b.startswith(('r','g','d')) for b in m['big']),'one slide per recorded result, with its effect size shown large')
    main=[r for r in m['t'] if r not in ('appendix',)]
    ok(main[-1]=='refs' and main[-2]=='conclusion','conclusions are the last main slide, before the references')
    ok('Both findings support the hypotheses'==[x for x,r in zip(m['titles'],m['t']) if r=='conclusion'][0],'the conclusion title states the takeaway')
    ok('appendix' in m['t'],'likely questions are ready in an appendix')
    print('auto sections', J("editor.querySelectorAll('.bb-slot').length"))
    json.dump({'fails': fails, 'obs': obs}, open(OUT + 'journey1.json', 'w'))
    print('FAILED' if fails else 'ALL PASS', len(fails))
