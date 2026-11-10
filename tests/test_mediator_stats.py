"""Mediator and moderator roles drive the suggested test and the column picks (build 2026.11.10f)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
V=lambda n,r,t='score': {'name':n,'role':r,'type':t}
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='MS';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    def setv(vs,ty='correlational'): J("(()=>{const o=studyGet();o.design=o.design||{};o.design.type='%s';o.design.vars=%s;studySet(o)})()"%(ty,json.dumps(vs)))
    sug=lambda: J("(()=>{const s=studySuggestTest();return s?{k:s.k,why:s.why}:null})()")
    setv([V('Stress','predictor'),V('Anxiety','outcome')]); ok(sug()['k']=='pearson','no mediator or moderator: pearson as before')
    setv([V('Stress','predictor'),V('Anxiety','outcome'),V('Rumination','mediator')]); s=sug(); ok(s['k']=='mediate' and 'Rumination' in s['why'],'a mediator: mediation')
    setv([V('Stress','predictor'),V('Anxiety','outcome'),V('Support','moderator')]); s=sug(); ok(s['k']=='moderate' and 'Support' in s['why'],'a moderator: moderation')
    setv([V('Stress','predictor'),V('Anxiety','outcome'),V('Rumination','mediator'),V('Support','moderator')]); s=sug(); ok(s['k']=='mediate' and 'separately' in s['why'],'both: mediation first, moderation said to be tested separately')
    setv([V('Stress','predictor'),V('Relapse','outcome','yesno'),V('Rumination','mediator')]); ok(sug()['k']=='logistic','yes/no outcome: falls back to logistic')
    setv([V('Stress','predictor'),V('Anxiety','outcome'),V('Rumination','mediator','category')]); ok(sug()['k']!='mediate','a category mediator is not offered to the mediation test')
    setv([V('Stress','predictor'),V('Anxiety','outcome'),V('Rumination','mediator')],'review'); ok(sug()['k']!='mediate','a review never gets it')
    # column picks
    setv([V('Stress','predictor'),V('Anxiety','outcome'),V('Rumination','mediator'),V('Support','moderator')])
    J("showTool('stats')"); pg.wait_for_timeout(300)
    J("document.getElementById('statsPaste').value='anxiety,support,stress,rumination\\n10,3,4,5\\n12,4,5,6\\n9,2,3,4\\n14,5,6,8\\n11,3,5,6\\n13,4,6,7';statsParse()"); pg.wait_for_timeout(400)
    J("studyUseTest()"); pg.wait_for_timeout(400)
    pick=J("(()=>{const o={};document.querySelectorAll('#statsFields .fld').forEach(f=>{const l=(f.querySelector('label')||{}).innerText||'',se=f.querySelector('select');if(se)o[l]=se.options[se.selectedIndex]?se.options[se.selectedIndex].text:''});return o})()")
    print('   ',pick)
    vals={k.lower():v.lower() for k,v in pick.items()}
    def col(frag): return next((v for k,v in vals.items() if frag in k),'')
    ok(J("document.getElementById('statsTest').value")=='mediate','Stats Lab test set to mediation')
    ok('stress' in col('predictor') and 'rumination' in col('mediator') and 'anxiety' in col('outcome'),'columns picked: X stress, M rumination, Y anxiety')
    setv([V('Stress','predictor'),V('Anxiety','outcome'),V('Support','moderator')]); J("studyUseTest()"); pg.wait_for_timeout(400)
    pick=J("(()=>{const o={};document.querySelectorAll('#statsFields .fld').forEach(f=>{const l=(f.querySelector('label')||{}).innerText||'',se=f.querySelector('select');if(se)o[l]=se.options[se.selectedIndex]?se.options[se.selectedIndex].text:''});return o})()")
    vals={k.lower():v.lower() for k,v in pick.items()}
    ok(J("document.getElementById('statsTest').value")=='moderate' and 'support' in col('moderator') and 'stress' in col('predictor') and 'anxiety' in col('outcome'),'moderation: W support, X stress, Y anxiety')
    # hint box shows the button
    J("studyStatsHint()"); h=J("(document.getElementById('studyStatsHint')||{innerText:''}).innerText")
    ok('moderator' in h.lower() or 'moderation' in h.lower(),'the hint box explains it')
    # Hindi
    J("LS.set('appu_lang','hi');applyLang()"); pg.wait_for_timeout(300); ok('moderator' in J("studySuggestTest().why") and 'बताया' in J("studySuggestTest().why"),'Hindi reason')
    ok(not [e for e in errors if 'Failed to load resource' not in str(e)],'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
