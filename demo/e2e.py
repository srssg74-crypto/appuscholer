"""Appuscholar end-to-end walk-through on simulated data. Runs on GitHub Actions with real internet:
real OpenAlex/PubMed search, real Crossref DOI lookup, real Chart.js and PptxGenJS. Only the AI provider is mocked.
Writes every file the app produces, plus screenshots and a log of checks, into demo/out/."""
import json, os, re, sys, time, traceback
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(__file__))
from content import A, B, REFS, GEMINI

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'demo', 'out'); os.makedirs(OUT, exist_ok=True)
BASE = 'http://localhost:8765/index.html'
LOG = []; ERRS = []; SHOT = [0]

def log(ok, what, info=''):
    LOG.append({'ok': bool(ok), 'what': what, 'info': str(info)[:3000]}); print(('PASS ' if ok else 'FAIL ') + what, str(info)[:200], flush=True)

GATE = r"""(()=>{const v=crypto.subtle.verify.bind(crypto.subtle);crypto.subtle.verify=async(a,...r)=>(a&&a.name==='ECDSA')?true:v(a,...r);
const p=btoa(JSON.stringify({exp:'2030-01-01',n:'Demo',id:'d1'})).replace(/=+$/,'');
try{if(!localStorage.getItem('appu_license'))localStorage.setItem('appu_license',JSON.stringify({payload:{exp:'2030-01-01',n:'Demo',id:'d1'},raw:p+'.AAAA'}));
if(!localStorage.getItem('appu_terms'))localStorage.setItem('appu_terms',JSON.stringify({v:999}));localStorage.setItem('appu_seen','1');
localStorage.setItem('appu_provider','gemini');localStorage.setItem('appu_key_gemini','AIzaDEMO');
localStorage.setItem('appu_me',JSON.stringify({name:'Asha Verma (demo student)',pos:'MA Psychology, Jaipur',role:'',course:''}));}catch(e){}})();"""

def gemini(route):
    body = route.request.post_data or ''
    txt = GEMINI['feasib'] if 'feasibility' in body.lower() else (GEMINI['gap'] if 'research gap' in body.lower() else GEMINI['default'])
    route.fulfill(status=200, content_type='application/json', body=json.dumps({'candidates': [{'content': {'parts': [{'text': txt}]}, 'finishReason': 'STOP'}]}))

def fillv(pg, sel, val):
    pg.evaluate("([s,v])=>{const e=document.querySelector(s);if(!e)throw new Error('missing '+s);e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))}", [sel, val])

def shot(pg, name):
    SHOT[0] += 1; p = os.path.join(OUT, f'{SHOT[0]:02d}-{name}.png'); pg.screenshot(path=p); return p

def save_dl(pg, js, name, timeout=60000):
    with pg.expect_download(timeout=timeout) as d:
        pg.evaluate(js)
    p = os.path.join(OUT, name); d.value.save_as(p); return p

def close_dialogs(pg):
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>{try{d.close()}catch(e){}})")

def cite(text, cids):
    return re.sub(r'\{(\w+)\}', lambda m: '<span class="cit" contenteditable="false" data-cid="%s">…</span>' % cids.get(REFS.get(m.group(1), ''), 'missing'), text)

def fill_ph(pg, contains, html):
    """Replace the yellow placeholder whose text includes `contains` with `html` (inline text or <p> blocks)."""
    return pg.evaluate("""([c,h])=>{const ph=[...editor.querySelectorAll('.draft-ph')].find(x=>x.textContent.indexOf(c)>=0);if(!ph)return false;
      if(/^\\s*<p/.test(h)){const p=ph.closest('p');const tmp=document.createElement('div');tmp.innerHTML=h;[...tmp.childNodes].forEach(n=>p.parentNode.insertBefore(n,p));p.remove()}
      else{const tmp=document.createElement('span');tmp.innerHTML=h;ph.replaceWith(...tmp.childNodes)}
      editor.dispatchEvent(new Event('input'));return true}""", [contains, html])

def caret_in(pg, sel):
    pg.evaluate("""s=>{const el=editor.querySelector(s);const r=document.createRange();r.selectNodeContents(el);r.collapse(false);const g=getSelection();g.removeAllRanges();g.addRange(r);savedRange=r.cloneRange()}""", sel)

def new_res_par(pg, k):
    pg.evaluate("""k=>{let anchor=editor.querySelector('#res'+(k-1))||editor.querySelector('#res0');const p=document.createElement('p');p.id='res'+k;anchor.after(p);}""", k)
    caret_in(pg, '#res%d' % k)

def run_test(pg, test, selects=None, checks=None, extra=None, k=1, insert=True):
    pg.evaluate("document.getElementById('statsDlg').open||document.getElementById('statsDlg').showModal()")
    pg.evaluate("t=>{statsTest.value=t;statsFieldsRender()}", test)
    for fid, colname in (selects or {}).items():
        ok = pg.evaluate("""([f,c])=>{const s=document.getElementById('sf_'+f);if(!s)return false;const o=[...s.options].find(o=>o.textContent.trim()===c);if(!o)return false;s.value=o.value;return true}""", [fid, colname])
        if not ok: log(False, f'{test}: column {colname} for {fid}')
    for fid, names in (checks or {}).items():
        pg.evaluate("""([f,ns])=>{document.querySelectorAll('.sfm_'+f).forEach(cb=>{const lab=cb.closest('label');cb.checked=ns.indexOf((lab?lab.textContent:'').trim())>=0})}""", [fid, names])
    for fid, val in (extra or {}).items():
        pg.evaluate("([f,v])=>{const e=document.getElementById('sf_'+f);if(e)e.value=v}", [fid, val])
    pg.evaluate("statsRunNow()"); pg.wait_for_timeout(1200)
    apa = pg.evaluate("window._statsAPA||''")
    log(bool(apa), f'Statistics Lab: {test}', apa[:220])
    if insert and apa:
        new_res_par(pg, k); pg.evaluate("statsInsert()"); pg.wait_for_timeout(500)
    return apa

def load_data(pg, path, name):
    txt = open(path, encoding='utf-8').read()
    pg.evaluate("document.getElementById('statsDlg').open||document.getElementById('statsDlg').showModal()")
    pg.evaluate("([t,n])=>{statsDsName.value=n;try{rtNameChanged()}catch(e){};statsPaste.value=t;statsParse()}", [txt, name]); pg.wait_for_timeout(1500)
    rows = pg.evaluate("window._statsData?window._statsData.rows.length:0"); log(rows > 500, f'Data loaded: {name}', f'{rows} rows')

def score_scale(pg, sid, coding=0):
    pg.evaluate("id=>slScoreOpen(id)", sid); pg.wait_for_timeout(400)
    pg.evaluate("c=>{const s=document.getElementById('slCoding');if(s)s.value=String(c)}", coding)
    pg.evaluate("slScoreRun()"); pg.wait_for_timeout(1200)
    out = pg.evaluate("document.getElementById('slScoreOut').innerText"); log('Added' in out, f'Scale scored: {sid}', out[:200])
    pg.evaluate("document.getElementById('slScoreDlg').close()")

def add_refs(pg, keys):
    cids = {}
    pg.evaluate("showTool('cite')")
    for k in keys:
        doi = REFS[k]
        pg.evaluate("d=>{citClearForm&&citClearForm();citDOI.value=d}", doi); pg.evaluate("citLookup()")
        for _ in range(30):
            pg.wait_for_timeout(500)
            if pg.evaluate("citTitle.value.length>5"): break
        title = pg.evaluate("citTitle.value"); log(len(title) > 5, f'Crossref DOI lookup: {k}', title)
        if len(title) > 5:
            pg.evaluate("citAdd()"); pg.wait_for_timeout(300)
        cid = pg.evaluate("d=>{const e=citGetLib().find(x=>String(x.doi||'').toLowerCase().indexOf(d.toLowerCase())>=0);return e?e.cid:''}", doi)
        if cid: cids[doi] = cid
    return cids

def study(pg, S, label, project, data_files, tests_fn, figure_fn, gap_refs, refs_keys, design, vars_js):
    # ---- project and Stage 1 ----
    pg.evaluate("openNewProjectDirect()"); fillv(pg, '#sapName', project); pg.evaluate("saveAsProject()"); pg.wait_for_timeout(600); close_dialogs(pg)
    pg.evaluate("showTool('idea')"); pg.wait_for_timeout(300)
    fillv(pg, '#ideaTopic', S.get('topic1', S['topic'])); fillv(pg, '#ideaResources', S['resources']); fillv(pg, '#ideaTimeframe', S['timeframe']); fillv(pg, '#ideaConstraints', S['constraints'])
    pg.evaluate("ideaAssess()"); pg.wait_for_timeout(2500)
    log('Verdict' in pg.evaluate("aiOut.textContent") or 'test reply' in pg.evaluate("aiOut.textContent"), f'{label} Stage 1: feasibility assessment shown')
    shot(pg, f'{label}-stage1-idea')
    fillv(pg, '#ideaTopic', S['topic']); pg.evaluate("ideaSave()")   # edit 1: sharpen the question
    log(pg.evaluate("studyIdea().topic") == S['topic'], f'{label} Edit: research question changed and saved')
    # ---- Stage 2: real search, gap, key papers ----
    pg.evaluate("showTool('research')"); pg.wait_for_timeout(300)
    log(pg.evaluate("rsTopic.value") == S['topic'], f'{label} Stage 2: search box filled from Stage 1')
    fillv(pg, '#rsTopic', S['search']); pg.evaluate("researchSearch()")
    for _ in range(60):
        pg.wait_for_timeout(1000)
        if pg.evaluate("(typeof rsResults!=='undefined'?rsResults:[]).length>=3"): break
    n = pg.evaluate("(typeof rsResults!=='undefined'?rsResults:[]).length"); log(n >= 3, f'{label} Stage 2: real paper search (OpenAlex/PubMed)', f'{n} results')
    shot(pg, f'{label}-stage2-search')
    pg.evaluate("(()=>{const R=(typeof rsResults!=='undefined'?rsResults:[]);let ix=R.map((r,i)=>[+(r.year||0),i]).filter(x=>x[0]>=2010).map(x=>x[1]).slice(0,2);if(ix.length<2)ix=[0,1];ix.forEach(i=>{const c=document.getElementById('rsChk'+i);if(c)c.checked=true})})()")   # the student ticks two recent papers
    pg.evaluate("researchGapFinder()"); pg.wait_for_timeout(2500)
    pg.evaluate("gapDlgOpen()"); pg.wait_for_timeout(300); fillv(pg, '#gapText', S.get('gap1', S['gap'])); pg.evaluate("gapSave()"); pg.wait_for_timeout(300)
    pg.evaluate("gapDlgOpen()"); pg.wait_for_timeout(300); fillv(pg, '#gapText', S['gap']); pg.evaluate("gapSave()")   # edit 2: rewrite the gap
    g = pg.evaluate("studyGet().gap"); log(g and g['text'] == S['gap'] and len(g.get('cids', [])) >= 1, f'{label} Stage 2: research gap and key papers saved, then edited', g)
    # ---- citations by DOI (real Crossref) ----
    cids = add_refs(pg, refs_keys)
    # ---- Stage 3: plan, then edit it ----
    pg.evaluate("showTool('design')"); pg.evaluate("spOpen()"); pg.wait_for_timeout(300)
    fillv(pg, '#spType', design); fillv(pg, '#spPop', S['pop']); fillv(pg, '#spN', '1200'); fillv(pg, '#spSampling', S['sampling']); fillv(pg, '#spHyp', S['hyp'])
    pg.evaluate(vars_js); shot(pg, f'{label}-stage3-plan'); pg.evaluate("spSave()"); pg.wait_for_timeout(300)
    pg.evaluate("spOpen()"); fillv(pg, '#spN', '1240' if label == 'A' else '1133'); pg.evaluate("spAddRow()")
    pg.evaluate("""l=>{const r=[...document.querySelectorAll('#spVars tbody tr')].pop();r.querySelector('.spName').value=l==='A'?'Residence':'Low birth weight';r.querySelector('.spRole').value='covariate';r.querySelector('.spTypeV').value='category';r.querySelector('.spLevels').value=l==='A'?'Urban, Rural':'Yes, No'}""", label)
    pg.evaluate("spSave()"); log(len(pg.evaluate("studyGet().design.vars")) >= 4, f'{label} Edit: study plan changed (sample size, one more variable)')
    pg.evaluate("document.getElementById('protoDlg').showModal();protoLoad()"); pg.wait_for_timeout(300)
    pr = pg.evaluate("[protoBg.value,protoObj.value,protoDesign.value,protoPart.value]"); log(all(pr), f'{label} Stage 3: protocol filled from the study', pr[2][:150])
    shot(pg, f'{label}-stage3-protocol'); pg.evaluate("try{protoSave()}catch(e){}"); close_dialogs(pg)
    # ---- Stage 4: questionnaire ----
    pg.evaluate("showTool('stats');qnOpen()"); pg.wait_for_timeout(400); shot(pg, f'{label}-stage4-questionnaire')
    pg.evaluate("qnSave()")
    save_dl(pg, "qnWord()", f'{label}-questionnaire.docx'); save_dl(pg, "qnCsv()", f'{label}-data-template.csv'); save_dl(pg, "qnCodebook()", f'{label}-codebook.csv')
    log(True, f'{label} Stage 4: questionnaire Word file, data template and codebook downloaded'); close_dialogs(pg)
    # ---- Stage 5: document and outline ----
    pg.evaluate("p=>{window.prompt=()=>p}", project + ' paper'); pg.evaluate("docNew()"); pg.wait_for_timeout(400)
    pg.evaluate("showTool('cite');citStyle.value='apa';citStyleChanged();draftBuild()"); pg.wait_for_timeout(800)
    log(pg.evaluate("editor.querySelectorAll('.draft-ph').length") > 5, f'{label} Stage 5: paper outline built from the study')
    shot(pg, f'{label}-stage5-outline')
    fill_ph(pg, 'why the topic matters', cite(''.join(S['intro']), cids))
    fill_ph(pg, 'how the sample size', S['participants'])
    fill_ph(pg, 'ethics committee name', S['procedure'])
    fill_ph(pg, 'alpha level', S['analysis'])
    fill_ph(pg, 'main finding in plain words', cite(''.join(S['discussion']), cids))
    fill_ph(pg, 'two or three sentences', S['conclusion'])
    fill_ph(pg, 'main result with the test', S['abstract_res']); fill_ph(pg, 'one sentence', S['abstract_con'])
    # measures placeholder for own-question variables
    pg.evaluate("""()=>{editor.querySelectorAll('.draft-ph').forEach(x=>{if(/how it was measured/.test(x.textContent))x.replaceWith(document.createTextNode('Taken from the hospital laboratory report or the antenatal card.'))});editor.dispatchEvent(new Event('input'))}""")
    pg.evaluate("""()=>{const ph=[...editor.querySelectorAll('.draft-ph')].find(x=>/Statistics Lab/.test(x.textContent));const p=ph.closest('p');p.id='res0';p.innerHTML='Results for each hypothesis follow.';editor.dispatchEvent(new Event('input'))}""")
    pg.wait_for_timeout(900)
    # ---- Stage 4 again: data, scoring, tests, figure ----
    for path, nm in data_files[:1]: load_data(pg, path, nm)
    pg.wait_for_timeout(300); shot(pg, f'{label}-stage4-statslab-plan-hint')
    hint = pg.evaluate("(document.getElementById('studyStatsHint')||{}).innerText||''"); log(len(hint) > 20, f'{label} Statistics Lab suggests a test from the plan', hint[:200])
    k = tests_fn(pg, data_files)
    figure_fn(pg, k)
    close_dialogs(pg)
    # ---- edit: the student swaps data column names for plain words in the Results ----
    words = WORDS_A if label == 'A' else WORDS_B
    nt = pg.evaluate("""w=>{const tw=document.createTreeWalker(editor,NodeFilter.SHOW_TEXT);let n,c=0;while(n=tw.nextNode()){const pe=n.parentElement;if(!pe||!(pe.closest('.stat-tag')||/^(Distribution|Figure)/.test((pe.closest('p,figcaption,div')||pe).textContent.trim())))continue;let t=n.textContent;w.forEach(([a,b])=>{t=t.split(a).join(b)});if(t!==n.textContent){n.textContent=t;c++}}editor.dispatchEvent(new Event('input'));return c}""", words)
    left = pg.evaluate("w=>{const t=[...editor.querySelectorAll('.stat-tag')].map(x=>x.innerText).join(' ');return w.filter(([a])=>/_/.test(a)&&t.indexOf(a)>=0).map(x=>x[0])}", words)
    log(nt > 0 and not left and pg.evaluate("editor.querySelectorAll('.stat-tag').length") > 0, f'{label} Edit: column names in Results changed to plain words; results stay tagged', f'{nt} text pieces edited; left: {left}')
    # ---- edits in the paper: citation style and a deleted citation ----
    pg.evaluate("showTool('cite');citStyle.value='vancouver';citStyleChanged()"); pg.wait_for_timeout(700)
    shot(pg, f'{label}-edit-vancouver')
    nums = pg.evaluate("[...editor.querySelectorAll('span.cit')].map(s=>s.innerText)"); log(all(re.match(r'^\[\d+(,\d+)*\]$', x) for x in nums if x), f'{label} Edit: switched to Vancouver, citations numbered', nums[:8])
    pg.evaluate("citStyle.value='apa';citStyleChanged()"); pg.wait_for_timeout(700)
    nbib = pg.evaluate("editor.querySelectorAll('[data-bib=\"i\"]').length"); log(nbib >= 3, f'{label} Edit: back to APA, reference list has {nbib} entries')
    pg.evaluate("""()=>{const sp=[...editor.querySelectorAll('#res0 ~ p span.cit, p span.cit')].pop();if(sp){const pv=sp.previousSibling;if(pv&&pv.nodeType===3)pv.textContent=pv.textContent.replace(/\\s+$/,'');sp.remove();editor.dispatchEvent(new Event('input'))}}""")
    pg.wait_for_timeout(1200)
    log(pg.evaluate("editor.querySelectorAll('[data-bib=\"i\"]').length") <= nbib, f'{label} Edit: deleted a citation; reference list updated')
    pg.evaluate("editor.querySelectorAll('#res0').forEach(p=>p.removeAttribute('id'))")
    # ---- Stage 6 ----
    pg.evaluate("showTool('slides')"); pg.wait_for_timeout(300)
    res = pg.evaluate("reviewRun().map(r=>[r[0],r[1]])"); json.dump(res, open(os.path.join(OUT, f'{label}-plan-check.json'), 'w'), indent=1, ensure_ascii=False)
    log(sum(1 for r in res if r[0]) >= len(res) - 3, f'{label} Stage 6: paper checked against the plan', f"{sum(1 for r in res if r[0])} of {len(res)} pass: " + '; '.join(r[1] for r in res if not r[0]))
    shot(pg, f'{label}-stage6-check')
    pg.evaluate("pptxBuildPreview()"); pg.wait_for_timeout(800)
    save_dl(pg, "pptxDownload()", f'{label}-slides.pptx', 120000); log(True, f'{label} Slides (PowerPoint) downloaded')
    save_dl(pg, "posterDownload()", f'{label}-poster-A0.pptx', 120000); log(True, f'{label} Poster (A0) downloaded')
    save_dl(pg, "downloadDoc()", f'{label}-paper.docx', 120000); log(True, f'{label} Paper downloaded as Word')
    save_dl(pg, "downloadLatex()", f'{label}-paper.tex'); log(True, f'{label} Paper downloaded as LaTeX')
    pg.evaluate("showTool('close')"); pg.wait_for_timeout(300)
    try: pg.evaluate("clRun()"); pg.wait_for_timeout(2500); shot(pg, f'{label}-stage6-closeness')
    except Exception as e: log(False, f'{label} closeness check', e)
    pg.evaluate("studyDlgOpen()"); pg.wait_for_timeout(300); shot(pg, f'{label}-my-study-plan'); close_dialogs(pg)
    open(os.path.join(OUT, f'{label}-paper.html'), 'w').write('<!doctype html><meta charset=utf-8><title>%s</title><body style="font:16px/1.6 Georgia;max-width:820px;margin:30px auto">' % project + pg.evaluate("editor.innerHTML.replace(/\\u200b/g,'')") + '</body>')

def tests_A(pg, files):
    score_scale(pg, 'GAD7', 0); score_scale(pg, 'RSES', 0); score_scale(pg, 'SWLS', 0)
    pg.evaluate("studyUseTest()"); pg.wait_for_timeout(300)
    k = 1
    run_test(pg, 'ttestInd', {'dv': 'GAD7_total', 'iv': 'anaemia_34wk'}, k=k); k += 1
    run_test(pg, 'pearson', {'v1': 'RSES_total', 'v2': 'SWLS_total'}, k=k); k += 1
    run_test(pg, 'pearson', {'v1': 'GAD7_total', 'v2': 'SWLS_total'}, k=k); k += 1
    run_test(pg, 'ttestPaired', {'v1': 'hb_16wk', 'v2': 'hb_34wk'}, k=k); k += 1
    run_test(pg, 'mregress', {'dv': 'GAD7_total'}, {'preds': ['hb_34wk', 'age'], 'cats': ['parity']}, k=k); k += 1
    run_test(pg, 'alpha', checks={'items': ['GAD7_%02d' % i for i in range(1, 8)]}, k=k); k += 1
    run_test(pg, 'chisq', {'v1': 'anaemia_34wk', 'v2': 'parity'}, k=k); k += 1
    load_data(pg, files[1][0], files[1][1])
    run_test(pg, 'ttestPaired', {'v1': 'mother_GAD7_total', 'v2': 'father_GAD7_total'}, k=k); k += 1
    load_data(pg, files[0][0], files[0][1]); score_scale(pg, 'GAD7', 0)
    return k

def fig_A(pg, k):
    new_res_par(pg, k)
    pg.evaluate("document.getElementById('statsDlg').close();vzOpen()"); pg.wait_for_timeout(600)
    pg.evaluate("""()=>{vzType.value='box';const y=[...vzY.options].find(o=>o.textContent==='GAD7_total');if(y)vzY.value=y.value;const g=[...vzG.options].find(o=>o.textContent==='anaemia_34wk');if(g)vzG.value=g.value;vzSync();vzWhere.value='cursor'}""")
    pg.wait_for_timeout(800); shot(pg, 'A-figure-boxplot'); pg.evaluate("vzInsert()"); pg.wait_for_timeout(1500)
    log(pg.evaluate("editor.querySelectorAll('img').length") >= 1, 'A Figure inserted into Results')

def tests_B(pg, files):
    k = 1
    run_test(pg, 'chisq', {'v1': 'paracetamol_given', 'v2': 'seroconverted'}, k=k); k += 1
    run_test(pg, 'chisq', {'v1': 'infant_sex', 'v2': 'seroconverted'}, k=k); k += 1
    run_test(pg, 'logistic', {'dv': 'seroconverted'}, {'preds': ['birth_weight_g'], 'cats': ['paracetamol_given', 'infant_sex']}, k=k); k += 1
    run_test(pg, 'pearson', {'v1': 'maternal_hb_34wk', 'v2': 'birth_weight_g'}, k=k); k += 1
    run_test(pg, 'ttestInd', {'dv': 'birth_weight_g', 'iv': 'infant_sex'}, k=k); k += 1
    return k

def fig_B(pg, k):
    new_res_par(pg, k)
    pg.evaluate("document.getElementById('statsDlg').close();vzOpen()"); pg.wait_for_timeout(600)
    pg.evaluate("""()=>{vzType.value='hist';const y=[...vzY.options].find(o=>o.textContent==='birth_weight_g');if(y)vzY.value=y.value;vzSync();vzWhere.value='cursor'}""")
    pg.wait_for_timeout(800); pg.evaluate("vzInsert()"); pg.wait_for_timeout(1500)
    log(pg.evaluate("editor.querySelectorAll('img').length") >= 1, 'B Figure inserted into Results')

WORDS_A = [['mother_GAD7_total', "the mothers' GAD-7 scores"], ['father_GAD7_total', "the fathers' GAD-7 scores"], ['GAD7_total', 'GAD-7 score'], ['RSES_total', 'self-esteem (RSES)'], ['SWLS_total', 'life satisfaction (SWLS)'], ['hb_16wk', 'haemoglobin at 16 weeks'], ['hb_34wk', 'haemoglobin at 34 weeks'], ['anaemia_34wk', 'anaemia at 34 weeks'], ['between Yes (', 'between women with anaemia ('], [' and No (', ' and women without anaemia (']]
WORDS_B = [['maternal_hb_34wk', "the mother's haemoglobin at 34 weeks"], ['paracetamol_given', 'paracetamol after MR1'], ['seroconverted', 'seroconversion'], ['infant_sex', 'infant sex'], ['birth_weight_g', 'birth weight (g)'], ['between Boy (', 'between boys ('], [' and Girl (', ' and girls (']]
VARS_A = """(()=>{const tb=document.querySelector('#spVars tbody');tb.innerHTML='';const add=(n,r,t,s,l)=>{spAddRow();const row=[...tb.querySelectorAll('tr')].pop();row.querySelector('.spName').value=n;row.querySelector('.spRole').value=r;row.querySelector('.spTypeV').value=t;row.querySelector('.spScale').value=s;row.querySelector('.spLevels').value=l||''};
add('Anxiety','outcome','score','GAD7');add('Life satisfaction','outcome','score','SWLS');add('Self-esteem','predictor','score','RSES');add('Anaemia at 34 weeks','group','yesno','');add('Haemoglobin at 34 weeks','predictor','score','own');add('Parity','covariate','category','','First pregnancy, Second or later');add('Age','covariate','score','own')})()"""
VARS_B = """(()=>{const tb=document.querySelector('#spVars tbody');tb.innerHTML='';const add=(n,r,t,s,l)=>{spAddRow();const row=[...tb.querySelectorAll('tr')].pop();row.querySelector('.spName').value=n;row.querySelector('.spRole').value=r;row.querySelector('.spTypeV').value=t;row.querySelector('.spScale').value=s;row.querySelector('.spLevels').value=l||''};
add('Seroconversion','outcome','yesno','');add('Paracetamol after MR1','predictor','yesno','');add('Infant sex','group','category','','Boy, Girl');add('Birth weight','covariate','score','own')})()"""

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1366, 'height': 900}, service_workers='block', accept_downloads=True)
        ctx.add_init_script(GATE); ctx.route('**/generativelanguage.googleapis.com/**', gemini)
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: ERRS.append(str(e)[:300]))
        pg.on('dialog', lambda d: d.accept())
        pg.goto(BASE); pg.wait_for_timeout(4000)
        D = os.path.join(ROOT, 'demo')
        try:
            study(pg, A, 'A', 'Janani A: anaemia, anxiety and well-being', [(os.path.join(D, 'janani_mothers.csv'), 'Janani mothers'), (os.path.join(D, 'janani_fathers.csv'), 'Janani fathers')], tests_A, fig_A, None,
                  ['kassebaum', 'rahman', 'penarosas', 'dennis', 'grigoriadis', 'spitzer', 'diener'], 'survey', VARS_A)
        except Exception as e:
            log(False, 'Study A crashed', traceback.format_exc()[-3000:]); shot(pg, 'A-crash')
        try:
            pg.evaluate("setActiveProject('',{skipJump:true})")
            study(pg, B, 'B', 'Janani B: paracetamol and MR1 response', [(os.path.join(D, 'janani_infants.csv'), 'Janani infants')], tests_B, fig_B, None,
                  ['moss', 'prymula'], 'cohort', VARS_B)
        except Exception as e:
            log(False, 'Study B crashed', traceback.format_exc()[-3000:]); shot(pg, 'B-crash')
        try: save_dl(pg, "backupExport()", 'backup.json'); log(True, 'Backup of everything downloaded')
        except Exception as e: log(False, 'Backup', e)
        b.close()
    json.dump({'checks': LOG, 'page_errors': ERRS}, open(os.path.join(OUT, 'checks.json'), 'w'), indent=1, ensure_ascii=False)
    print('PASSED', sum(1 for x in LOG if x['ok']), 'FAILED', sum(1 for x in LOG if not x['ok']), 'PAGE ERRORS', len(ERRS))

if __name__ == '__main__':
    main()
