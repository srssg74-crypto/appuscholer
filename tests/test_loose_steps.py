"""Done rules with 'still needed' lists for A1, A3, A4, C1, C2, C6, C10, E2–E7, F5."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
W=lambda n:' '.join(['word']*n)
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Loose';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    for s in ['A1','A3','A4','C1','C2','C6','C10','E2','E3','E4','E5','E6','E7','F5']:
        ok(J("subState('%s').s"%s)!='dn','%s not done on an empty study'%s)
    J("subOpen('idea','A1')"); t=J("document.getElementById('subMain').innerText")
    ok('Still needed' in t and 'other topics' in t,'A1 page lists what is missing')
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety in college students'};studySet(o);lsSet('A1','alt','Social media and loneliness; dropped because school access was uncertain.')")
    ok(J("subState('A1').s")=='dn','A1 done with topic and alternatives')
    J("lsSet('A3','aim','To find whether sleep hours relate to exam anxiety.');lsSet('A3','q','Do fewer sleep hours go with more anxiety?')")
    ok(J("subState('A3').s")!='dn','A3 needs hypotheses or the exploratory tick')
    J("lsSet('A3','noHyp',true)"); ok(J("subState('A3').s")=='dn','A3 done with aim, question and exploratory tick')
    J("const o=studyGet();o.write.A4={r:{acc:'ok',time:'ok',skill:'risk',sup:'ok',cost:'ok',equip:'ok',eth:'ok'},dec:'revise',why:'Need a statistics workshop first.'};studySet(o)")
    ok(any('revise' in x for x in J("lsIssues('A4',studyGet())")),'A4 revise is not done')
    J("lsSet('A4','dec','go')"); ok(J("subState('A4').s")=='dn','A4 done with all rated and go')
    J("const o=studyGet();o.design={type:'correlational',pop:'First-year students in Jaipur',sampling:'convenience'};studySet(o)")
    ok(J("subState('C1').s")=='dn','C1 done with a design')
    ok(J("subState('C2').s")!='dn','C2 needs inclusion, exclusion, recruitment')
    J("lsSet('C2','incl','First-year, 17–25, enrolled');lsSet('C2','excl','Already in counselling');lsSet('C2','rec','Notice boards and class visits')")
    ok(J("subState('C2').s")=='dn','C2 done')
    J("designSet('ec',{title:'Sleep',pi:'Asha',what:'A survey',risks:'Mild discomfort',contact:'Dr X, 0141-2700000'})")
    ok(J("subState('C10').s")!='dn','C10 needs the consent form made')
    J("const s=designGet('ec');s.consentAt=Date.now();designSet('ec',s)"); ok(J("subState('C10').s")=='dn','C10 done once the consent form is made')
    J("const o=studyGet();o.ethics=Object.assign(o.ethics||{},{risk:{minor:true}});studySet(o)")
    ok(J("subState('C10').s")!='dn','under-18 needs an assent form'); J("lsSet('C10','assent',true)"); ok(J("subState('C10').s")=='dn','C10 done with assent tick')
    # writing
    body='<h1>Introduction</h1><p>'+W(210)+' The aim of this study is to test it.</p><h1>Review of literature</h1><p>'+W(420)+' (Rao, 2020) (Sen, 2019) (Iyer, 2018) (Das, 2021) (Roy, 2017)</p><h1>Methods</h1><p>'+W(210)+' Ethics approval and consent were obtained. The analysis used Pearson r.</p><h1>Results</h1><p>'+W(70)+' r(48) = .41, p = .003, N = 50.</p><h1>Discussion</h1><p>'+W(210)+' One limitation is the sample.</p>'
    J("setEditorHTML(%s);docSaveBody(getEditorHTML())"%json.dumps(body))
    for s in ['E2','E3','E4','E6']: ok(J("subState('%s').s"%s)=='dn','%s done from the document headings'%s)
    J("const o=studyGet();o.logs=o.logs||{};o.logs.aplan=[{h:'H1: Sleep and anxiety',kind:'Main',test:'Pearson r'}];o.results=[{h:'H1: Sleep and anxiety',kind:'main',apa:'There was a moderate negative correlation, r(48) = -.41, p = .003.'}];studySet(o)")
    ok(any('not in the Results text' in x for x in J("lsIssues('E5',studyGet())")),'E5 catches a result not reported as it was run (sign changed)')
    J("setEditorHTML(getEditorHTML().replace('r(48) = .41','r(48) = -.41'));docSaveBody(getEditorHTML())")
    ok(J("subState('E5').s")=='dn','E5 done when the run result is in the Results')
    J("setEditorHTML('<h1>Abstract</h1><p>'+%s+' We found r(48) = -.41, p = .004, N = 50.</p><p>Keywords: sleep, anxiety</p>'+getEditorHTML());docSaveBody(getEditorHTML())"%json.dumps(W(120)))
    ok(any('p=.004' in x for x in J("lsIssues('E7',studyGet())")),'E7 catches an abstract number that is not in the Results')
    J("setEditorHTML(getEditorHTML().replace('p = .004','p = .003'));docSaveBody(getEditorHTML())")
    ok(J("subState('E7').s")=='dn','E7 done when the abstract matches')
    J("localStorage.setItem(pkey('appu_viva'),JSON.stringify([1,2,3,4,5].map(i=>({q:'q'+i,a:'a'}))))")
    ok(J("subState('F5').s")=='dn','F5 done after five practice answers')
    J("subOpen('writing','E3')"); ok('words' in J("document.getElementById('subMain').innerText"),'writing step shows where it found the section')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
