"""Boxes show they are saved, panels never scroll sideways, and the AI key button pulses until a key is saved (build 2026.11.02f)."""
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
    b,pg=new_page(p,errors,viewport={'width':1120,'height':670})
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    ok(J("document.body.classList.contains('no-ai-key')"),'no key: the AI key button pulses')
    J("openNewProjectDirect();document.getElementById('sapName').value='Sleep';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){};showTool('idea')"); pg.wait_for_timeout(300)
    ok(J("document.querySelectorAll('.fs-wrap .fs-go').length")==4,'each Idea box has a save arrow inside it')
    pg.fill('#ideaResources','Two colleges agreed; 150 students')
    pg.press('#ideaResources','Enter'); pg.wait_for_timeout(150)
    ok(J("document.getElementById('ideaResources').value")=='Two colleges agreed; 150 students','Enter saves instead of adding a new line')
    ok('Saved' in J("document.querySelector('label[for=ideaResources]').innerText"),'a saved time shows on the label line')
    pg.fill('#ideaTimeframe','Five months'); pg.locator('#ideaTimeframe + .fs-go').click(); pg.wait_for_timeout(150)
    ok(J("studyGet().idea.timeframe")=='Five months','the Save button stores the box')
    # a very wide line must not push the panel sideways
    J("const d=document.createElement('pre');d.textContent='Screener-NIFTY50-'+'x'.repeat(400);document.querySelector('.tool-panel.active .panel').appendChild(d);const t=document.createElement('table');t.innerHTML='<tr>'+'<td>wide cell content</td>'.repeat(30)+'</tr>';document.querySelector('.tool-panel.active .panel').appendChild(t)")
    pg.wait_for_timeout(100)
    ok(J("(()=>{const m=document.querySelector('.tool-main');return m.scrollWidth<=m.clientWidth+1})()"),'the tool panel does not scroll sideways')
    # come back later: the boxes are filled and say when they were saved
    pg.reload(); pg.wait_for_timeout(1500); J("showTool('idea')"); pg.wait_for_timeout(200)
    ok(J("document.getElementById('ideaResources').value")=='Two colleges agreed; 150 students','after coming back the box still holds the text')
    ok('Saved' in J("document.querySelector('label[for=ideaResources]').innerText"),'and says when it was saved')
    # other boxes flash Saved on change
    J("subOpen('idea','A3')"); pg.wait_for_timeout(200)
    loc=pg.locator("#subMain textarea[onchange*=\"'aim'\"],#subMain textarea[oninput*=\"'aim'\"]").first
    loc.fill('To examine sleep and exam anxiety in first-year students'); loc.dispatch_event('change'); pg.wait_for_timeout(100)
    ok(J("!!document.querySelector('#subMain .fs-tick.on')") or 'Saved' in J("document.getElementById('subMain').innerText"),'a step box shows Saved')
    J("document.getElementById('subDlg').close()")
    # the tool panel grows while a box is filled and returns afterwards
    pg.click('#ideaTimeframe'); pg.wait_for_timeout(300)
    ok(J("document.body.classList.contains('tool-big')") and J("document.querySelector('.tool-main').getBoundingClientRect().width")>500,'clicking into a box makes the tool panel bigger')
    pg.mouse.click(300,450); pg.wait_for_timeout(200)
    ok(not J("document.body.classList.contains('tool-big')"),'a click back in the document puts it back')
    J("tbToggle()"); pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    ok(not J("document.body.classList.contains('tool-big')"),'Esc puts it back too')
    J("LS.set('appu_key_gemini','AIza'+'x'.repeat(35));refreshProvUI()")
    ok(not J("document.body.classList.contains('no-ai-key')"),'with a key saved the button stops pulsing')
    b.close()
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:2])
print('FAILED' if fails else 'ALL PASS', len(fails))
