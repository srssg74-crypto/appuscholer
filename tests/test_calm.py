"""Version 121 calm look: new logo and icons, warm-white page, tools as one quiet list with status,
no emoji in the interface, and the home hero with one main button (English and Hindi, phone and laptop)."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

EMO = re.compile('[\U0001F300-\U0001FAFF☀-➿]')
with sync_playwright() as p:
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 1366, 'height': 900})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    ok(pg.evaluate("!!document.getElementById('calm-2026-11-22')"), 'calm style layer present')
    ok(pg.evaluate("getComputedStyle(document.body).backgroundColor") == 'rgb(250, 248, 244)', 'warm-white page')
    ok(pg.evaluate("!!document.querySelector('header svg.logo path[stroke=\"#F0A33C\"]')"), 'new logo in the header')
    ok(pg.evaluate("[...document.querySelectorAll('link[rel=icon]')].some(l=>l.href.endsWith('logo.svg'))"), 'svg favicon linked')
    # home hero
    pg.evaluate("apHomeShow()"); pg.wait_for_timeout(300)
    ok(pg.is_visible('.hm-hero .hm-go') and 'Start a project' in pg.inner_text('.hm-hero'), 'home hero offers one main action with no project')
    ok(not pg.is_visible('.project-bar .btn-new'), 'duplicate New project hidden on home')
    pg.evaluate("toggleLang()"); pg.wait_for_timeout(300)
    ok('प्रोजेक्ट शुरू करें' in pg.inner_text('.hm-hero'), 'hero in Hindi')
    pg.evaluate("toggleLang()"); pg.wait_for_timeout(300)
    # design stage: one list with status
    pg.evaluate("apGoTool('design')"); pg.wait_for_timeout(400)
    rows = pg.evaluate("[...document.querySelectorAll('.tool-panel[data-panel=design] .tl-row')].map(b=>b.textContent.trim())")
    ok(len(rows) >= 6, 'design tools shown as list rows: %d' % len(rows))
    ok(not any(EMO.search(r[:2]) for r in rows), 'no emoji at the start of tool rows: %s' % rows[:3])
    ok(pg.evaluate("document.querySelectorAll('#designDash button').length") == 0, 'checklist no longer repeats the tools')
    ok(pg.evaluate("document.querySelectorAll('.tool-panel[data-panel=design] .tl-row[data-st]').length") >= 6, 'each design tool shows its status')
    pg.evaluate("designSet('reg',{done:true});designRenderDash()"); pg.wait_for_timeout(100)
    ok(pg.evaluate("document.querySelector('.tool-panel[data-panel=design] .tl-row[data-st=done]')!==null") and '1 of 6' in pg.inner_text('#designDash'), 'finished tool marked done and counted')
    ok(pg.evaluate("document.querySelectorAll('.tool-panel[data-panel=design] .tl-main').length") == 1, 'one main button in the stage')
    # editor text is never changed by the emoji pass
    pg.evaluate("document.getElementById('editor').innerHTML='<p>✅ my own text</p>'"); pg.wait_for_timeout(300)
    ok('✅ my own text' in pg.inner_text('#editor'), 'student text keeps its symbols')
    # project hero with progress
    pg.evaluate("saveProjectsList([{id:'p1',name:'Sleep and exam stress',stage:'design',status:'active'}]);LS.set('appu_active_project','p1');apHomeShow()")
    pg.wait_for_timeout(300)
    t = pg.inner_text('.hm-hero')
    ok('Sleep and exam stress' in t and 'Continue' in t and 'Stage 3 / 6' in t, 'hero shows the project, its stage and Continue: %r' % t[:120])
    ok(pg.evaluate("document.querySelectorAll('.hm-bar i.d').length") == 2, 'progress bar marks two finished stages')
    bad = [e for e in errs if e[0] == 'pageerror']
    ok(not bad, 'no page errors %s' % bad[:3])
    b.close()
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 400, 'height': 860})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    pg.evaluate("apHomeShow()"); pg.wait_for_timeout(300)
    ok(pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"), 'no sideways scroll on a phone')
    hero_y = pg.evaluate("document.querySelector('.hm-hero').getBoundingClientRect().top")
    me_y = pg.evaluate("document.querySelector('.hm-me').getBoundingClientRect().top")
    ok(hero_y < me_y, 'on a phone the hero comes before the profile card')
    ok(pg.evaluate("getComputedStyle(document.getElementById('cmdBtn').querySelector('span')).display") == 'none', 'phone header shows the search icon only')
    bad = [e for e in errs if e[0] == 'pageerror']
    ok(not bad, 'no page errors on phone %s' % bad[:3])
    b.close()
sys.exit(1 if fails else 0)
