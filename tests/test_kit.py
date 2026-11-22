"""Student test kit (kit.html): consent gate, five tasks with timer, SUS, open questions, summary and the
researcher results page that reads the APPUKIT lines."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
KIT = harness.BASE.replace('index.html', '') + 'kit.html'
with sync_playwright() as p:
    for w in (390, 1366):
        errs = []
        b, pg = harness.new_page(p, errs, {'width': w, 'height': 860})
        pg.goto(KIT + '?r=2'); pg.wait_for_timeout(800)
        pg.evaluate("localStorage.removeItem('appu_kit_v1')"); pg.reload(); pg.wait_for_timeout(600)
        ok(pg.is_disabled('#startBtn'), 'start is locked until 18+ and consent are ticked')
        pg.check('#c18'); pg.check('#cok')
        ok(not pg.is_disabled('#startBtn'), 'ticking both unlocks start'); pg.click('#startBtn')
        pg.click('[data-g=subj] button[data-v=psy]'); pg.click('[data-g=dev] button[data-v=phone]')
        pg.click('text=Go to task 1')
        for i in range(5):
            ok(f'Task {i+1} / 5' in pg.inner_text('main'), f'task {i+1} shown')
            if i == 3: ok('group,stress' in pg.inner_text('.code'), 'task 4 shows the sample data')
            pg.wait_for_timeout(1100)
            pg.click('.choices button:nth-child(%d)' % (1 if i != 2 else 3))
            if i == 1: pg.fill('#tn', 'Could not find the AI key box')
            pg.click('text=' + ('Next task' if i < 4 else 'Next: your opinion'))
        ok(pg.is_disabled('#susNext'), 'SUS needs every statement answered')
        for k in range(10):
            pg.click(f'[data-s="{k}"] button[data-v="{4 if k % 2 == 0 else 2}"]')
        pg.click('#susNext')
        ok('Which part did you use most' in pg.inner_text('main'), 'round 2 adds the week questions')
        pg.fill('#o_hard', 'Finding the library')
        pg.click('text=See my summary')
        t = pg.inner_text('main')
        ok('75' in pg.inner_text('.big'), 'SUS scored by Brooke\'s rule (all 4s and 2s = 75): %s' % pg.inner_text('.big'))
        ok('APPUKIT:' in t and 'wa.me' in pg.get_attribute('a.btn', 'href'), 'summary with the APPUKIT line and a WhatsApp link')
        msg = pg.evaluate("summary().text")
        pg.evaluate("toggleLang()"); pg.wait_for_timeout(200)
        ok('अपने उत्तर भेजें' in pg.inner_text('main'), 'Hindi')
        pg.evaluate("toggleLang()")
        pg.goto(KIT + '#results'); pg.wait_for_timeout(400)
        pg.fill('#rIn', 'From Riya:\n' + msg + '\n\nduplicate:\n' + msg); pg.click('text=Build the table'); pg.wait_for_timeout(300)
        r = pg.inner_text('#rOut')
        ok('Students: 1' in r and '75' in r, 'results page reads the line once and shows SUS')
        ok('Could not find the AI key box' in r and 'Finding the library' in r, 'notes and answers listed')
        ok(pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"), f'no sideways scroll at {w}px')
        bad = [e for e in errs if e[0] == 'pageerror']
        ok(not bad, 'no page errors %s' % bad[:2])
        b.close()
sys.exit(1 if fails else 0)
