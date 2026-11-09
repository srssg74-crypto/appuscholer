"""C1 to F7 say what the chosen design family asks of them (build 2026.11.09d)."""
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
    ok('Choose your study design in C1' in page('design','C3'),'no design chosen: points to C1')
    def setd(k): J("(()=>{const o=studyGet();o.design=o.design||{};o.design.type='%s';studySet(o)})()"%k)
    setd('qualitative')
    t=page('design','C3'); ok('Light' in t and 'saturation' in t,'qualitative: C3 is Light, saturation')
    t=page('collect','D4'); ok('does not appear' in t,'qualitative: D4 not shown')
    t=page('review','F2'); ok('COREQ or SRQR' in t,'qualitative: F2 names COREQ or SRQR')
    setd('experiment')
    t=page('review','F2'); ok('CONSORT 2025' in t,'experiment: CONSORT 2025')
    t=page('design','C9'); ok('harm and withdrawal' in t,'experiment: C9 asks for a harm and withdrawal plan')
    setd('cohort'); t=page('collect','D3'); ok('attrition' in t,'cohort: D3 keeps the attrition record')
    setd('review'); t=page('design','C2'); ok('Already done in your review steps' in t and 'B3' in t,'review: C2 counts as done through B3')
    ok(J("subState('C2').s")=='dn' and J("subState('D4').s")=='dn' and J("subState('C3').s")=='na' and J("subState('D5').s")=='na','review: states are done or not applicable')
    t=page('design','C3'); ok('Not needed for a review' in t,'review: C3 not needed')
    J("subSet('C2',{s:'ip'})"); ok(J("subState('C2').s")=='ip','a state set by hand wins')
    setd('survey'); ok(J("subState('C3').s")!='na','a survey is untouched')
    setd('review')
    t=page('writing','E3'); ok('this chapter is the review' in t.lower() or 'This chapter is the review' in t,'review: E3 is the review')
    setd('mixed'); t=page('review','F2'); ok('GRAMMS' in t,'mixed: GRAMMS')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
