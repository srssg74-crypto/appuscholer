"""Pre-post and case-control get their own notes in C1, D2 and D3 (build 2026.11.10d)."""
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
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='CF';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    def page(stage,id):
        J("subOpen('%s','%s')"%(stage,id)); pg.wait_for_timeout(450)
        return J("document.getElementById('subMain')?document.getElementById('subMain').innerText:document.body.innerText")
    def setd(k): J("(()=>{const o=studyGet();o.design=o.design||{};o.design.type='%s';studySet(o)})()"%k)
    setd('pre-post')
    ok('gap between the two measurements' in page('design','C1'),'pre-post C1: gap between measurements')
    ok('measured at both times' in page('collect','D2'),'pre-post D2: log of who was measured both times')
    ok('who was lost between the two measurements' in page('collect','D3'),'pre-post D3: attrition record')
    ok('harm and withdrawal' in page('design','C9'),'pre-post C9 keeps the experiment duty: harm and withdrawal plan')
    f2=page('review','F2'); ok('TREND (22 items' in f2 and 'CONSORT 2025 instead' in f2,'pre-post F2: TREND named, CONSORT only if randomised')
    d6=page('collect','D6'); ok('regression to the mean' in d6 and 'maturation' in d6 and 'history' in d6 and 'unmeasured confounders' in d6,'pre-post D6: the threats list')
    setd('case-control')
    c1=page('design','C1'); ok('cases and controls were identified' in c1 and 'follow people' not in c1,'case-control C1: no follow-up wording')
    ok('found and matched' in page('collect','D2'),'case-control D2: how cases and controls were found')
    d3=page('collect','D3'); ok('no attrition record' in d3 and 'Nobody is followed' in d3,'case-control D3: no attrition record')
    setd('experiment'); ok('regression to the mean' not in page('collect','D6'),'experiment D6 has no pre-post threats list')
    setd('cohort')
    ok('how long you follow' in page('design','C1') and 'attrition record' in page('collect','D3'),'cohort unchanged')
    setd('longitudinal'); ok('attrition record' in page('collect','D3'),'longitudinal unchanged')
    setd('experiment'); ok('allocated to groups' in page('design','C1'),'experiment unchanged')
    setd('pre-post'); J("LS.set('appu_lang','hi');applyLang()"); pg.wait_for_timeout(300)
    ok('दोनों माप के बीच' in page('design','C1'),'Hindi pre-post C1')
    ok(not [e for e in errors if 'Failed to load resource' not in str(e)],'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
