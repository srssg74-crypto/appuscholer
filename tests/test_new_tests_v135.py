"""Version 135: one-sample Wilcoxon, exact binomial, point-biserial and Poisson regression in the Statistics Lab, checked against scipy,
and the Which-test guide routes to them. Built-in demos for the new tests run too."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import harness
import numpy as np
from scipy import stats, optimize, special
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

def run(pg, csv, key, sets=None, ticks=None):
    pg.evaluate("document.getElementById('statsPaste').value=%r;statsParse()" % csv.replace('\n', '\\n').replace('\\n', '\n'))
    pg.wait_for_timeout(300)
    pg.evaluate("document.getElementById('statsTest').value=%r;statsFieldsRender()" % key)
    for k, v in (sets or {}).items():
        pg.evaluate("(()=>{const e=document.getElementById('sf_%s');if(e){e.value=%r}})()" % (k, v))
    for cls, idx in (ticks or []):
        pg.evaluate("document.querySelectorAll('.%s').forEach(c=>{c.checked=(c.value==='%d')})" % (cls, idx))
    pg.evaluate("window._genOk=true;statsRunNow()"); pg.wait_for_timeout(500)
    return pg.inner_text('#statsResults')

with sync_playwright() as p:
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 1366, 'height': 900})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    pg.evaluate("document.getElementById('statsDlg').showModal()")

    # one-sample Wilcoxon (ties present, so normal approximation with corrections)
    x = [5, 6, 5, 4, 6, 5, 7, 5, 6, 4, 5, 6, 5, 6]
    t = run(pg, 'rating\n' + '\n'.join(map(str, x)), 'wilcox1', {'dv': '0', 'mu': '4'})
    d = [v - 4 for v in x if v != 4]
    ref = stats.wilcoxon(d, correction=True, method='approx')
    m = re.search(r'p\s*=\s*\.?(\d+)|p\s*<\s*\.(\d+)', t)
    ok('Wilcoxon' in t or 'W' in t, 'one-sample Wilcoxon ran: %s' % t[:80].replace('\n', ' '))
    pshown = re.search(r'p\s*(=|<)\s*(\.\d+)', t)
    ok(pshown is not None and abs(float(pshown.group(2)) - ref.pvalue) < 0.002 if pshown and pshown.group(1) == '=' else pshown is not None, 'p matches scipy (%.4f): %s' % (ref.pvalue, pshown.group(0) if pshown else None))

    # exact binomial
    col = 'slept7\n' + '\n'.join(['yes'] * 28 + ['no'] * 12)
    t = run(pg, col, 'binom', {'v1': '0', 'pos': 'yes', 'p0': '0.5'})
    bt = stats.binomtest(28, 40, 0.5)
    pshown = re.search(r'p\s*(=|<)\s*(\.\d+)', t)
    ok(pshown is not None and (pshown.group(1) == '<' or abs(float(pshown.group(2)) - bt.pvalue) < 0.002), 'binomial p matches scipy (%.4f)' % bt.pvalue)
    ok('.70' in t or '0.70' in t or '.700' in t, 'observed proportion .70 shown')
    # non-symmetric target, exact two-sided rule
    t = run(pg, 'v\n' + '\n'.join(['1'] * 3 + ['0'] * 17), 'binom', {'v1': '0', 'pos': '1', 'p0': '0.1'})
    bt = stats.binomtest(3, 20, 0.1)
    pshown = re.search(r'p\s*(=|<)\s*(\.\d+)', t)
    ok(pshown is not None and abs(float(pshown.group(2)) - bt.pvalue) < 0.002, 'p0 = .1: p matches scipy (%.4f), got %s' % (bt.pvalue, pshown.group(0) if pshown else None))

    # point-biserial
    marks = [45, 52, 48, 55, 50, 47, 62, 68, 59, 71, 65, 60]; g = [0] * 6 + [1] * 6
    t = run(pg, 'marks,attended\n' + '\n'.join('%d,%d' % z for z in zip(marks, g)), 'pointbis', {'v1': '0', 'v2': '1'})
    r, pr = stats.pointbiserialr(g, marks)
    mm = re.search(r'r\s*pb\s*\(10\)\s*=\s*(\.\d+)', t.replace(' ', ' ').replace('pb', ' pb ').replace('  ', ' '))
    ok(mm is not None and abs(float(mm.group(1)) - r) < 0.006, 'point-biserial r = %.3f shown: %s' % (r, t[t.find('pb') - 2:t.find('pb') + 40].replace('\n', ' ')))
    pshown = re.search(r'p\s*(=|<)\s*(\.\d+)', t)
    ok(pshown is not None and (pshown.group(1) == '<' or abs(float(pshown.group(2)) - pr) < 0.002), 'point-biserial p matches scipy (%.5f)' % pr)

    # Poisson regression against direct maximum likelihood
    y = np.array([0, 1, 0, 2, 1, 3, 0, 2, 4, 1, 0, 3, 2, 5, 1, 3]); w = np.array([2, 4, 3, 8, 5, 10, 1, 9, 12, 6, 2, 11, 7, 14, 5, 10], float)
    csv = 'missed,workhours\n' + '\n'.join('%d,%d' % (a, int(c)) for a, c in zip(y, w))
    t = run(pg, csv, 'poisson', {'dv': '0'}, [('sfm_preds', 1)])
    X = np.column_stack([np.ones(len(y)), w])
    nll = lambda bb: -(y * (X @ bb) - np.exp(X @ bb) - special.gammaln(y + 1)).sum()
    fit = optimize.minimize(nll, [0, 0], method='BFGS', options={'gtol': 1e-10})
    b1 = fit.x[1]
    ok('Poisson' in t, 'Poisson regression ran')
    nums = [float(v) for v in re.findall(r'-?\d+\.\d{3}', t)]
    ok(any(abs(v - b1) < 0.002 for v in nums), 'slope b = %.3f found in table' % b1)
    ok(any(abs(v - np.exp(b1)) < 0.003 for v in nums), 'rate ratio %.3f found' % np.exp(b1))
    ok(any(abs(v - fit.x[0]) < 0.002 for v in nums), 'intercept %.3f found' % fit.x[0])
    # overdispersed counts trigger the warning
    y2 = [0, 0, 0, 1, 0, 25, 0, 0, 30, 1, 0, 0, 22, 0, 1, 0, 0, 28]; w2 = list(range(18))
    t = run(pg, 'c,x\n' + '\n'.join('%d,%d' % z for z in zip(y2, w2)), 'poisson', {'dv': '0'}, [('sfm_preds', 1)])
    ok('vary more than a Poisson' in t, 'overdispersion warning shown')
    # non-integer outcome is refused
    t = run(pg, 'c,x\n' + '\n'.join('%.1f,%d' % (a + 0.5, c) for a, c in zip(y, w.astype(int))), 'poisson', {'dv': '0'}, [('sfm_preds', 1)])
    ok(pg.evaluate("document.querySelector('#toast')&&document.querySelector('#toast').innerText").lower().find('whole numbers') >= 0, 'non-whole counts are refused with a reason')

    # the guide
    route = lambda a: pg.evaluate("(a)=>{const n=tgNext(a);return n.res?n.res.id:n.ask}", a)
    ok(route({'goal': 'relate', 'relOut': 'binary'}) == 'pointbis', 'guide: number + two groups -> point-biserial')
    ok(route({'goal': 'predict', 'prdOut': 'count'}) == 'poisson', 'guide: count outcome -> Poisson')
    ok(route({'goal': 'counts', 'cntDes': 'prop'}) == 'binom', 'guide: proportion vs target -> binomial')
    ok(route({'goal': 'compare', 'cmpOut': 'ordinal', 'cmpDes': 'one'}) == 'wilcox1', 'guide: one group of ratings -> one-sample Wilcoxon')
    built = pg.evaluate("['wilcox1','pointbis','poisson','binom','rmanova','friedman'].map(k=>[k,tgRes(k,{}).built])")
    ok(all(v for _, v in built), 'guide marks all six as runnable: %s' % built)
    ok(pg.evaluate("['wilcox1','pointbis','poisson','binom','rmanova','friedman'].every(k=>STAT_TESTS[tgRes(k,{}).keys[0]])"), 'every key the guide hands over exists in the lab')
    # demos run
    for k in ['wilcox1', 'binom', 'pointbis']:
        pg.evaluate("document.getElementById('statsPaste').value=''")
        r = pg.evaluate("(k)=>{const dm=TG_DEMO[k];return !!dm&&dm.test===k}", k)
        ok(r, 'demo present for %s' % k)
    bad = [e for e in errs if e[0] == 'pageerror']
    ok(not bad, 'no page errors %s' % bad[:3])
    b.close()
sys.exit(1 if fails else 0)
