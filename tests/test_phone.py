"""Version 124 phone layout: one view at a time from a bottom bar (Home, Steps, Write, AI help), in English and Hindi."""
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
    b, pg = harness.new_page(p, errs, {'width': 390, 'height': 844})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    pg.evaluate("saveProjectsList([{id:'p1',name:'Sleep and exam stress (sample)',stage:'design',status:'active'}]);LS.set('appu_active_project','p1')")
    ok(pg.is_visible('#phNav') and pg.evaluate("document.querySelectorAll('#phNav button').length") == 4, 'bottom bar with four places')
    pg.evaluate("apGoTool('design')"); pg.wait_for_timeout(400)
    ok(pg.is_visible('.tool-panel[data-panel=design]') and not pg.is_visible('#editor'), 'Steps shows the stage tools, not the page')
    pg.click('#phNav button:nth-child(3)'); pg.wait_for_timeout(300)
    ok(pg.is_visible('#editor') and not pg.is_visible('.tool-panel[data-panel=design]') and not pg.is_visible('#stageBar'), 'Write shows the page alone')
    pg.click('#phNav button:nth-child(4)'); pg.wait_for_timeout(300)
    ok(pg.is_visible('#aiPane') and not pg.is_visible('#editor'), 'AI help shows the suggestion pane')
    pg.click('#phNav button:nth-child(1)'); pg.wait_for_timeout(300)
    ok(pg.evaluate("apHomeIs()") and pg.is_visible('.hm-hero'), 'Home opens the home screen')
    pg.click('#phNav button:nth-child(2)'); pg.wait_for_timeout(300)
    ok(not pg.evaluate("apHomeIs()") and pg.is_visible('.tool-main .tool-panel.active'), 'Steps leaves home and shows the open stage')
    pg.evaluate("apGoTool('stats')"); pg.wait_for_timeout(300)
    ok(pg.evaluate("[...document.querySelectorAll('.tool-sidebar .stage-group')].filter(g=>g.offsetParent).length") == 1, 'only the open stage is listed in Steps')
    ok(pg.evaluate("document.querySelector('.stage-group.calm-cur .stage-header').getAttribute('data-sn')") == '4', 'stage keeps its own number when alone')
    pg.evaluate("toggleLang()"); pg.wait_for_timeout(300)
    ok('लिखें' in pg.inner_text('#phNav'), 'bottom bar in Hindi')
    ok(pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"), 'no sideways scroll')
    b.close()
    errs2 = []
    b, pg = harness.new_page(p, errs2, {'width': 1366, 'height': 800})
    pg.goto(harness.BASE); pg.wait_for_timeout(1200)
    ok(not pg.is_visible('#phNav') and pg.is_visible('#editor'), 'no bottom bar on a laptop')
    b.close()
    bad = [e for e in errs + errs2 if e[0] == 'pageerror']
    ok(not bad, 'no page errors %s' % bad[:3])
sys.exit(1 if fails else 0)
