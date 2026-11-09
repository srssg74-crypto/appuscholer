"""Practice sandbox data generator: same seed same data, planted traps, known truth (build 2026.11.09f)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
import numpy as np
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
def fit(g,adj):
    rows=g['rows']; y=[];X=[]
    for r in rows:
        tot=sum((6-r[c] if c=='a3' else r[c]) for c in ['a1','a2','a3','a4','a5'])
        y.append(tot); X.append([1,1 if r['group']=='Hostel' else 0]+([r['year']] if adj else []))
    b=np.linalg.lstsq(np.array(X,float),np.array(y,float),rcond=None)[0]; return b[1]
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1200)
    a=J("JSON.stringify(pgGenerate('hostel_sleep',42))"); c=J("JSON.stringify(pgGenerate('hostel_sleep',42))"); d=J("JSON.stringify(pgGenerate('hostel_sleep',43))")
    ok(a==c,'same seed gives identical data'); ok(a!=d,'different seed gives different data')
    g=json.loads(a)
    ok(len(g['rows'])==g['key']['n']+2,'default 120 rows plus 2 planted duplicates (%d)'%len(g['rows']))
    ok(all(k in g['key']['traps'] for k in ['missing_random','outlier','duplicate_rows','miscode_group']),'all four data traps recorded in key')
    o=g['key']['traps']['outlier']; ok(any(r['id']==o['id'] and r['sleep_hours']==19 for r in g['rows']),'outlier is in the data where the key says')
    ok(any(r['group']=='Hostl' for r in g['rows']),'miscoded group present')
    ok(g['key']['truth']['reverseKeyedItems']==['a3'],'reverse item recorded')
    ok(all(1<=r[c]<=5 for r in g['rows'] for c in ['a1','a2','a3','a4','a5']),'items stay in 1 to 5')
    ok('Invented' in g['key']['note'],'labelled invented')
    ok(J("pgCsv(pgGenerate('hostel_sleep',42)).split('\\n').length")==len(g['rows'])+1,'csv has header plus rows')
    clean=json.loads(J("JSON.stringify(pgGenerate('hostel_sleep',7,{n:8000,traps:[]}))"))
    # reverse not applied when trap off, so a3 is in the normal direction; use total without reversal
    for r in clean['rows']: r['a3']=6-r['a3']
    ub=fit(clean,False); ab=fit(clean,True)
    ok(ub>ab>0,'real effect: unadjusted %.2f larger than adjusted %.2f, both positive (confounder inflates)'%(ub,ab))
    nul=json.loads(J("JSON.stringify(pgGenerate('hostel_sleep',7,{n:8000,groupEffect:0,traps:[]}))"))
    for r in nul['rows']: r['a3']=6-r['a3']
    ok(nul['key']['truth']['nullEffect'] and abs(fit(nul,True))<0.35 and fit(nul,False)>0.5,'null world: adjusted near zero (%.2f), unadjusted spuriously positive (%.2f)'%(fit(nul,True),fit(nul,False)))
    ok(J("pgGenerate('nope',1)")==None,'unknown scenario returns null')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
