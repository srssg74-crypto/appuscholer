"""Stage 1 flow (build 2026.11.02r): header with video slot, flow strip, A4 chips and decision cards."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='Flow';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("subOpen('idea','A1')"); pg.wait_for_timeout(300)
    t=J("document.getElementById('subDlg').innerText")
    ok('Find your idea and test it' in t and 'video coming soon' in t,'stage header with purpose and a video slot')
    ok(J("document.querySelectorAll('#s1Flow .s1-node').length")==4 and 'Decision' in t,'flow strip: four steps and the decision')
    ok(J("getComputedStyle(document.querySelector('#subDlg .sub-list')).display")=='none','the old left list is gone for stage 1')
    ok('Ask AI to check my topic' in t,'step button is named by its result')
    # clicking a node opens that step
    pg.locator('#s1Flow .s1-node').nth(2).click(); pg.wait_for_timeout(200)
    ok('Question, aim' in J("document.getElementById('subMain').innerText"),'a flow node opens its step')
    # typing updates the strip
    pg.locator('#s1Flow .s1-node').nth(0).click(); pg.wait_for_timeout(200)
    ins=pg.locator('#subMain .a1-f input'); ins.nth(0).fill('first-year nursing students'); ins.nth(1).fill('exam anxiety'); ins.nth(2).fill('two colleges in Pune'); pg.wait_for_timeout(300)
    ok('exam anxiety' in J("document.querySelector('#s1Flow .s1-node').innerText"),'the strip shows the student\'s own topic under step 1')
    # A4
    pg.locator('#s1Flow .s1-node').nth(3).click(); pg.wait_for_timeout(200)
    n=J("document.querySelectorAll('#a4Rows .a4-seg').length"); ok(n==7,'A4 has seven rating rows')
    for i in range(7): pg.locator('#a4Rows .a4-seg').nth(i).locator('label').nth(0).click()
    pg.locator('#a4Rows .a4-seg').nth(6).locator('label').nth(1).click(); pg.wait_for_timeout(200)
    ok('6 fine, 1 risk, 0 not possible' in J("document.getElementById('a4Sum').innerText") and 'Go ahead' in J("document.getElementById('a4Sum').innerText"),'live summary suggests go with one risk')
    pg.locator('#a4Rows .a4-seg').nth(0).locator('label').nth(2).click(); pg.wait_for_timeout(200)
    ok('Revise' in J("document.getElementById('a4Sum').innerText"),'a "not possible" turns the suggestion to revise')
    ok(J("document.querySelectorAll('#a4Dcs .a4-dc').length")==4,'four decision cards')
    pg.locator('#a4Dcs .a4-dc-new').click(); pg.wait_for_timeout(200)
    ok(J("(studyGet().inbox||[]).some(x=>x.t.indexOf('Set aside topic')===0&&x.t.indexOf('exam anxiety')>0)"),'"New topic" saves the old topic to the Idea inbox')
    ok('New topic' in J("document.querySelector('#s1Flow .s1-dec').innerText"),'the strip shows the decision taken')
    pg.locator('#a4Dcs .a4-dc-go').click(); pg.wait_for_timeout(200)
    ok(J("studyGet().write.A4.dec")=='go','Go is stored')
    # the same header and strip on the other five stages
    for st,sid,title,n in [('lit','B3','Read what is already known',3),('design','C6','Plan how you will find out',4),('collect','D4','Collect and analyse your data',4),('writing','E5','Write it up',4),('review','F3','Check, submit and share',4)]:
        J("subOpen('%s','%s')"%(st,sid)); pg.wait_for_timeout(250)
        ok(title in J("document.getElementById('subDlg').innerText") and J("document.querySelectorAll('#s1Flow .s1-node').length")==n,'%s: header and %d-group strip'%(st,n))
        ok(J("document.querySelectorAll('#s1Sub .s1-sp').length")>=1 or st=='writing' and False,'%s: the steps of the current group are listed'%st)
    J("subOpen('lit','B1')"); pg.wait_for_timeout(200)
    pg.locator('#s1Flow .s1-node').nth(1).click(); pg.wait_for_timeout(250)
    ok(J("SUB_CUR.id")=='B3','a group node opens its first open step')
    pg.locator('#s1Sub .s1-sp').nth(1).click(); pg.wait_for_timeout(250)
    ok(J("SUB_CUR.id")=='B4','a step pill inside the group opens that step')
    real=[e for e in errors if 'favicon' not in e[1]]
    ok(not real,'no page errors %s'%real[:3]); b.close()
print('\n%d failures'%len(fails) if fails else '\nALL PASS'); sys.exit(1 if fails else 0)
