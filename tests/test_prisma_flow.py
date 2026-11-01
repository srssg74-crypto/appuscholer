"""PRISMA 2020 flow diagram follows the 2020 template: registers, removals before screening, reports sought and
not retrieved, reports of included studies, other methods; unfilled numbers show as n = ?."""
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
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Prisma';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("subOpen('lit','B1');wPick('B1','type','sys')")
    t=J("document.getElementById('subMain').innerText")
    ok('Identification' in t and 'Reports sought for retrieval' in t and 'Records from registers' in t,'B1 asks for every PRISMA 2020 number, grouped')
    set_=lambda k,v: J("wNestRedraw('B1','n','%s','%s')"%(k,v))
    set_('id',480); set_('reg',20); set_('dup',90); set_('auto',10)
    svg=J("(document.querySelector('#subMain svg')||{}).outerHTML||''")
    ok('Databases (n = 480)' in svg and 'Registers (n = 20)' in svg and 'automation tools (n = 10)' in svg,'identification shows databases, registers and removals')
    ok('(n = ?)' in svg and 'must be filled' in J("document.getElementById('subMain').innerText"),'numbers not filled yet show as n = ? with a warning')
    set_('scr',400); set_('exT',330); set_('sought',70); set_('notRet',5); set_('ft',65); set_('exF',50); set_('inc',15); set_('repInc',17)
    ok(J("b1FlowIssues(studyGet())")==[],'numbers with registers, automation and not-retrieved add up')
    svg=J("(document.querySelector('#subMain svg')||{}).outerHTML||''")
    for x in ['Reports sought for retrieval','Reports not retrieved','(n = 5)','Reports assessed for eligibility','Reports of included studies (n = 17)']:
        ok(x in svg,'diagram shows '+x)
    ok('(n = ?)' not in svg,'no n = ? once everything is filled')
    set_('ft',70)
    ok(any('not retrieved' in x for x in J("b1FlowIssues(studyGet())")),'full texts must subtract the reports not retrieved')
    set_('ft',65); set_('repInc',12)
    ok(any('cannot be fewer' in x for x in J("b1FlowIssues(studyGet())")),'reports of included studies cannot be fewer than studies')
    set_('repInc',17)
    set_('oId',30); set_('oSought',8); set_('oNotRet',1); set_('oFt',7); set_('oExF',4)
    ok(any('other-methods' in x for x in J("b1FlowIssues(studyGet())")),'included must add the other-methods studies')
    set_('inc',18); set_('repInc',20)
    ok(J("b1FlowIssues(studyGet())")==[],'15 + 3 other-methods studies = 18 included')
    svg=J("(document.querySelector('#subMain svg')||{}).outerHTML||''")
    ok('via other methods' in svg and 'citation searching (n = 30)' in svg,'other-methods part is drawn')
    real=[e for e in errors if 'favicon' not in e[1]]
    ok(not real,'no page errors %s'%real[:3])
    b.close()
print('\n%d failures'%len(fails) if fails else '\nALL PASS')
sys.exit(1 if fails else 0)
