"""Stats Lab: plain-language note without AI, AI one click away (build 2026.11.08c)."""
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
    J("showTool('stats');window.__ai=0;window.callAI=async function(){window.__ai++;return 'AI text.'}")
    J("statsResultsShow('<p>t = 4.27</p>','A paired-samples t-test showed a significant difference, t(29) = 4.27, p < .001, d = 0.78.')")
    n0=J("window.__ai")
    J("statsExplain()")
    t=J("document.getElementById('statsPlain').textContent")
    ok('statistically significant' in t and 'medium effect' in t and 'no AI' in t,'t-test: significance and medium d, labelled as no AI')
    ok(J("window.__ai")==n0,'no AI call for the quick note')
    ok('experiment' not in t and 'cause' not in t,'no claim about design or cause')
    J("statsResultsShow('<p>x</p>','A one-way ANOVA showed a non-significant effect, F(2, 57) = 1.84, p = .168, η² = 0.061.')")
    J("statsExplain()")
    t=J("document.getElementById('statsPlain').textContent")
    ok('not statistically significant' in t and '6%' in t and 'medium' in t,'ANOVA: not significant, 6%, medium')
    J("statsResultsShow('<p>x</p>','There was a moderate positive correlation, which was statistically significant, r(58) = .41, p = .001.')")
    J("statsExplain()")
    ok('correlation of .41 is medium' in J("document.getElementById('statsPlain').textContent"),'correlation size label')
    J("statsResultsShow('<p>x</p>','Internal consistency was α = .86 (k = 12 items, N = 60).')")
    J("statsExplain()")
    ok('no p-value' in J("document.getElementById('statsPlain').textContent"),'no p-value: says so and points to AI')
    J("statsResultsShow('<p>x</p>','A paired-samples t-test showed a significant difference, t(29) = 4.27, p < .001, d = 0.78.')")
    J("statsExplain()"); n1=J("window.__ai"); J("statsExplainAI()"); pg.wait_for_timeout(300)
    ok(J("window.__ai")==n1+1 and 'AI text.' in J("document.getElementById('statsSentence').textContent"),'AI button still works')
    ok(not errors,'no page errors: %s'%errors)
    b.close()
print('failures:',len(fails))
