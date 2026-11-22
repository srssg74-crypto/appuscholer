"""Accessibility check with Deque's free, open-source axe-core (MPL-2.0), run on the test copy only.
Every main screen, at laptop, tablet and phone width, in English and Hindi, against WCAG 2.2 AA.
The pages hold only a made-up sample project; no student work is ever loaded.
Usage: AXE_JS=path/to/axe.min.js python3 tests/a11y_axe.py > report.md   (prints Markdown, writes a11y.json)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright

AXE = os.environ.get('AXE_JS', 'node_modules/axe-core/axe.min.js')
setup = "saveProjectsList([{id:'p1',name:'Sleep quality and exam stress in first-year students (sample)',stage:'design',status:'active'}]);LS.set('appu_active_project','p1');"
cases = [('Home', "apHomeShow()"), ('Literature', "apGoTool('research')"), ('Design & ethics', "apGoTool('design')"),
         ('Statistics', "apGoTool('stats')"), ('Writing', "apGoTool('style')"), ('Review', "apGoStage('review')")]
sizes = [(1366, 768, 'laptop'), (1180, 820, 'tablet'), (400, 860, 'phone')]
RUN = """async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']},resultTypes:['violations']});
  return r.violations.map(v=>({id:v.id,impact:v.impact,help:v.help,url:v.helpUrl,n:v.nodes.length,ex:v.nodes.slice(0,3).map(n=>n.target.join(' ')+' :: '+(n.failureSummary||'').split('\\n').slice(1,2).join('').trim())}))}"""

found = {}
with sync_playwright() as p:
    for (w, h, size) in sizes:
        for lang in ['en', 'hi']:
            errs = []
            b, pg = harness.new_page(p, errs, {'width': w, 'height': h})
            pg.goto(harness.BASE); pg.wait_for_timeout(1500); pg.evaluate(setup)
            if lang == 'hi': pg.evaluate("toggleLang()"); pg.wait_for_timeout(300)
            pg.add_script_tag(path=AXE)
            for name, js in cases:
                pg.evaluate(js); pg.wait_for_timeout(500)
                for v in pg.evaluate(RUN):
                    k = v['id']
                    e = found.setdefault(k, {'impact': v['impact'], 'help': v['help'], 'url': v['url'], 'where': set(), 'count': 0, 'ex': []})
                    e['where'].add('%s / %s / %s' % (name, size, lang)); e['count'] += v['n']
                    for x in v['ex']:
                        if len(e['ex']) < 4 and x not in e['ex']: e['ex'].append(x)
            b.close()

order = {'critical': 0, 'serious': 1, 'moderate': 2, 'minor': 3}
rows = sorted(found.items(), key=lambda kv: (order.get(kv[1]['impact'], 9), -kv[1]['count']))
json.dump({k: dict(v, where=sorted(v['where'])) for k, v in rows}, open('a11y.json', 'w'), indent=1, ensure_ascii=False)
print('## Accessibility check (axe-core, WCAG 2.2 AA)\n')
print('Screens: %d · sizes: laptop, tablet, phone · languages: English, Hindi · test copy with sample data only.\n' % len(cases))
if not rows:
    print('No problems found.')
for k, v in rows:
    print('### %s: %s (%s, %d elements)' % (k, v['help'], v['impact'], v['count']))
    print('- Where: %s' % ', '.join(sorted(v['where'])[:8]) + (' and more' if len(v['where']) > 8 else ''))
    for x in v['ex']:
        print('- `%s`' % x.replace('`', "'")[:220])
    print('- Rule: %s\n' % v['url'])
