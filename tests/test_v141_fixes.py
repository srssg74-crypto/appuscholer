"""Version 141: the fixes found on 24 Nov.
- The lecture theatre fits the window at every comfort text size, and its text bar still grows with the size.
- The theatre opens at once; it does not wait for the classroom picture.
- Listen never covers Continue: in the top bar on a laptop, above the bottom bar on a phone.
- Arriving from the account page (?acct=1) marks the device, and the marker leaves the address bar.
- Invite and admin messages say exactly what went wrong (static check of the pages' text)."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

def open_lecture(pg):
    pg.evaluate("apHomeLectures()"); pg.wait_for_timeout(600)
    pg.locator('dialog[open] button:has-text("The gap")').first.click(); pg.wait_for_timeout(800)

with sync_playwright() as p:
    # 1. theatre fits at every text size, laptop and phone
    for (w, h) in [(1366, 768), (390, 844)]:
        sizes = {}
        for sz in ['', '1', '2', '3']:
            errs = []
            b, pg = harness.new_page(p, errs, {'width': w, 'height': h})
            pg.add_init_script("localStorage.setItem('appu_comfort',JSON.stringify({size:'%s'}))" % sz)
            pg.goto(harness.BASE); pg.wait_for_timeout(1200)
            open_lecture(pg); pg.evaluate("apThOpen()"); pg.wait_for_timeout(1500)
            r = pg.evaluate("""(()=>{const s=document.querySelector('#apTh .th-sub').getBoundingClientRect(),b=document.getElementById('thBox').getBoundingClientRect();
              return {sub:[s.left,s.right,s.bottom],box:[b.left,b.right,b.bottom],vw:innerWidth,vh:innerHeight,fs:parseFloat(getComputedStyle(document.querySelector('#apTh .th-sub')).fontSize)}})()""")
            fits = r['sub'][0] >= -1 and r['sub'][1] <= r['vw'] + 1 and r['sub'][2] <= r['vh'] + 1 and r['box'][1] <= r['vw'] + 1
            ok(fits, 'theatre fits %dx%d at text size %s' % (w, h, sz or 'normal'))
            sizes[sz] = r['fs']
            ok(not [e for e in errs if e[0] == 'pageerror'], 'no page errors %dx%d size %s' % (w, h, sz or 'normal'))
            b.close()
        ok(sizes['3'] > sizes[''], 'the text bar is larger at the largest size (%s > %s px) on %d px' % (sizes['3'], sizes[''], w))

    # 2. theatre opens at once while the classroom picture is still on its way
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 1366, 'height': 768})
    def slow(route):
        import time; time.sleep(4); route.continue_()
    pg.context.route('**/assets/bg_class.webp', slow)
    pg.goto(harness.BASE); pg.wait_for_timeout(1200)
    open_lecture(pg)
    pg.evaluate("apThOpen()"); pg.wait_for_timeout(700)
    ok(pg.evaluate("!!document.getElementById('apTh')&&document.getElementById('apTh').open"), 'theatre is open within a second, before the picture arrives')
    b.close()

    # 3. Listen placement
    for (w, h, where) in [(1366, 768, 'laptop'), (390, 844, 'phone')]:
        errs = []
        b, pg = harness.new_page(p, errs, {'width': w, 'height': h})
        pg.add_init_script("localStorage.setItem('appu_comfort',JSON.stringify({audio:true}))")
        pg.goto(harness.BASE); pg.wait_for_timeout(1200)
        pg.evaluate("saveProjectsList([{id:'p1',name:'Sleep and exam stress',stage:'design',status:'active'}]);LS.set('appu_active_project','p1');cfListenBtn();apHomeShow()")
        pg.wait_for_timeout(600)
        if where == 'laptop':
            ok(pg.evaluate("document.getElementById('listenBtn').closest('header')!==null"), 'Listen sits in the top bar on a laptop')
        else:
            r = pg.evaluate("(()=>{const l=document.getElementById('listenBtn').getBoundingClientRect(),n=document.getElementById('phNav').getBoundingClientRect();return [l.bottom,n.top]})()")
            ok(r[0] <= r[1], 'Listen sits above the phone bottom bar: %s' % r)
        cov = pg.evaluate("""(()=>{const L=document.getElementById('listenBtn').getBoundingClientRect();return [...document.querySelectorAll('.hm-go')].filter(x=>{const r=x.getBoundingClientRect();return r.width&&!(r.right<=L.left||r.left>=L.right||r.bottom<=L.top||r.top>=L.bottom)}).length})()""")
        ok(cov == 0, 'Listen does not cover Continue on the %s' % where)
        b.close()

    # 4. account marker
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 1366, 'height': 768})
    pg.goto(harness.BASE.replace('index.html', 'index.html?acct=1')); pg.wait_for_timeout(1500)
    ok(pg.evaluate("localStorage.getItem('appu_acct_seen')")=='1' and 'acct=1' not in pg.url, 'arriving from the account page marks the device and cleans the address')
    b.close()

# 5. static checks of the account and admin pages
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
auth = open(os.path.join(root, 'auth.html'), encoding='utf-8').read()
admin = open(os.path.join(root, 'admin.html'), encoding='utf-8').read()
backend = open(os.path.join(root, 'backend.js'), encoding='utf-8').read()
ok(all(k in auth for k in ['INVITE_EXPIRED', 'INVITE_INACTIVE', 'INVITE_USED_UP', 'ALREADY_REDEEMED']), 'student page explains expired, switched-off, used-up and already-joined codes')
ok('appu-profile-open' in auth, 'profile page has an Open Appuscholar button')
ok(all(k in admin for k in ['SIGN_IN_FAILED', 'PAST_DATE', 'isAdmin()', 'btn.disabled=true']), 'admin page: wrong-password message, admin check, no past date, no double create')
ok(all(k in backend for k in ["fail('INVITE_EXPIRED'", "fail('INVITE_INACTIVE'", "fail('INVITE_USED_UP'", 'isAdmin()']), 'backend gives the exact reason a code cannot be used')
sys.exit(1 if fails else 0)
