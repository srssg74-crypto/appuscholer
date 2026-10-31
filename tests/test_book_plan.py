"""The book plan: nothing may be left without a home.
Every item of STROBE, CONSORT 2025, PRISMA 2020, COREQ and SRQR, every UGC 2022 document and every F4 thesis
item must map to a section of the Appuscholar standard plan that applies to the matching design; every one of
the 42 steps must feed the book or say why it does not; every plan must use real section ids."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    # --- structure ---
    r=J("""(()=>{const ids=[];bpWalk(n=>ids.push(n.id));const dup=ids.filter((x,i)=>ids.indexOf(x)!==i);
      const bad=[];bpWalk(n=>{if(!n.t||!n.t[0]||!n.t[1])bad.push(n.id+' title');if(!BP_MODES[n.m])bad.push(n.id+' mode');
        if(!(n.k&&n.k.length)&&(!n.g||!n.g[0]||!n.g[1]))bad.push(n.id+' guide');
        (n.s||[]).forEach(s=>{if(!SUBSTAGES.some(x=>x[0]===s))bad.push(n.id+' step '+s)});
        if(!(n.k&&n.k.length)&&!(n.s||[]).length&&n.id!=='front.ack')bad.push(n.id+' no step')});
      return{n:ids.length,dup:dup,bad:bad}})()""")
    ok(r['n']>80,'standard plan has %d sections'%r['n'])
    ok(not r['dup'],'section ids are unique %s'%r['dup'])
    ok(not r['bad'],'every section has titles in both languages, a mode, a guide and a step %s'%r['bad'][:8])
    # --- every checklist item has a home that applies to the matching design ---
    r=J("""(()=>{const tagsFor={strobe:BP_DESIGN_TAGS.survey,consort:BP_DESIGN_TAGS.experiment,coreq:BP_DESIGN_TAGS.qualitative,srqr:BP_DESIGN_TAGS.qualitative,prisma:['review']};
      const miss=[],extra=[],count={};
      Object.keys(BP_COVER_TAG).forEach(k=>{const items=F2_LISTS[k].items,map=BP_COVER[k]||{};count[k]=items.length;
        items.forEach(it=>{const ids=map[it[0]];if(!Array.isArray(ids)||!ids.length){miss.push(k+' '+it[0]+' no home');return}
          ids.forEach(id=>{const n=bpNode(id);if(!n)miss.push(k+' '+it[0]+' -> unknown '+id);else if(!bpApplies(n,tagsFor[k]))miss.push(k+' '+it[0]+' -> '+id+' not in this design')})});
        Object.keys(map).forEach(x=>{if(!items.some(it=>it[0]===x))extra.push(k+' '+x)})});
      return{miss:miss,extra:extra,count:count}})()""")
    ok(not r['miss'],'every reporting-checklist item has a home in the plan for its design %s'%r['miss'][:10])
    ok(not r['extra'],'no stale checklist ids in the map %s'%r['extra'])
    ok(r['count']=={'strobe':22,'consort':42,'coreq':32,'srqr':21,'prisma':27},'all five checklists counted in full %s'%r['count'])
    r=J("""(()=>{const out=[];const ugc=PACKS_BUILTIN.find(p=>p.id==='ugc-phd-2022').docs;
      ugc.forEach(d=>{const v=BP_COVER.ugc[d[0]];if(v!=='process'&&!(Array.isArray(v)&&v.length&&v.every(bpNode)))out.push('ugc '+d[0])});
      F4_THESIS.forEach(d=>{const v=BP_COVER.f4[d[0]];if(v!=='process'&&!(Array.isArray(v)&&v.length&&v.every(bpNode)))out.push('f4 '+d[0])});
      return out})()""")
    ok(not r,'every UGC 2022 document and F4 thesis item is either a page of the book or a process record %s'%r)
    # --- workflow and book: no orphan step ---
    r=J("""(()=>{const out=[];SUBSTAGES.forEach(x=>{const n=bpStepNodes(x[0]).length;if(!n&&!BP_NOBOOK[x[0]])out.push(x[0]+' feeds nothing');if(n&&BP_NOBOOK[x[0]])out.push(x[0]+' both')});return{out:out,n:SUBSTAGES.length}})()""")
    ok(r['n']==42 and not r['out'],'each of the 42 steps feeds the book or says why not %s'%r['out'])
    # --- plans use real ids, and the editions keep what they must ---
    r=J("""(()=>{const out=[];BP_PLANS.forEach(p=>(p.groups||[]).forEach(g=>g[2].forEach(id=>{if(!bpNode(id))out.push(p.id+' '+id)})));
      const syn=[].concat(...BP_PLANS.find(p=>p.id==='synopsis').groups.map(g=>g[2]));bpWalk(n=>{if(n.syn&&!(n.k&&n.k.length)&&syn.indexOf(n.id)<0)out.push('synopsis lacks '+n.id)});
      const apa=[].concat(...BP_PLANS.find(p=>p.id==='apa').groups.map(g=>g[2]));
      ['method','results','disc'].forEach(c=>bpWalk(n=>{if(!(n.k&&n.k.length)&&apa.indexOf(n.id)<0)out.push('apa lacks '+n.id)},bpNode(c).k,1));
      return out})()""")
    ok(not r,'synopsis and APA plans use real sections and leave none of theirs out %s'%r[:8])
    # --- the plan follows the design ---
    J("openSaveAsProject();document.getElementById('sapName').value='Book';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.design=Object.assign(o.design||{},{type:'survey'});studySet(o)")
    ids=J("(()=>{const a=[];bpWalk(n=>a.push(n.id),bpTree(studyGet(),'thesis'));return a})()")
    ok('results.main' in ids and 'results.themes' not in ids and 'method.random' not in ids and 'syn.timeline' not in ids,'a survey gets hypotheses results, no themes, no randomisation, no synopsis-only parts')
    ok(J("bpNumbers(bpTree(studyGet(),'thesis'))['method.size']")=='3.3.3','sample size numbered 3.3.3 for a survey')
    J("const o=studyGet();o.design.type='qualitative';studySet(o)")
    ids=J("(()=>{const a=[];bpWalk(n=>a.push(n.id),bpTree(studyGet(),'thesis'));return a})()")
    ok('results.themes' in ids and 'method.reflex' in ids and 'results.main' not in ids and 'intro.hypotheses' not in ids,'a qualitative study gets themes and reflexivity, no hypotheses')
    J("const o=studyGet();o.design.type='experiment';studySet(o)")
    ids=J("(()=>{const a=[];bpWalk(n=>a.push(n.id),bpTree(studyGet(),'thesis'));return a})()")
    ok('method.random' in ids and 'results.harms' in ids and 'back.registration' in ids,'a trial gets randomisation, harms and registration')
    J("const o=studyGet();o.design.type='survey';studySet(o)")
    # --- the step shows where it goes; the plan dialog ---
    h=J("bpStepBookHTML('C3',studyGet())")
    ok('3.3.3' in h and 'Sample size' in h,'C3 says it goes into 3.3.3 Sample size')
    ok('study record' in J("bpStepBookHTML('A4',studyGet())"),'A4 says why it writes no part of the book')
    J("subOpen('design','C3')")
    ok('Goes into the book at' in J("document.getElementById('subMain').innerText"),'the line shows inside the step')
    J("document.getElementById('subDlg').close();bpOpen('method.size')")
    t=J("document.getElementById('bpDlg').innerText")
    ok('Chapter 3: Method' in t and 'Report' in t and 'Interpret' in t and 'STROBE' in t,'plan dialog shows chapters, the writing modes and the checklist it was checked against')
    ok(J("document.querySelectorAll('#bpDlg .bp-row').length")>40,'plan dialog lists the sections')
    J("bpPlanSet('synopsis')")
    t=J("document.getElementById('bpDlg').innerText")
    ok('Timeline' in t and 'Expected outcome' in t and 'Results for each hypothesis' not in t,'synopsis plan shows synopsis parts and no results')
    J("bpPlanSet('std');bpInsertOutline()")
    r=J("({h1:[...editor.querySelectorAll('h1[data-sec]')].map(h=>h.textContent),sec:!!editor.querySelector('h3[data-sec=\"method.size\"]'),t:docsGet().find(d=>d.id===docCurrentId()).title})")
    ok('Chapter 3: Method' in r['h1'] and r['sec'] and 'standard' in r['t'],'outline goes into a new document with section ids on the headings')
    J("LS.set('appu_lang','hi')")
    ok('अध्याय' in J("bpOutlineHTML(studyGet())") and 'विधि' in J("bpOutlineHTML(studyGet())"),'outline in Hindi when the app is in Hindi')
    real=[e for e in errors if 'favicon' not in e[1]]
    ok(not real,'no page errors %s'%real[:3])
    b.close()
print('\n%d failures'%len(fails) if fails else '\nALL PASS')
sys.exit(1 if fails else 0)
