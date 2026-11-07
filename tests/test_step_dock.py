"""The tool of a step opens beside it: step on the left, tool on the right. Phones get a pill back to the step. Named buttons, new diary label."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='Dock';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("subOpen('idea','A1')"); pg.wait_for_timeout(300)
    t=J("document.getElementById('subMain').innerText")
    ok('My research diary: To do / To check' in t and 'My notes' not in t,'diary label replaces "My notes"')
    ok('Ask AI to check my topic' in t and 'Go to the tool for this' not in t,'the button says which tool it opens')
    pg.locator('#subMain button:has-text("Ask AI to check my topic")').click(); pg.wait_for_timeout(500)
    ok(J("document.getElementById('subDlg').classList.contains('sub-docked') && document.getElementById('subDlg').open"),'the step dialog docks to the left')
    ok(J("document.getElementById('subDlg').matches(':modal')")==False,'it is not modal, so the tool beside it can be used')
    w=J("document.getElementById('subDlg').getBoundingClientRect().width")
    ok(w>=1300 and J("Math.abs(document.getElementById('subDlg').getBoundingClientRect().bottom-innerHeight)<3"),'the step is a task bar along the bottom (%d wide)'%w)
    ok(J("document.body.classList.contains('sub-docked-on')"),'the page makes room for it')
    ok(J("!!document.getElementById('ideaTopic') && document.getElementById('ideaTopic').getBoundingClientRect().width>600"),'the Idea tool gets the full width')
    ok('Who' in J("document.getElementById('tbChips').innerText"),'what is still needed stays in the bar')
    J("subUndock()"); pg.wait_for_timeout(300)
    ok(J("document.getElementById('subDlg').matches(':modal') && !document.getElementById('subDlg').classList.contains('sub-docked')"),'All steps goes back to the full view')
    J("document.getElementById('subDlg').close()"); pg.wait_for_timeout(200)
    ok(J("!document.body.classList.contains('sub-docked-on')"),'closing removes the room made for the dock')
    # dialog-type tools still open as before
    J("subOpen('design','C6')"); pg.wait_for_timeout(300)
    ok('Open the questionnaire maker' in J("document.getElementById('subMain').innerText"),'a dialog tool is named too')
    # phone
    pg.set_viewport_size({'width':390,'height':800}); pg.wait_for_timeout(200)
    J("subOpen('idea','A1')"); pg.wait_for_timeout(300)
    pg.locator('#subMain button:has-text("Ask AI to check my topic")').click(); pg.wait_for_timeout(500)
    ok(J("!document.getElementById('subDlg').open"),'phone: the step closes and the tool takes the screen')
    ok(J("!!document.getElementById('subBackPill')"),'phone: a pill offers the way back to the step')
    J("document.getElementById('subBackPill').click()"); pg.wait_for_timeout(300)
    ok(J("document.getElementById('subDlg').open && !document.getElementById('subBackPill')"),'the pill brings the step back and goes away')
    # one place to type: the step panel is guide-only, the tool side holds the boxes
    pg.set_viewport_size({'width':1366,'height':900}); pg.wait_for_timeout(200)
    J("subOpen('idea','A1')"); pg.wait_for_timeout(300)
    pg.locator('#subMain button:has-text("Ask AI to check my topic")').click(); pg.wait_for_timeout(600)
    ok(J("document.querySelectorAll('#subMain .a1-f input').length")==0,'docked: no type-boxes in the step panel')
    ok(J("document.querySelectorAll('#subWork .a1-f input').length")==5,'docked: the boxes sit on the tool side')
    J("(()=>{const i=document.querySelectorAll('#subWork .a1-f input');i[0].value='first-year nursing students';i[0].oninput()})()"); pg.wait_for_timeout(300)
    ok('Who' not in J("document.getElementById('tbChips').innerText"),'typing a box ticks it off in the bar')
    J("subUndock()"); pg.wait_for_timeout(300)
    ok(J("!document.getElementById('subWork') && document.querySelectorAll('#subMain .a1-f input').length")>=3,'back to all steps: boxes return to the step, tool-side card is gone')
    real=[e for e in errors if 'favicon' not in e[1]]
    ok(not real,'no page errors %s'%real[:3])
    b.close()
print('\n%d failures'%len(fails) if fails else '\nALL PASS')
sys.exit(1 if fails else 0)
