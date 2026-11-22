"""Version 121 layout guard: every main screen, at laptop, tablet and phone widths and in English and Hindi,
must not scroll sideways, push a control off the screen or cut a label short. Fixing one screen must not break another."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
setup = "saveProjectsList([{id:'p1',name:'Sleep quality and exam stress in first-year students',stage:'design',status:'active'}]);LS.set('appu_active_project','p1');"
cases = [('home', "apHomeShow()"), ('lit', "apGoTool('research')"), ('design', "apGoTool('design')"), ('stats', "apGoTool('stats')"), ('writing', "apGoTool('style')"), ('review', "apGoStage('review')")]
CHECK = """(()=>{const o=[];if(document.documentElement.scrollWidth>innerWidth+1)o.push('page scrolls sideways');
  document.querySelectorAll('header button, .stagebar button, .dock-tabs button, .project-bar button, .tool-sidebar button, .fmtbar button, .doc-pane .toolbar button').forEach(e=>{if(!e.offsetParent)return;const r=e.getBoundingClientRect();if(r.right>innerWidth+1)o.push('off-screen: '+e.textContent.trim().slice(0,30));if(e.scrollWidth>e.clientWidth+2&&getComputedStyle(e).overflow!=='visible')o.push('cut text: '+e.textContent.trim().slice(0,30))});
  const fb=document.getElementById('fmtBar'),fm=document.getElementById('fmtMoreBtn');if(fb&&fm&&fm.offsetParent&&fm.getBoundingClientRect().right>fb.getBoundingClientRect().right+1)o.push('toolbar More button clipped');
  return o})()"""
with sync_playwright() as p:
    for (w, h, tag) in [(1366, 768, 'laptop'), (1180, 820, 'tablet'), (400, 860, 'phone')]:
        for lang in ['en', 'hi']:
            errs = []
            b, pg = harness.new_page(p, errs, {'width': w, 'height': h})
            pg.goto(harness.BASE); pg.wait_for_timeout(1400); pg.evaluate(setup)
            if lang == 'hi': pg.evaluate("toggleLang()"); pg.wait_for_timeout(300)
            for name, js in cases:
                pg.evaluate(js); pg.wait_for_timeout(450)
                r = pg.evaluate(CHECK)
                ok(not r, '%s %s %s: %s' % (tag, lang, name, r[:4] if r else 'clean'))
            bad = [e for e in errs if e[0] == 'pageerror']
            ok(not bad, 'no page errors %s %s %s' % (tag, lang, bad[:2]))
            b.close()
sys.exit(1 if fails else 0)
