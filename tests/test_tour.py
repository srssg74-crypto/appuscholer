"""First-run demo and the 'why we ask' lines."""
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
    J("showTool('idea');document.getElementById('ideaTopic').value='My own real question';ideaSave()")
    J("localStorage.removeItem('appu_demo');tourAfterWelcome();document.getElementById('welcomeDlg').showModal()")
    ok(J("!!document.getElementById('welcomeDemoBtn')"),'welcome has a demo button')
    J("document.getElementById('welcomeDlg').close()"); pg.wait_for_timeout(600)
    ok(J("document.getElementById('tourOv')&&document.getElementById('tourOv').style.display")=='block','demo starts by itself after the welcome closes')
    ok(J("localStorage.getItem('appu_demo')")=='1','demo marked as seen')
    J("TOUR_PLAY=false;tourGo(2)"); pg.wait_for_timeout(3800)
    ok('screen time at night' in J("document.getElementById('ideaTopic').value"),'example typed into the idea field')
    ok(J("studyGet().idea&&studyGet().idea.topic||''")!='Does screen time at night go with poorer sleep in college students?','example not saved to the study')
    r=J("(()=>{const h=document.getElementById('tourHole').getBoundingClientRect(),e=document.getElementById('ideaTopic').getBoundingClientRect();return Math.abs(h.left-(e.left-6))<3&&Math.abs(h.top-(e.top-6))<3})()")
    ok(r,'spotlight sits on the field')
    pg.screenshot(path=S+'tour-idea.png')
    J("tourGo(5)"); pg.wait_for_timeout(2500)
    ok(J("document.querySelector('.tool-panel.active').dataset.panel")=='research','research tool opened for the search questions')
    ok('sleep quality' in J("document.getElementById('rsTopic').value"),'search words typed')
    J("tourGo(9)"); pg.wait_for_timeout(400)
    pg.screenshot(path=S+'tour-steps.png')
    # autoplay advances
    J("TOUR_PLAY=true;tourGo(0)"); pg.wait_for_timeout(11500)
    ok(J("TOUR_I")>=1,'demo moves on by itself')
    J("tourPause()"); i=J("TOUR_I"); pg.wait_for_timeout(7000)
    ok(J("TOUR_I")==i,'pause stops it')
    J("tourEnd()"); pg.wait_for_timeout(300)
    ok(J("document.getElementById('tourOv').style.display")=='none','skip closes the demo')
    ok(J("document.getElementById('ideaTopic').value")=='My own real question',"student's own text put back")
    ok(J("document.getElementById('rsTopic').value")=='','search box put back')
    # why lines
    J("localStorage.removeItem('appu_why');WHY_SEEN={};showTool('idea')"); pg.wait_for_timeout(200)
    ok('Why we ask' in J("(document.getElementById('why_ideaTopic')||{}).innerHTML||''"),'why line shown in full the first time')
    J("localStorage.setItem('appu_why',JSON.stringify({ideaTopic:5}));WHY_SEEN={};whyRender()")
    ok('<details' in J("document.getElementById('why_ideaTopic').innerHTML"),'folded after a few times')
    J("whyOff()")
    ok(J("document.getElementById('why_ideaTopic')")==None,'whole set can be hidden')
    J("whyOn()")
    ok(J("!!document.getElementById('why_ideaTopic')"),'Help turns them on again')
    J("spOpen()"); pg.wait_for_timeout(300)
    ok(J("!!document.getElementById('why_spHyp')"),'why lines in the study plan dialog')
    J("document.getElementById('spDlg').close()")
    # Hindi
    J("localStorage.setItem('appu_lang','hi');WHY_SEEN={};localStorage.removeItem('appu_why');showTool('idea')"); pg.wait_for_timeout(200)
    ok('क्यों पूछ रहे हैं' in J("document.getElementById('why_ideaTopic').innerHTML"),'Hindi why line')
    J("tourStart();TOUR_PLAY=false;tourGo(0)")
    ok('उदाहरण' in J("document.getElementById('tourTxt').textContent"),'Hindi demo text')
    J("tourEnd()")
    # phone
    pg.set_viewport_size({'width':390,'height':800}); J("localStorage.setItem('appu_lang','en');tourStart();TOUR_PLAY=false;tourGo(3)"); pg.wait_for_timeout(600)
    ok(J("(()=>{const c=document.getElementById('tourCard').getBoundingClientRect();return c.left>=0&&c.right<=390&&c.top>=0&&c.bottom<=800})()"),'card fits on a phone')
    pg.screenshot(path=S+'tour-phone.png'); J("tourEnd()")
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
