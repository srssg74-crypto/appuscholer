"""Writing pieces inside the steps: A2, B5, B7, C5, D6, E8."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='Writing study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Does sleep relate to exam anxiety in first-year students?'};o.design={type:'correlational',pop:'first-year students',vars:[{name:'Sleep hours',role:'predictor',type:'score',scale:'own'},{name:'Exam anxiety',role:'outcome',type:'score',scale:'GAD7'}],hyp:'H1: Fewer sleep hours go with higher exam anxiety.\\nH2: The link is stronger in hostel students.'};studySet(o)")
    # A2
    J("subOpen('idea','A2')"); pg.wait_for_timeout(200)
    ok('no problem statement yet' in J("document.getElementById('subMain').innerText"),'A2 warns: question without problem')
    J("wPatch('A2','text','Exam anxiety is common among first-year students in India. It is linked with poorer sleep in several studies.')")
    ok(J("wProblemOk(studyGet())")==False,'short text without citations does not complete A2')
    J("wPatch('A2','text','Exam anxiety is common among first-year students in Indian colleges, and around one in four report it at a level that affects their work (Sharma, 2021). Sleep problems rise in the weeks before examinations (Rao & Iyer, 2019). Most studies come from medical students in large cities; little is known about first-year arts, science and commerce students in smaller towns of Rajasthan, where hostel life begins for many. This study asks whether shorter sleep goes with higher exam anxiety in that group.')")
    ok(J("wCiteCount(wGet().A2.text)")==2 and J("subState('A2').s")=='dn','A2 done with two citations and enough text')
    # B5 from matrix themes
    J("logSaveRows('matrix',[{paper:'Sharma (2021)',finding:'Anxiety high',theme:'Prevalence'},{paper:'Rao (2019)',finding:'Sleep falls before exams',theme:'Sleep and exams'},{paper:'Gupta (2020)',finding:'Prevalence 28%',theme:'Prevalence'}])")
    J("subOpen('lit','B5')"); pg.wait_for_timeout(200)
    txt=J("document.getElementById('subMain').innerText")
    ok('Prevalence' in txt and 'Sleep and exams' in txt,'theme map built from the matrix')
    ok(J("wThemesOk(studyGet())")==False,'themes need notes and two papers')
    J("wB5Note('Prevalence','Both find one in four affected; samples are medical students in cities.');wB5Note('Sleep and exams','Only one study; it used self-reported sleep diaries over two weeks.');wB5Note('one:Sleep and exams',true)")
    ok(J("wThemesOk(studyGet())")==True and J("subState('B5').s")=='dn','B5 done with notes, one-study theme declared')
    # B7
    J("subOpen('lit','B7');wPatch('B7','theory','Transactional model of stress');wPatch('B7','cite','Lazarus & Folkman, 1984');wB7Con(0,'name','Sleep loss');wB7Con(0,'v','Sleep hours');wB7Con(1,'name','Appraised threat');wB7Con(1,'v','Exam anxiety')")
    ok(J("wFrameOk(studyGet())")==True and J("subState('B7').s")=='dn','B7 done with theory and linked constructs')
    ok('<svg' in J("wFrameSVG(studyGet())") and J("document.querySelectorAll('#subMain svg').length")>=1,'framework diagram drawn')
    pg.screenshot(path=S+'write-b7.png')
    # C5
    J("subOpen('design','C5');wPatch('C5','mode','pub');wRedraw()")
    ok(J("wTransOk(studyGet())")==False,'published version needs its details')
    J("wPatch('C5','scale','RSES, 10 items');wPatch('C5','src','Aachal, Kumar & Bahurupi (2024)');wPatch('C5','sample','143 nursing students');wPatch('C5','lic','CC BY-NC 4.0')")
    ok(J("subState('C5').s")=='dn','C5 done with a published Hindi version recorded')
    J("wPatch('C5','mode','own')")
    ok(J("wTransOk(studyGet())")==False,'own translation needs all seven steps')
    # D6
    J("subOpen('collect','D6');wInterpFromHyp()")
    ok(J("logRows(studyGet(),'interp').length")==2,'two rows made from hypotheses')
    J("logCell('interp',0,'res','r(118) = -.31, p < .001');logCell('interp',0,'mean','Shorter sleep causes higher exam anxiety');logCell('interp',0,'lim','Cross-sectional: no direction');logCell('interp',1,'res','Difference in r not significant');logCell('interp',1,'mean','No clear difference between hostel and day students');logCell('interp',1,'lim','Small hostel group')")
    ok(J("wCausalFlags(studyGet())")==[1] and J("subState('D6').s")!='dn','causal wording flagged in a correlational design')
    J("logCell('interp',0,'mean','Shorter sleep goes with higher exam anxiety')")
    ok(J("subState('D6').s")=='dn','D6 done once the wording matches the design')
    # E8
    ok(J("subState('E8').s")=='ns','E8 not done before the statement is inserted')
    J("const o=studyGet();o.write.aiu=Date.now();studySet(o)")
    ok(J("subState('E8').s")=='dn','E8 done after the statement is inserted')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
# framework picture goes into the document as a PNG image
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("const o=studyGet();o.design={type:'correlational',vars:[{name:'Sleep hours',role:'predictor'},{name:'Exam anxiety',role:'outcome'}]};o.write={B7:{theory:'T',cite:'C, 2000',cons:[{name:'Sleep loss',v:'Sleep hours'},{name:'Threat',v:'Exam anxiety'}]}};studySet(o)")
    J("wFrameInsert()"); pg.wait_for_timeout(800)
    src=J("(document.querySelector('#editor figure img')||{}).src||''")
    ok(src.startswith('data:image/png') and len(src)>2000,'framework inserted as a PNG image in the document')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors on insert')
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS (with image check)')
