"""Practice study screen: seed, data to Statistics, write first, then the key (build 2026.11.09g)."""
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
    pg.click('.tool-tab[data-tool=practice]'); pg.wait_for_timeout(300)
    ok(J("document.querySelector('[data-panel=practice]').classList.contains('active')"),'tab opens the panel')
    ok(J("document.getElementById('pgRun').hidden")==True,'nothing shown before Start')
    pg.fill('#pgSeed','42'); pg.wait_for_timeout(700); pg.click('#pgStart'); pg.wait_for_timeout(200)
    ok(J("document.getElementById('pgRun').hidden")==False,'run appears after Start')
    ok('invented' in J("document.getElementById('pgStory').innerText").lower(),'story says invented')
    ok(J("document.getElementById('pgReveal').disabled")==True,'key locked before writing')
    pg.fill('#pgQ','Do hostel students feel more anxiety?'); pg.fill('#pgClaim','short')
    ok(J("document.getElementById('pgReveal').disabled")==True,'still locked with a short attempt')
    pg.fill('#pgClaim','Hostel students scored higher on anxiety, so hostel life causes anxiety.')
    ok(J("document.getElementById('pgReveal').disabled")==False,'unlocks after a real attempt')
    pg.wait_for_timeout(700); pg.click('#pgReveal'); pg.wait_for_timeout(200)
    k=J("document.getElementById('pgKey').innerText")
    ok(not J("document.getElementById('pgKey').hidden") and 'confounder' in k and 'reverse worded' in k and 'Hostl' in k,'key shows confounder, reverse item, miscode')
    ok('19 hours' in k,'key names the outlier')
    pg.wait_for_timeout(300); pg.click('#pgOpen'); pg.wait_for_timeout(800)
    ok(J("document.getElementById('statsPaste').value.split('\\n')[0]")=='id,group,year,sleep_hours,a1,a2,a3,a4,a5','data lands in Statistics')
    ok(J("document.querySelector('[data-panel=stats]').classList.contains('active')"),'Statistics tab opened')
    pg.reload(); pg.wait_for_timeout(1500); pg.click('.tool-tab[data-tool=practice]'); pg.wait_for_timeout(300)
    ok(J("document.getElementById('pgQ').value").startswith('Do hostel') and not J("document.getElementById('pgKey').hidden"),'work and reveal survive reload')
    J("LS.set('appu_lang','hi');applyLang()"); pg.wait_for_timeout(300)
    ok('अभ्यास' in J("document.getElementById('pgTitle').innerText") and 'उत्तर-कुंजी' in J("document.getElementById('pgKey').innerText"),'Hindi title and key')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
