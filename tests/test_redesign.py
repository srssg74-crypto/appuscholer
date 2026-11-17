"""Redesign of 17 Nov: icon rail (wide screens only), Ctrl+K command search in English and Hindi, the
"Stays on this device" chip and its dialog, the one-time AI notice, polite use of Crossref/OpenAlex/PubMed
(mailto added, requests spaced out), and the phone swipe between Tools and the AI suggestion."""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

with sync_playwright() as p:
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 1536, 'height': 900})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    ok(pg.is_visible('#iconRail') and pg.evaluate("document.querySelectorAll('#iconRail button').length") == 9, 'rail shows nine places on a wide screen')
    ok(pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"), 'no sideways scroll with the rail')
    pg.evaluate("apGoTool('cite')"); pg.wait_for_timeout(150)
    ok(pg.evaluate("document.querySelector('#iconRail [data-rl=cite]').classList.contains('on')"), 'rail marks the open place')
    # command search
    pg.keyboard.press('Control+k'); pg.wait_for_timeout(150)
    ok(pg.is_visible('#cmdDlg') and pg.evaluate("document.activeElement.id") == 'cmdQ', 'Ctrl+K opens the search with the cursor in it')
    pg.fill('#cmdQ', 'margin'); pg.wait_for_timeout(100)
    first = pg.inner_text('#cmdo0')
    ok('Margin map' in first, 'typing finds the margin map first: %r' % first[:40])
    pg.keyboard.press('Enter'); pg.wait_for_timeout(250)
    ok(not pg.is_visible('#cmdDlg') and pg.evaluate("!!(document.getElementById('mmDlg')||{}).open"), 'Enter runs the action and closes the search')
    pg.evaluate("document.getElementById('mmDlg').close()")
    pg.keyboard.press('Control+k'); pg.wait_for_timeout(100)
    ok('Margin map' in pg.inner_text('#cmdList').split('\n')[1] and 'Recent' in pg.inner_text('#cmdList'), 'last pick listed under Recent')
    pg.fill('#cmdQ', 'stat char'); pg.wait_for_timeout(100)
    pg.keyboard.press('ArrowDown'); pg.keyboard.press('ArrowUp'); pg.wait_for_timeout(50)
    ok(pg.get_attribute('#cmdo0', 'aria-selected') == 'true', 'arrow keys move the choice')
    pg.keyboard.press('Enter'); pg.wait_for_timeout(250)
    ok(pg.evaluate("document.querySelector('.tool-tab.active').dataset.tool") == 'stats', 'a tool opens from the search')
    pg.keyboard.press('Control+k'); pg.fill('#cmdQ', 'zzqqxx'); pg.wait_for_timeout(100)
    ok('Nothing matches' in pg.inner_text('#cmdList'), 'no match says so')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    ok(not pg.is_visible('#cmdDlg'), 'Esc closes')
    pg.click('#cmdBtn'); pg.wait_for_timeout(100)
    ok(pg.is_visible('#cmdDlg'), 'header Search button opens it too')
    pg.keyboard.press('Escape')
    # Hindi
    pg.evaluate("toggleLang()"); pg.wait_for_timeout(300)
    ok('संदर्भ' in pg.inner_text('#iconRail') and 'खोजें' in pg.inner_text('#cmdBtn'), 'rail and button relabel in Hindi')
    pg.keyboard.press('Control+k'); pg.fill('#cmdQ', 'बैकअप'); pg.wait_for_timeout(100)
    ok('बैकअप' in pg.inner_text('#cmdo0'), 'Hindi words find Hindi actions')
    pg.keyboard.press('Escape')
    ok('इसी डिवाइस' in pg.get_attribute('#devChip','aria-label'), 'chip in Hindi')
    pg.evaluate("toggleLang()"); pg.wait_for_timeout(300)
    # chip
    pg.click('#devChip'); pg.wait_for_timeout(150)
    t = pg.inner_text('#devDlg')
    ok('only in this browser' in t and 'outside India' in t and 'Crossref' in t and 'backup' in t.lower(), 'chip explains what stays and what leaves')
    pg.evaluate("document.getElementById('devDlg').close()")
    # one-time AI notice
    n = pg.evaluate("""()=>{localStorage.removeItem('appu_ai_notice_seen');let c=0;const o=showToast;showToast=m=>{if(/outside India/.test(m))c++};
        devAiNoticeOnce();devAiNoticeOnce();showToast=o;return [c,callAIRaw._dev===1]}""")
    ok(n == [1, True], 'AI notice shows once and is wired into every AI call: %s' % n)
    # polite urls and spacing
    u = pg.evaluate("""[apiPoliteUrl('https://api.crossref.org/works/10.1/x'),apiPoliteUrl('https://api.openalex.org/works?search=a#z'),
        apiPoliteUrl('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed'),apiPoliteUrl('https://api.crossref.org/works?mailto=a@b.c')]""")
    ok(u[0].endswith('?mailto=contact%40appuscholar.com') and u[1] == 'https://api.openalex.org/works?search=a&mailto=contact%40appuscholar.com#z'
       and 'mailto' not in u[2] and u[3].count('mailto') == 1, 'contact address added to Crossref and OpenAlex only: %s' % u)
    seen = []
    pg.route('**/api.crossref.org/**', lambda r: (seen.append((time.time(), r.request.url)), r.fulfill(status=200, body='{}', content_type='application/json')))
    pg.evaluate("Promise.all([1,2,3].map(i=>fetch('https://api.crossref.org/works/10.1037/x'+i).then(r=>r.text())))")
    gaps = [seen[i+1][0]-seen[i][0] for i in range(len(seen)-1)]
    ok(len(seen) == 3 and all(g > 0.15 for g in gaps) and all('mailto=' in s[1] for s in seen), 'three Crossref calls go out spaced and with the contact: %s' % [round(g, 2) for g in gaps])
    bad = [e for e in errs if e[0] == 'pageerror']
    ok(not bad, 'no page errors %s' % bad[:3])
    b.close()
    # phone: no rail; tablet: swipe moves between Tools and AI
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 420, 'height': 860})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    ok(not pg.is_visible('#iconRail') and pg.evaluate("getComputedStyle(document.body).paddingLeft") in ('0px', ''), 'no rail on a phone')
    ok(pg.is_visible('#devChip'), 'chip shown on a phone')
    b.close()
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 1180, 'height': 820})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    pg.evaluate("apGoTool('cite')"); pg.wait_for_timeout(200)
    sw = """dx=>{const el=dx<0?(document.querySelector('#toolShell .tool-panel.active')||document.getElementById('toolShell')):document.querySelector('.ai-pane');const r=el.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+40;
      const T=(cx)=>new Touch({identifier:1,target:el,clientX:cx,clientY:y});
      el.dispatchEvent(new TouchEvent('touchstart',{bubbles:true,touches:[T(x)],changedTouches:[T(x)]}));
      el.dispatchEvent(new TouchEvent('touchend',{bubbles:true,touches:[],changedTouches:[T(x+dx)]}));
      return document.querySelector('main').classList.contains('dock-ai')}"""
    on_phone = pg.evaluate("dockOn()")
    a = pg.evaluate(sw, -120); c = pg.evaluate(sw, 120)
    ok(on_phone and a is True and c is False, 'swipe left shows the AI suggestion, swipe right brings Tools back (%s %s %s)' % (on_phone, a, c))
    bad = [e for e in errs if e[0] == 'pageerror']
    ok(not bad, 'no page errors on tablet %s' % bad[:3])
    b.close()
sys.exit(1 if fails else 0)
