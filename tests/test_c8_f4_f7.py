"""C8 synopsis and protocol as separate documents, F4 submission, F7 closure."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
S='/tmp/claude-0/-home-claude/d540b351-a2df-5fa6-9a88-226a4c6e6a4f/scratchpad/'
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Synopsis study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("setEditorHTML('<p>My main paper text</p>');docSaveBody(getEditorHTML())")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety in first-year students'};o.gap={text:'No study of first-year students in Rajasthan towns.'};o.design={type:'correlational',pop:'First-year students in two colleges in Jaipur',sampling:'convenience',n:'85',ss:{basis:'fixed',why:'All first-year students in two sections, agreed with the supervisor.'},vars:[{name:'Sleep hours',role:'predictor',type:'score',scale:'own'},{name:'Exam anxiety',role:'outcome',type:'score',scale:'GAD7'}],hyp:'H1: Fewer sleep hours go with higher exam anxiety.'};o.write={A2:{text:'Exam anxiety is common (Sharma, 2021).'}};studySet(o)")
    J("subOpen('design','C8');c8Front('student','Asha Verma');c8Front('sup','Dr. Meena Sharma, Professor');c8Front('degree','Ph.D. in Psychology');c8Front('univ','Demo University, Jaipur')")
    n0=J("docsStudy().length")
    J("synBuild()"); pg.wait_for_timeout(300)
    ok(J("docsStudy().length")==n0+1,'synopsis made as a new document in the same study')
    html=J("getEditorHTML()")
    ok('Asha Verma' in html and 'Dr. Meena Sharma' in html and 'Ph.D. in Psychology' in html,'front page filled')
    for sec in ['1. Introduction','2. Need and rationale','3. Review of literature','5. Hypotheses','6.2 Population','6.3 Variables and tools','7. Ethical considerations','8. Tentative chapterisation','References']:
        ok(sec in html,'synopsis has '+sec)
    ok('Fewer sleep hours go with higher exam anxiety' in html and 'GAD-7' in html,'hypothesis and tool carried over')
    ok('All first-year students in two sections' in html,'sample-size basis carried over')
    ok(J("subState('C8').s")=='dn','C8 done after the synopsis')
    ok('My main paper text' in J("docsStudy().find(d=>!/^Synopsis/.test(d.title)).body"),'main paper untouched')
    pg.screenshot(path=S+'synopsis.png')
    # protocol goes to its own document too
    J("document.getElementById('protoDlg').showModal();protoLoad();document.getElementById('protoBg').value='Background text';protoGenerate()"); pg.wait_for_timeout(300)
    ok(J("docsStudy().some(d=>/^Protocol/.test(d.title))") and J("docsStudy().length")==n0+2,'protocol made as its own document')
    ok('Ethics review and consent' in J("getEditorHTML()"),'protocol has an ethics section')
    # F4
    J("subOpen('review','F4')"); pg.wait_for_timeout(200)
    ok(J("f4Ok(studyGet())")==False,'F4 not done at start')
    for k in ['decl','cert','plag','eth','forms']: J("f4Tick('thesis','%s',true)"%k)
    ok(J("f4Ok(studyGet())")==False,'checklist alone is not enough')
    J("logAdd('submit');logCell('submit',0,'to','Demo University');logCell('submit',0,'st','Submitted')")
    ok(J("subState('F4').s")=='dn','F4 done with thesis checklist and a submission')
    ok(J("document.querySelectorAll('#subMain .log-tbl').length")==2,'submission and reviewer tables shown')
    # F7
    J("subOpen('review','F7')"); pg.wait_for_timeout(200)
    J("f7Set('keep','5 years after the award');f7Set('src','consent');f7Set('where','Encrypted drive in the department')")
    ok(J("f7Ok(studyGet())")==False,'closure needs the committee report date')
    J("f7Set('closed','2027-06-30')")
    ok(J("subState('F7').s")=='dn','F7 done with retention, source, storage and closure report')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
