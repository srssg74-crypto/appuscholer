"""One table for every paper (build 2026.11.08o)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
AB='Background: Sleep affects learning. Few studies have examined hostel students. Methods: A cross-sectional survey of 412 students (58% women) used the Pittsburgh Sleep Quality Index. Data were analysed with SPSS using regression. Results: Each hour less sleep was linked to lower GPA (r = .32, p < .001). Conclusion: Sleep matters for grades. Limitations include self-report.'
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true;window.__ai=0;window.callAI=async function(){window.__ai++;return ''}")
    J("openSaveAsProject();document.getElementById('sapName').value='Table';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("citSaveLib(%s)"%json.dumps([{"author":"Lee, A.","year":"2019","title":"Sleep and grades","source":"Sleep Health","type":"Journal article","style":"apa","abs":AB},{"author":"Rao, C.","year":"2021","title":"No abstract paper","type":"Journal article","style":"apa"}]))
    J("subOpen('lit','B3')")
    T=lambda: J("document.getElementById('subMain').innerText")
    ok('One table for every paper' in T() and 'Study design and planning' in T(),'table shown with stage names')
    ok(J("b3Cols(studyGet())").__len__()==6,'default six columns')
    J("b3ColToggle('stats')"); ok('stats' in J("b3Cols(studyGet())"),'column switched on')
    J("b3ColToggle('stats')"); ok('stats' not in J("b3Cols(studyGet())"),'and off again')
    ai0=J("window.__ai")
    J("b3FillAbstracts()")
    L=json.loads(J("JSON.stringify(citGetLib())"))
    c=L[0]['cells']
    ok(c['sample']['by']=='rule' and '412' in c['sample']['t'],'sample cell lifted from the abstract, labelled by rules')
    ok('Few studies' in c['gap']['t'] and 'cells' not in L[1],'gap cell filled; paper without abstract left alone')
    ok(J("window.__ai")==ai0,'no AI call')
    J("b3Cell(0,'sample','N = 412, first-year students')")
    L=json.loads(J("JSON.stringify(citGetLib())")); ok(L[0]['cells']['sample']=={'t':'N = 412, first-year students','by':'me'},'typing replaces it and marks it as my words')
    J("b3FillAbstracts()")
    L=json.loads(J("JSON.stringify(citGetLib())")); ok(L[0]['cells']['sample']['by']=='me','filling again never overwrites my words')
    J("b3Cell(0,'dir','less')"); J("b3Cell(0,'why','core paper')")
    L=json.loads(J("JSON.stringify(citGetLib())")); ok(L[0]['dir']=='less' and L[0]['scr']['why']=='core paper','direction and why-line saved')
    J("citScrSet(1,'st','excluded')"); J("subOpen('lit','B3')")
    ok(J("document.getElementById('subMain').innerHTML").count('One line: why it is out')>=1,'exclude shows the reason box')
    ok(json.loads(J("JSON.stringify(citGetLib()[1].scr.st)"))=='excluded','Exclude button sets the library status')
    ok('From the abstract, by rules' in T() or J("document.getElementById('subMain').innerHTML").count('by rules')>0,'rule label shown')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
