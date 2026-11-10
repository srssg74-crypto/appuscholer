"""Conceptual framework figure from the study record, and the figure check (build 2026.11.10b)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.on('requestfailed',lambda r:print('   REQFAIL',r.url[:100]))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='FW';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    ok(J("dgFw(studyGet())")==None,'no variables: no figure')
    J("(()=>{const o=studyGet();o.design=o.design||{};o.design.type='survey';o.design.vars=[{name:'Hours of sleep',role:'predictor',type:'score'},{name:'Residence (hostel or day)',role:'group',type:'category'},{name:'Exam anxiety',role:'outcome',type:'score'}];studySet(o)})()")
    d=J("(()=>{const d=dgFw(studyGet());return {svg:d.svg,n:d.allowed.length}})()")
    ok('Hours of sleep' in d['svg'] and 'Residence (hostel' in d['svg'] and 'Exam anxiety' in d['svg'],'names from the record are in the figure')
    ok('Covariates' not in d['svg'],'no covariate box when none exist')
    r=J("dgCheck(dgFw(studyGet()))")
    for x in r: print('   ',('ok ' if x['ok'] else 'NO ')+x['t'])
    ok(len(r)==6 and all(x['ok'] for x in r),'figure check passes all six rules')
    J("(()=>{const o=studyGet();o.design.vars.push({name:'Age',role:'covariate',type:'score'},{name:'Year of study',role:'covariate',type:'score'});studySet(o)})()")
    ok('Covariates' in J("dgFw(studyGet()).svg") and 'Age, Year of study' in J("dgFw(studyGet()).svg"),'covariate box lists covariates')
    r=J("dgCheck(dgFw(studyGet()))"); ok(all(x['ok'] for x in r),'check still passes with covariates')
    # many variables and a long name
    J("(()=>{const o=studyGet();o.design.vars=[1,2,3,4,5].map(i=>({name:'Predictor number '+i+' with a rather long descriptive name',role:'predictor',type:'score'})).concat([{name:'Outcome',role:'outcome',type:'score'}]);studySet(o)})()")
    r=J("dgCheck(dgFw(studyGet()))"); ok(all(x['ok'] for x in r),'five long predictors still pass')
    # mediator and moderator
    J("(()=>{const o=studyGet();o.design.vars=[{name:'Hours of sleep',role:'predictor',type:'score'},{name:'Exam anxiety',role:'outcome',type:'score'},{name:'Rumination',role:'mediator',type:'score'},{name:'Social support',role:'moderator',type:'score'},{name:'Age',role:'covariate',type:'score'}];studySet(o)})()")
    sv=J("dgFw(studyGet()).svg")
    ok('Rumination' in sv and 'Mediators' in sv and 'Social support' in sv and 'Moderators' in sv and 'Covariates' in sv,'mediator, moderator and covariate all drawn with headings')
    r=J("dgCheck(dgFw(studyGet()))")
    for x in r: print('   ',('ok ' if x['ok'] else 'NO ')+x['t'])
    ok(len(r)==6 and all(x['ok'] for x in r),'check passes with mediator, moderator and covariate')
    J("(()=>{const o=studyGet();o.design.vars=[{name:'Stress',role:'predictor',type:'score'},{name:'Anxiety',role:'outcome',type:'score'},{name:'Rumination about exams',role:'mediator',type:'score'},{name:'Sleep quality',role:'mediator',type:'score'},{name:'Social support',role:'moderator',type:'score'},{name:'Coping style',role:'moderator',type:'score'},{name:'Gender',role:'covariate',type:'category'}];studySet(o)})()")
    r=J("dgCheck(dgFw(studyGet()))"); ok(all(x['ok'] for x in r),'two mediators and two moderators still pass')
    ok(J("studyRoleLabel('mediator')")=='Mediator (carries the effect)' and J("studyRoleLabel('moderator')")=='Moderator (changes the effect)','role labels')
    # roles do not disturb other parts: test suggestion and protocol text
    J("(()=>{const o=studyGet();o.design.vars=[{name:'Stress',role:'predictor',type:'score'},{name:'Anxiety',role:'outcome',type:'score'},{name:'Rumination',role:'mediator',type:'score'}];studySet(o)})()")
    base=[{'name':'Stress','role':'predictor','type':'score'},{'name':'Anxiety','role':'outcome','type':'score'}]
    import json
    J("(()=>{const o=studyGet();o.design.vars=%s;studySet(o)})()"%json.dumps(base)); s1=J("JSON.stringify(studySuggestTest())")
    J("(()=>{const o=studyGet();o.design.vars=%s;studySet(o)})()"%json.dumps(base+[{'name':'Rumination','role':'mediator','type':'score'},{'name':'Support','role':'moderator','type':'score'}])); s2=J("JSON.stringify(studySuggestTest())")
    ok('pearson' in s1 and 'mediate' in s2,'a mediator now moves the suggestion from Pearson to mediation (step 2) (%s)'%s2[:50])
    # the check catches problems
    bad=J("dgCheck({w:620,h:100,svg:'<svg viewBox=\"0 0 1400 100\"><rect stroke=\"#000\" x=\"0\" y=\"0\" width=\"60\" height=\"30\"/><rect stroke=\"#000\" x=\"40\" y=\"10\" width=\"60\" height=\"30\"/><text x=\"30\" y=\"20\" text-anchor=\"middle\" font-size=\"9\">A very long label that cannot fit</text><text x=\"5\" y=\"90\" font-size=\"12\">Figure 1. Title</text></svg>'})")
    fl=[x['t'] for x in bad if not x['ok']]
    ok(len(fl)>=5,'a bad figure fails at least five rules (%d: %s)'%(len(fl),'; '.join(t[:28] for t in fl)))
    inv=J("dgCheck({w:620,h:60,allowed:['Anxiety'],svg:'<svg viewBox=\"0 0 620 60\"><rect x=\"0\" y=\"0\" width=\"620\" height=\"60\"/><text x=\"300\" y=\"30\" text-anchor=\"middle\" font-size=\"12.5\">Invented mediator</text></svg>'})")
    ok(any((not x['ok']) and 'not from your study record' in x['t'] for x in inv),'a label that is not in the record is caught')
    # screen
    J("(()=>{const o=studyGet();o.design.vars=[{name:'Hours of sleep',role:'predictor',type:'score'},{name:'Exam anxiety',role:'outcome',type:'score'}];studySet(o)})()")
    J("subOpen('design','C4')"); pg.wait_for_timeout(500)
    t=J("document.getElementById('subMain').innerText")
    ok('Conceptual framework figure' in t and 'Figure check' in t and 'Put it in my document' in t,'C4 shows the figure, its check and the insert button')
    # existing figures under the check
    for nm,js in [('Gantt',"(()=>{const o=studyGet();o.write=o.write||{};o.write.C8={plan:{idea:{a:1,d:2},lit:{a:3,d:3},design:{a:6,d:2}}};studySet(o);return dgGantt(studyGet())})()")]:
        r=J("dgCheck(%s)"%js.rstrip(';')) if True else []
        print('   existing',nm,[('ok' if x['ok'] else 'NO ')+x['t'][:60] for x in r])
    J("LS.set('appu_lang','hi');applyLang()"); pg.wait_for_timeout(300)
    J("subOpen('design','C4')"); pg.wait_for_timeout(500)
    ok('Figure की जाँच' in J("document.getElementById('subMain').innerText"),'Hindi check heading')
    errs=[e for e in errors if 'Failed to load resource' not in str(e)]; ok(not errs,'no page errors (the OpenAlex feed request cannot reach the network in this sandbox) %s'%errs)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
