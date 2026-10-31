"""PRISMA flow from B1 numbers; participant flow from the D2 log."""
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
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Diagrams';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("subOpen('lit','B1');wPick('B1','type','sys')")
    ok('appears here once all seven numbers' in J("document.getElementById('subMain').innerText"),'no diagram before the numbers')
    for k,v in [('id',512),('dup',112),('scr',400),('exT',340),('ft',60),('exF',45),('inc',15)]: J("wNestRedraw('B1','n','%s','%d')"%(k,v))
    J("wPick('B1','exWhy','Wrong population: 20\\nNo outcome measure: 15\\nNot peer reviewed: 10')"); pg.wait_for_timeout(200)
    svg=J("(document.querySelector('#subMain svg')||{}).outerHTML||''")
    for t in ['(n = 512)','(n = 112)','(n = 400)','(n = 340)','(n = 60)','(n = 45)','(n = 15)','Wrong population: 20','Identification','Screening','Included']:
        ok(t in svg,'PRISMA shows '+t)
    pg.locator('#subMain svg').first.screenshot(path=S+'prisma.png')
    J("wNestRedraw('B1','n','inc','14')")
    ok(J("document.querySelector('#subMain svg')")==None,'no diagram when the numbers do not add up')
    J("wNestRedraw('B1','n','inc','15')")
    J("document.getElementById('subDlg').close();setEditorHTML('<p>x</p>');dgPrismaInsert()"); pg.wait_for_timeout(800)
    ed=J("getEditorHTML()")
    ok('data:image/png' in ed and 'PRISMA 2020 flow diagram' in ed,'PRISMA diagram inserted as a picture with caption')
    J("subOpen('collect','D2')")
    ok('recruitment log below' in J("document.getElementById('subMain').innerText"),'participant flow waits for the log')
    J("logAdd('recruit');logCell('recruit',0,'appr','120');logCell('recruit',0,'agreed','95');logCell('recruit',0,'done','88');logCell('recruit',0,'left','3')"); pg.wait_for_timeout(200)
    svg=J("(document.querySelector('#subMain svg')||{}).outerHTML||''")
    ok('(n = 120)' in svg and '(n = 25)' in svg and '(n = 7)' in svg and 'withdrew: 3' in svg and '(n = 88)' in svg,'participant flow: 120 approached, 25 declined, 7 did not finish, 88 analysed')
    pg.locator('#subMain svg').first.screenshot(path=S+'partflow.png')
    # Gantt
    J("subOpen('design','C8')")
    for st,a,d in [('idea',1,2),('lit',2,4),('design',5,3),('collect',8,6),('writing',12,8),('review',19,4)]: J("dgPlanSet('%s','a','%d');dgPlanSet('%s','d','%d')"%(st,a,st,d))
    svg=J("(document.querySelector('#subMain svg')||{}).outerHTML||''")
    ok('Data collection and analysis' in svg and svg.count('fill="#4b6fa8"')==6,'time chart drawn with six stage bars')
    pg.locator('#subMain svg').first.screenshot(path=S+'gantt.png')
    J("document.getElementById('subDlg').close();setEditorHTML('<p>x</p>');dgGanttInsert()"); pg.wait_for_timeout(800)
    ok('Work plan of the study' in J("getEditorHTML()"),'time chart inserted with caption')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
