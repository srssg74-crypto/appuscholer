"""C7 plan → Stats Lab result recorded per hypothesis → D4 done → D6 filled → Results and Discussion drafts."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='Chain';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    H1='H1: Hostel students report more exam anxiety than day scholars.'; H2='H2: Sleep hours go with exam anxiety.'
    J("const o=studyGet();o.design={type:'two-group',hyp:%s};studySet(o)"%json.dumps(H1+'\n'+H2))
    J("subOpen('design','C7');c7FromHyp()")
    for i,(t,es) in enumerate([('Welch t-test (two groups)',"Cohen\\'s d / Hedges\\' g"),('Pearson r','r')]):
        J("logCell('aplan',%d,'dv','Exam anxiety');logCell('aplan',%d,'test','%s');logCell('aplan',%d,'es','%s');logCell('aplan',%d,'miss','Complete cases')"%(i,i,t,i,es,i))
    J("document.getElementById('subDlg').close()")
    ok(J("subState('D4').s")=='ns','D4 not done before any result')
    csv='g,s,sl\n'+'\n'.join('H,%d,%d'%(x,y) for x,y in [(30,5),(34,6),(33,5),(36,4),(31,6),(35,5)])+'\n'+'\n'.join('D,%d,%d'%(x,y) for x,y in [(25,7),(27,7),(26,8),(28,6),(24,8),(26,7)])
    def run(test,f):
        J("showTool('stats');document.getElementById('statsPaste').value=%s;statsParse();document.getElementById('statsTest').value='%s';statsFieldsRender()"%(json.dumps(csv),test))
        for k,v in f.items(): J("document.getElementById('sf_%s').value='%s'"%(k,v))
        J("statsRunNow()"); pg.wait_for_timeout(150)
    run('ttestInd',{'dv':1,'iv':0})
    ok(J("!!document.getElementById('resLink')"),'result offers to be recorded against the plan')
    J("document.getElementById('resH').value='0';resCheck();resRecord()")
    ok(J("studyGet().results.length")==1 and J("studyGet().results[0].kind")=='main' and J("studyGet().results[0].build")==J("APP_BUILD"),'H1 recorded as the main analysis, with build and time')
    run('spearman',{'v1':1,'v2':2})
    J("document.getElementById('resH').value='1';resCheck()")
    ok('deviation' in J("document.getElementById('resDevTxt').textContent"),'Spearman instead of planned Pearson flagged as a deviation')
    J("resRecord()")
    ok('Write why' in J("document.getElementById('resMsg').textContent"),'deviation needs a reason')
    J("document.getElementById('resWhy').value='Sleep hours were skewed, so a rank correlation was used.';resRecord()")
    ok(J("studyGet().results.find(r=>r.h.startsWith('H2')).kind")=='dev','deviation recorded with its reason')
    ok(J("subState('D4').s")=='dn','D4 done when every main analysis has a result')
    run('pearson',{'v1':1,'v2':2})
    J("document.getElementById('resH').value='x';resRecord()")
    ok(J("studyGet().results.filter(r=>r.kind==='expl').length")==1,'extra test recorded as exploratory')
    J("subOpen('collect','D4')")
    t=J("document.getElementById('subMain').innerText")
    ok('Changed to' in t and 'exploratory' in t,'D4 shows the plan, the deviation and the exploratory count')
    J("SUB_CUR.id='D6';subRender();wInterpFromHyp();resFillInterp()")
    rows=J("logRows(studyGet(),'interp')")
    ok(len(rows)==2 and all(r.get('res') for r in rows) and 'Deviation from plan' in rows[1]['res'] and rows[0].get('size','').startswith('g ='),'D6 filled from the records, effect size pulled out')
    J("logCell('interp',0,'mean','Hostel students were more anxious before exams.');logCell('interp',0,'lim','Groups were not randomised.');logCell('interp',1,'mean','Fewer sleep hours went with more anxiety.');logCell('interp',1,'lim','One time point only.')")
    J("setEditorHTML('<p>x</p>');resInsert('res')"); pg.wait_for_timeout(200); ed=J("getEditorHTML()")
    ok('<h2>Results</h2>' in ed and H1 in ed and 'was used instead because sleep hours were skewed' in ed and 'Exploratory analyses' in ed,'Results draft: one part per hypothesis, the deviation explained, exploratory part separate')
    J("resInsert('disc')"); pg.wait_for_timeout(200); ed=J("getEditorHTML()")
    ok('<h2>Discussion</h2>' in ed and 'Groups were not randomised.' in ed,'Discussion start from the meanings and limits')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
