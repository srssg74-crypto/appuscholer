"""Comfort settings: opt-in only, saved, applied before paint; Listen button reads the screen."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright

fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

with sync_playwright() as p:
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 1366, 'height': 820})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    H = lambda a: pg.evaluate("a=>document.documentElement.getAttribute(a)", a)
    ok(all(H(a) is None for a in ('data-size','data-contrast','data-bold','data-roomy','data-calm')), 'off by default')
    ok(pg.evaluate("!document.getElementById('listenBtn')"), 'no Listen button by default')
    ok(pg.evaluate("!document.querySelector('header #comfortBtn')"), 'no comfort button in the header')
    pg.evaluate("openHelp()"); pg.click('#comfortBtn'); pg.wait_for_timeout(200)
    ok(pg.is_visible('#comfortDlg'), 'panel opens from Help')
    pg.evaluate("cfSet.size(2);cfSet.con(1);cfSet.bold(1);cfSet.roomy(1);cfSet.calm(1);cfSet.audio(1)")
    ok((H('data-size'), H('data-contrast'), H('data-bold'), H('data-roomy'), H('data-calm')) == ('2','high','1','1','1'), 'all settings apply')
    ok(pg.is_visible('#listenBtn'), 'Listen button appears when audio is on')
    # speech: stub the synthesis API and check it is asked to speak the screen text
    pg.evaluate("""()=>{window.__said=[];window.SpeechSynthesisUtterance=function(t){this.text=t};
      Object.defineProperty(window,'speechSynthesis',{value:{speak:u=>{window.__said.push(u.text);setTimeout(()=>u.onend&&u.onend(),5)},cancel(){},getVoices:()=>[],addEventListener(){}},configurable:true})}""")
    pg.evaluate("document.getElementById('comfortDlg').close();apHomeShow()"); pg.wait_for_timeout(300)
    pg.click('#listenBtn'); pg.wait_for_timeout(300)
    said = pg.evaluate("window.__said.join(' ')")
    ok('step by step' in said, 'Listen reads the home guidance: ' + said[:60])
    pg.reload(); pg.wait_for_timeout(1200)
    ok(H('data-size') == '2' and H('data-contrast') == 'high', 'settings survive a reload')
    pg.evaluate("cfSet.reset()")
    ok(H('data-size') is None and pg.evaluate("!document.getElementById('listenBtn')"), 'reset returns to normal')
    ok(not [e for e in errs if e[0] in ('pageerror',)], 'no page errors %s' % errs[:2])
    b.close()
sys.exit(1 if fails else 0)
