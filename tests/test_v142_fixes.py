"""Version 142: the breaks found in the 28 Nov dress rehearsal.
- An invite code pasted into the access-code box opens account sign-up with the code filled in (F1).
- A review study plan saves without participants or variables, and builds a review outline (F21).
- A missing AI key opens the key window; no message points to the old gear icon (F4).
- Own questions: the answer type is chosen once and the Word file, form, codebook and data agree (F6, F18b).
- Own questions with reverse-worded lines get a total score through the scale scorer (F12).
- Check a scale starts with nothing ticked when items do not form one group, and offers one-tap groups (F11).
- Sending form answers to the Statistics Lab asks before replacing data already there (F18).
- Under-18 participants are flagged by the data check (F10).
- B3 is not ticked just because the library has papers; review exclusions need reasons (F5, F19).
- PRISMA "Fill from my library" fills screened, assessed and excluded boxes too (F20).
- The talk deck lists only cited sources and uses inserted results (F15, F16)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

SRC = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'index.html'), encoding='utf-8').read()
AUTH = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'auth.html'), encoding='utf-8').read()

ok('⚙ AI Provider / Key</b> at the top right' not in SRC and "click ⚙ at the top right" not in SRC and 'Open ⚙ and paste' not in SRC, 'no message sends the student to the old gear icon')
ok("appuInviteHint" in SRC and "appuInviteHint" in AUTH, 'access box hands an invite code to the account page')

with sync_playwright() as p:
    errs = []
    b, pg = harness.new_page(p, errs)
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)

    # F21: review plan and outline
    r = pg.evaluate("""(()=>{const o=studyGet();o.idea={topic:'What is known about sleep and test anxiety in students?'};o.write={B1:{type:'sys',crit:'Students; sleep; test anxiety; any design; English',reg:'none'}};o.design={};studySet(o);
      spOpen();document.getElementById('spType').value='review';spRevToggle();const hidden=document.getElementById('spVars').style.display==='none';
      spSave();const t=(studyGet().design||{}).type;editor.innerHTML='';draftBuild();
      const hs=[...editor.querySelectorAll('h2,h3')].map(h=>h.textContent);return{hidden,t,hs,built:!!(studyGet().draft||{}).built,txt:editor.innerText}})()""")
    ok(r['hidden'] and r['t'] == 'review', 'review plan hides participant fields and saves without an outcome variable')
    ok(r['built'] and any('Eligibility criteria' in h for h in r['hs']) and any('Study selection' in h for h in r['hs']) and any('Risk of bias' in h for h in r['hs']), 'systematic review outline has eligibility, selection and risk-of-bias sections')
    ok('Students; sleep; test anxiety' in r['txt'] and 'not registered' in r['txt'], 'review outline uses the B1 criteria and registration')
    ok(not any('2.2 Participants' in h for h in r['hs']), 'review outline has no Participants section')

    # F4: missing key opens the key window
    r = pg.evaluate("""(()=>{document.querySelectorAll('dialog[open]').forEach(d=>d.close());const m=apiMsg({message:'key'});return new Promise(res=>setTimeout(()=>res([m,!!document.querySelector('dialog[open]')]),300))})()""")
    ok('key window is opening' in r[0] and r[1], 'no-key message opens the key window')

    # F6 / F18b / F12: own questions
    r = pg.evaluate("""(()=>{document.querySelectorAll('dialog[open]').forEach(d=>d.close());const o=studyGet();o.idea={topic:'Does sleep predict exam anxiety?'};o.write={};
      o.design={type:'correlational',pop:'students',n:'120',vars:[{name:'Sleep quality',role:'predictor',type:'score',scale:'own'},{name:'Exam anxiety',role:'outcome',type:'score',scale:'gad7'}],hyp:'H1'};
      o.qn={built:true,demo:['age','gender'],own:{'Sleep quality':'I sleep well\\nI wake up tired (R)\\nI fall asleep quickly'},ownResp:{'Sleep quality':'freq5'}};studySet(o);
      const it=qnItems().filter(i=>i.own),h=document.createElement('div');h.innerHTML=qnHTML();
      const csv=sfCsvText([{pc:'P1',a:{age:'20',gender:'Man',Sleep_quality_01:'Often',Sleep_quality_02:'Never',Sleep_quality_03:'Always'}}]);
      return{n:it.length,rev:it.map(i=>!!i.rev),resp:it[0].resp,word:h.innerText,csv:csv,def:sfDef?null:null}})()""")
    ok(r['n'] == 3 and r['rev'] == [False, True, False], 'own questions: (R) marks the reverse-worded line and is removed from the text')
    ok(r['resp'][0] == 'Never' and 'Strongly disagree' not in r['word'].split('Sleep quality')[1], 'Word file uses the chosen answer type, not agree/disagree')
    ok('wake up tired (R)' not in r['word'], 'the (R) mark does not show to participants')
    ok(r['csv'].split('\n')[1] == 'P1,20,2,4,1,5', 'form answers arrive in the Lab as the codebook numbers')
    pg.evaluate("showTool('stats')"); pg.wait_for_timeout(500)
    r = pg.evaluate("""(()=>{const ta=document.getElementById('statsPaste');let csv='participant_id,age,gender,Sleep_quality_01,Sleep_quality_02,Sleep_quality_03\\n';
      [[4,2,5],[2,4,2],[5,1,4],[3,3,3],[1,5,2]].forEach((x,i)=>csv+='P'+i+','+(i==2?17:20)+',1,'+x.join(',')+'\\n');ta.value=csv;statsParse();studyStatsHint();
      const hint=document.getElementById('studyStatsHint').innerText,dc=(document.getElementById('dcBox')||{}).innerText||'';
      slScoreOwn(0);slScoreRun();const d=window._statsData,i=d.headers.indexOf('Sleep_quality_total');return{hint,dc,tot:d.rows.map(r=>r[i])}})()""")
    ok('Score my own questions' in r['hint'], 'Lab offers to score the own questions')
    ok(r['tot'] == ['13', '6', '14', '9', '4'], 'own total reverses the (R) item: ' + ','.join(r['tot']))
    ok('under 18' in r['dc'], 'data check flags a 17-year-old against an 18+ consent')

    # F11: Check a scale
    r = pg.evaluate("""(()=>{document.querySelectorAll('dialog[open]:not(#statsDlg)').forEach(d=>d.close());const s=document.getElementById('statsTest');s.value='alpha';statsFieldsRender();
      const t=[...document.querySelectorAll('.sfm_items:checked')].map(c=>c.parentNode.textContent.trim());return t})()""")
    ok('age' not in r and 'gender' not in r and 'Sleep_quality_total' not in r and len(r) == 3, 'Check a scale ticks only the one item group, never age, gender or totals: ' + ','.join(r))

    # F18: asking before replacing data
    r = pg.evaluate("""(()=>{let asked='';window.confirm=m=>{asked=m;return false};SF_ROWS=[{pc:'X',a:{}}];
      return sfToStats().then(()=>[asked,window._statsData.rows.length])})()""")
    ok('already holds' in r[0] and r[1] == 5, 'form answers do not replace Lab data without asking')

    # F5 / F19 / F20: review screening
    r = pg.evaluate("""(()=>{const o=studyGet();o.write={B1:{type:'sys'}};studySet(o);
      const lib=[];for(let i=0;i<5;i++)lib.push({title:'Paper '+i,author:'Author'+i+', A.',year:'202'+i,type:'Journal article',scr:{st:i<3?'included':'excluded',why:i==3?'Wrong population':''}});
      citSaveLib(lib);const before=b3AllDecided(studyGet());const nr=b3NoReason(studyGet());
      b1FillFromLibrary();const n=(wGet(studyGet()).B1||{}).n||{};return{before,nr,n}})()""")
    ok(not r['before'] and r['nr'] == 1, 'B3 not done while an excluded paper has no reason')
    ok(r['n'].get('scr') == '5' and r['n'].get('inc') == '3' and r['n'].get('exT') == '2' and r['n'].get('ft') == '3', 'PRISMA fill gives screened, excluded, assessed and included: ' + str(r['n']))

    # F16: talk references only cited sources
    r = pg.evaluate("""(()=>{const l=citGetLib();citEnsureIds(l);citSaveLib(l);const c=citGetLib()[0].cid;editor.innerHTML='<p>Text <span class="cit" data-cid="'+c+'">x</span>.</p>';
      const m=tkModel(studyGet(),15);const ref=m.slides.find(s=>s.role==='refs');return ref?ref.refs.length:0})()""")
    ok(r == 1, 'talk References slide lists only the cited source')

    # review fixes: RSES codes follow its own direction; PRISMA waits for every decision; Home ignores automatic ticks
    r = pg.evaluate("""(()=>{const x=SCALES.find(z=>z.id==='RSES');const it={resp:x.labels,scale:x};return [qnCodes(it)[0],slLabelCode(x,x.codings[0],x.labels[0])]})()""")
    ok(r[0][0] == r[1], 'RSES: codebook code for the first answer equals the scorer code: ' + str(r))
    r = pg.evaluate("""(()=>{const o=studyGet();o.write={B1:{type:'sys'}};studySet(o);const l=citGetLib();l.push({title:'Undecided',author:'Z, Z.',year:'2020',type:'Journal article'});citSaveLib(l);
      const o2=studyGet();o2.write.B1.n={};studySet(o2);b1FillFromLibrary();return Object.keys((wGet(studyGet()).B1||{}).n||{}).length})()""")
    ok(r == 0, 'PRISMA fill waits while a paper is undecided')
    r = pg.evaluate("""(()=>{const o=studyGet();o.design={type:'review'};o.write={};o.qn={};o.analysis={};studySet(o);return apEffStage({stage:'lit'})})()""")
    ok(r == 'lit', 'a review plan does not jump Home past Stage 2: ' + r)

    # rehearsal 2: name filled into an introduction saved earlier; test chooser uses totals; Insert lands in Results
    r = pg.evaluate("""(()=>{localStorage.setItem('appu_me',JSON.stringify({name:''}));const o=studyGet();o.qn=Object.assign({},o.qn||{},{intro:'A study by [your name]. Voluntary.'});studySet(o);
      const before=qnNameGap();localStorage.setItem('appu_me',JSON.stringify({name:'Priya Meena'}));return [before,qnNameGap(),qnModel().q.intro]})()""")
    ok(r[0] and not r[1] and 'Priya Meena' in r[2], 'a saved "[your name]" is filled once the name is on Home: ' + str(r))
    r = pg.evaluate("""(()=>{const o=studyGet();o.design={type:'correlational',vars:[{name:'Sleep quality',role:'predictor',type:'score',scale:'own'},{name:'Exam anxiety',role:'outcome',type:'score',scale:'GAD7'}]};studySet(o);
      const ta=document.getElementById('statsPaste');ta.value='id,age,Sleep_quality_01,Sleep_quality_02,GAD7_01,GAD7_total,Sleep_quality_total\\n'+[1,2,3,4,5,6].map(i=>i+',20,'+(i%5+1)+','+(i%4+1)+',1,'+(i*2)+','+(10-i)).join('\\n');statsParse();
      studyUseTest();return [...document.querySelectorAll('#statsFields select')].map(s=>s.options[s.selectedIndex].text)})()""")
    ok('Sleep_quality_total' in r and 'GAD7_total' in r, 'Use this test picks the total scores, not the first item: ' + str(r))
    r = pg.evaluate("""(()=>{editor.innerHTML='<h1 data-draft="1">T</h1><h2>3. Results</h2><p>x</p><h2>4. Discussion</h2><p>y</p><div data-bib="1"><h2>References</h2><p>R</p></div><p>end</p>';
      const r=document.createRange();r.selectNodeContents(editor);r.collapse(false);savedRange=r;window._statsAPA='RESULT SENTENCE r(4) = .50.';window._statsRun=null;statsInsert();
      const t=editor.innerText;return [t.indexOf('RESULT SENTENCE')<t.indexOf('4. Discussion'),t.indexOf('RESULT SENTENCE')>t.indexOf('3. Results')]})()""")
    ok(r[0] and r[1], 'Insert from the Lab with the cursor below the references goes into Results')

    # review round 3: a score with items but no total is not matched to a short column; two outlines take the newest
    r = pg.evaluate("""(()=>{const ta=document.getElementById('statsPaste');ta.value='id,gender,Gender_role_attitudes_01,Gender_role_attitudes_02\\n1,1,2,3\\n2,2,3,4\\n3,1,4,5';statsParse();
      return [planColFor({name:'Gender role attitudes',type:'score',scale:'own'}),planColFor({name:'Gender',type:'category'})]})()""")
    ok(r[0] == -1 and r[1] == 1, 'an unscored own scale is not matched to gender: ' + str(r))
    r = pg.evaluate("""(()=>{editor.innerHTML='<h1 data-draft="1">A</h1><h2>3. Results</h2><p>a</p><h2>4. Discussion</h2><h1 data-draft="1">B</h1><h2>3. Results</h2><p>b</p><h2>4. Discussion</h2>';savedRange=null;
      window._statsAPA='NEWEST r(4) = .50.';window._statsRun=null;statsInsert();const t=editor.innerText;return t.indexOf('NEWEST')>t.lastIndexOf('3. Results')})()""")
    ok(r, 'with two outlines the result goes into the newest one')

    real = [e for e in errs if e[0] == 'pageerror']
    ok(not real, 'no page errors: ' + str(real[:3]))
    b.close()
sys.exit(1 if fails else 0)
