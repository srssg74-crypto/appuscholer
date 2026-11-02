"""Present the slides inside the app, print them as PDF, and a journal club deck from one or more papers (build 2026.11.02l)."""
import sys, os
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
    J("window.confirm=()=>true;LS.set('appu_me',JSON.stringify({name:'Asha Verma',pos:'',role:'student',course:'pg'}))")
    J("openNewProjectDirect();document.getElementById('sapName').value='JC';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety in students'};studySet(o)")
    for a,y,t in [('Gupta, S.; Rao, M.','2020','Sleep duration and anxiety among medical students'),('Kumar, A.','2019','Sleep, stress and marks in college students')]:
        J("citClearForm();document.getElementById('citAuthor').value='%s';document.getElementById('citYear').value='%s';document.getElementById('citTitle').value='%s';document.getElementById('citSource').value='Indian J Psychol';citAdd()"%(a,y,t))
    J("logFromLibrary('matrix');logFromLibrary('quality')")
    J("logCell('matrix',0,'design','Cross-sectional survey');logCell('matrix',0,'sample','420 medical students');logCell('matrix',0,'finding','Shorter sleep went with more anxiety');logCell('matrix',0,'stance','Supports');logCell('matrix',0,'theme','Sleep and anxiety');logCell('quality',0,'str','Validated scale');logCell('quality',0,'weak','One city');logCell('quality',0,'tool','AXIS');logCell('quality',0,'judge','Moderate')")
    J("showTool('slides');jcPick()"); pg.wait_for_timeout(200)
    ok(J("document.querySelectorAll('.jcChk').length")==2,'the picker lists the library papers')
    J("document.querySelectorAll('.jcChk').forEach(c=>c.checked=true);jcBuild()"); pg.wait_for_timeout(300)
    m=J("_pptxSlideModel.map(x=>x.title)")
    print(m)
    ok(m[0].startswith('Journal club: 2 studies'),'cover names the journal club')
    ok(J("!!_pptxSlideModel[1].table&&_pptxSlideModel[1].table.length===3"),'two papers get an at-a-glance comparison table')
    ok(any('How far to trust' in x and 'Moderate' in x for x in m),'the appraisal slide carries the student verdict')
    ok('Questions for the group' in m and 'References' in m,'discussion questions and references are there')
    ok('yellow gaps' in J("document.getElementById('pptxPreview').innerText"),'notes not yet written show as gaps to fill')
    # present inside the app
    J("ssOpen()"); pg.wait_for_timeout(200)
    ok(J("getComputedStyle(document.getElementById('ssDlg')).display")=='flex' and J("document.getElementById('ssNum').textContent").startswith('1 /'),'the slideshow opens on slide 1')
    pg.keyboard.press('ArrowRight'); pg.keyboard.press('ArrowRight')
    ok(J("document.getElementById('ssNum').textContent").startswith('3 /'),'arrow keys move between slides')
    ok('ss-table' in J("(SS.i=1,ssShow(1),document.getElementById('ssSlide').innerHTML)"),'the table is drawn on screen')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    ok(J("getComputedStyle(document.getElementById('ssDlg')).display")=='none','Esc closes it')
    J("pptxDownload()")
    ok(not [e for e in errors if e[0]=='pageerror'],'PowerPoint export runs without errors %s'%errors[:2])
    b.close()
print('FAILED' if fails else 'ALL PASS', len(fails))
