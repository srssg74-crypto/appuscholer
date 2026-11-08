"""B1 steps-per-type panel (build 2026.11.08p)."""
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
    J("window.confirm=()=>true;window.callAI=async function(){return ''}")
    J("openSaveAsProject();document.getElementById('sapName').value='Steps';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("subOpen('lit','B1')")
    H=lambda: J("document.getElementById('subMain').innerHTML")
    ok('What this type asks of you' not in H(),'no panel before a type is chosen')
    for ty in ('narr','scop','sys','meta'):
        J("wPick('B1','type','%s')"%ty); J("subOpen('lit','B1')")
        t=J("Array.from(document.querySelectorAll('#subMain details')).map(d=>d.textContent).join('\\n')")
        ok('B2 · Search plan and log' in t and 'B7 · Framework' in t,'%s: panel lists the steps'%ty)
        if ty=='narr': ok('B3 · Second reviewer' in t and 'Not shown' in t and 'Most theses need it' in t,'narrative: second reviewer not shown, framework required')
        if ty=='sys': ok('Recommended' in t and 'RoB 2' in t and 'date when you close the search' in t,'systematic: kappa recommended, RoB 2, close date')
        if ty=='meta': ok('exported as CSV' in t,'meta: CSV step')
        if ty=='scop': ok('PRISMA-ScR version' in t,'scoping: PRISMA-ScR')
    J("toggleLang()"); J("subOpen('lit','B1')")
    ok('ज़रूरी' in J("Array.from(document.querySelectorAll('#subMain details')).map(d=>d.textContent).join('\\n')") or 'ज़रूरी' in H(),'Hindi labels')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
