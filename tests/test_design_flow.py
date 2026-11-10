"""Design flow diagram in C1 and the change note (build 2026.11.10g)."""
import sys, os, json
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
    J("openSaveAsProject();document.getElementById('sapName').value='DF';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    vars=[{'name':'Sleep hours','role':'group','type':'category','levels':'Hostel, Day scholar'},{'name':'Exam anxiety','role':'outcome','type':'score'}]
    def setd(ty,extra=None):
        d={'type':ty,'pop':'First-year BA students in Jaipur','n':'80','sampling':'Convenience sample','vars':vars}
        J("(()=>{const o=studyGet();const f=o.design&&o.design.flowPrev;o.design=%s;if(f)o.design.flowPrev=f;studySet(o)})()"%json.dumps(d))
    def c1():
        J("subOpen('design','C1')"); pg.wait_for_timeout(450)
        return J("document.getElementById('subMain').innerText")
    def svgtxt(): return J("(()=>{const s=document.querySelector('#subMain svg');return s?s.textContent:''})()")
    setd('two-group'); t=c1(); s=svgtxt()
    ok('at a glance' in t,'C1 shows the design picture')
    ok('Hostel' in s and 'Day scholar' in s and 'n = 80' in s and 'Exam anxiety' in s,'boxes carry the student\'s own words')
    ok('Welch' in s or 'Analysis' in s,'analysis box present')
    chk=J("(()=>{const d=dgDesign(studyGet());return JSON.stringify(dgCheck(d).map(x=>[x.ok,x.t.slice(0,50)]))})()"); print(chk)
    ok('false' not in chk,'figure check passes for two-group')
    for ty in ['survey','multi-group','experiment','pre-post','longitudinal','cohort','case-control','qualitative','mixed']:
        setd(ty); r=J("(()=>{const d=dgDesign(studyGet());return d?JSON.stringify(dgCheck(d).filter(x=>!x.ok).map(x=>x.t.slice(0,70))):'null'})()")
        ok(r=='[]','check clean for '+ty+(' '+r if r!='[]' else ''))
    setd('review'); ok(J("dgDesign(studyGet())")is None,'review gives no design picture')
    # change a design through the dialog save
    setd('pre-post'); J("spOpen()"); pg.wait_for_timeout(300)
    J("document.getElementById('spType').value='two-group';spSave()"); pg.wait_for_timeout(400)
    t=c1()
    ok('You changed the design' in t,'change note appears')
    ok('Measure before' in t and 'Intervention or event' in t,'gone boxes listed')
    ok('Compare on' in t or 'Hostel' in t,'new boxes listed')
    ok('C1' in t.split('read differently')[1][:80] if 'read differently' in t else False,'steps with changed notes named')
    J("dgDesignDismiss()"); pg.wait_for_timeout(300)
    ok('You changed the design' not in c1(),'note clears')
    J("LS.set('appu_lang','hi');applyLang()"); pg.wait_for_timeout(300)
    ok('एक नज़र में' in c1(),'Hindi heading')
    J("LS.set('appu_lang','en');applyLang()"); setd('survey'); J("spOpen()"); pg.wait_for_timeout(500)
    ok('Exam anxiety' in J("document.getElementById('spPrev').innerText+document.getElementById('spPrev').textContent"),'dialog preview shows the saved plan')
    J("(()=>{const s=document.getElementById('spType');s.value='experiment';s.dispatchEvent(new Event('change',{bubbles:true}))})()"); pg.wait_for_timeout(700)
    ok('Random allocation' in J("document.getElementById('spPrev').textContent"),'preview follows the dropdown live')
    J("(()=>{const s=document.getElementById('spN');s.value='123';s.dispatchEvent(new Event('input',{bubbles:true}))})()"); pg.wait_for_timeout(700)
    ok('n = 123' in J("document.getElementById('spPrev').textContent"),'preview follows sample size')
    for ty in ['survey','correlational','two-group','multi-group','pre-post','experiment','longitudinal','cohort','case-control','qualitative','mixed']:
        h=J("dgClaimHTML('%s')"%ty); ok('You can say' in h and 'You cannot say' in h and 'Watch for' in h,'claim card for '+ty)
    ok(J("dgClaimHTML('review')")=='','no claim card for a review')
    setd('pre-post'); t=c1(); ok('regression to the mean' in t and 'control group' in t,'pre-post card in C1')
    J("LS.set('appu_lang','hi');applyLang()"); setd('experiment'); ok('आप कह सकते हैं' in c1(),'Hindi claim card')
    J("LS.set('appu_lang','en');applyLang()"); setd('experiment'); J("spOpen()"); pg.wait_for_timeout(500)
    ok('You cannot say' in J("document.getElementById('spPrev').textContent"),'claim card in the dialog preview')
    ok(not [e for e in errors if 'Failed to load resource' not in str(e)],'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
