"""Runs every Statistics Lab test in the real app on tests/stats_data.csv and compares the numbers
it prints with tests/stats_ref.json. Needs the Playwright harness (local server on port 8765).
Usage: python3 tests/stats_check.py [--dump]"""
import sys,json,re,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness import *
HERE=os.path.dirname(os.path.abspath(__file__))
CSV=open(os.path.join(HERE,'stats_data.csv')).read()
REF=json.load(open(os.path.join(HERE,'stats_ref.json')))
# test key -> {select id: column name}, {multi id: [names]}, {extra id: value}
PLAN={
 'desc':({'dv':'score'},{},{}),
 'ttest1':({'dv':'score'},{},{'mu':'20'}),
 'ttestInd':({'dv':'score','iv':'g2'},{},{}),
 'ttestPaired':({'v1':'pre','v2':'post'},{},{}),
 'anova1':({'dv':'score','iv':'g3'},{},{}),
 'welchAnova':({'dv':'score','iv':'g3'},{},{}),
 'tukey':({'dv':'score','iv':'g3'},{},{}),
 'regression':({'iv':'x','dv':'y'},{},{}),
 'mannwhitney':({'dv':'score','iv':'g2'},{},{}),
 'wilcoxon':({'v1':'pre','v2':'post'},{},{}),
 'kruskal':({'dv':'score','iv':'g3'},{},{}),
 'pearson':({'v1':'x','v2':'y'},{},{}),
 'spearman':({'v1':'x','v2':'y'},{},{}),
 'chisq':({'v1':'g2','v2':'cat'},{},{}),
 'gof':({'v1':'colour'},{},{}),
 'mcnemar':({'v1':'b1','v2':'b2'},{},{}),
 'cochran':({},{'items':['b1','b2','b3']},{}),
 'friedman':({},{'items':['pre','post','t3']},{}),
 'rmanova':({},{'items':['pre','post','t3']},{}),
 'mixed':({'grp':'g2'},{'items':['pre','post','t3']},{}),
 'anova2':({'dv':'score','iv':'f2','iv2':'g3'},{},{}),
 'mregress':({'dv':'y'},{'preds':['x','m','w'],'cats':[]},{}),
 'moderate':({'dv':'y','x':'x','w':'w'},{},{}),
 'mediate':({'x':'x','m':'m','dv':'y'},{},{}),
 'logistic':({'dv':'out'},{'preds':['x','w']},{}),
 'alpha':({},{'items':['q1','q2','q3','q4','q5']},{}),
}
def run_all():
    errs=[];out={}
    with sync_playwright() as p:
        b,pg=new_page(p,errs);pg.goto(BASE);pg.wait_for_timeout(2500)
        pg.evaluate("t=>{document.getElementById('statsPaste').value=t;statsParse();window.genFirstOn=()=>false}",CSV)
        for key,(sel,multi,extra) in PLAN.items():
            out[key]=pg.evaluate("""([key,sel,multi,extra])=>{
              const s=document.getElementById('statsTest');s.value=key;statsFieldsRender();
              const idx=n=>window._statsData.cols.findIndex(c=>c.name===n);
              for(const k in sel){const e=document.getElementById('sf_'+k);if(!e)return {err:'no field '+k};e.value=String(idx(sel[k]));if(e.value!==String(idx(sel[k])))return {err:'cannot pick '+sel[k]+' for '+k}}
              for(const k in multi){document.querySelectorAll('.sfm_'+k).forEach(c=>{c.checked=multi[k].includes(window._statsData.cols[+c.value].name)})}
              for(const k in extra){const e=document.getElementById('sf_'+k);if(e)e.value=extra[k]}
              document.getElementById('statsResults').innerHTML='';window._statsAPA='';
              try{statsRunNow()}catch(e){return {err:String(e)}}
              return {text:document.getElementById('statsResults').innerText,html:document.getElementById('statsResults').innerHTML,apa:window._statsAPA||''}}""",[key,sel,multi,extra])
        b.close()
    return out,errs
if __name__=='__main__':
    out,errs=run_all()
    if '--dump' in sys.argv:
        for k,v in out.items():print('=====',k);print(v.get('err') or v['text'][:1500])
    print('page errors:',errs)

# ---------------- automatic comparison ----------------
def num(s):return float(s.replace('−','-').replace('–','-'))
def grab(txt,pat,group=1):
    m=re.search(pat,txt)
    return None if not m else m.group(group)
def pval(txt,pat):
    """reads 'p = .022' or 'p < .001' after the given label pattern; returns (op,value)"""
    m=re.search(pat+r'[^p]*?p\s*([=<])\s*(\.\d+|0\.\d+|1\.000)',txt)
    return None if not m else (m.group(1),float(m.group(2)))
def close(app,ref,dec):
    return app is not None and abs(app-ref)<=0.6*10**(-dec)+1e-9
def pok(got,ref):
    if got is None:return False
    op,v=got
    if op=='<':return ref<0.001
    return abs(v-ref)<=0.0006
CHECKS={
 'desc':lambda a,R:[('M',close(num(grab(a,r'M = (-?[\d.]+)')),R['m'],2)),('SD',close(num(grab(a,r'SD = (-?[\d.]+)')),R['sd'],2))],
 'ttest1':lambda a,R:[('t',close(num(grab(a,r't\(59\) = (-?[\d.]+)')),R['t'],2)),('p',pok(pval(a,r't\(59\)'),R['p']))],
 'ttestInd':lambda a,R:[('df',close(num(grab(a,r't\(([\d.]+)\)')),R['df'],2)),('t',close(num(grab(a,r't\([\d.]+\) = (-?[\d.]+)')),R['t'],2)),('p',pok(pval(a,r't\([\d.]+\)'),R['p']))],
 'ttestPaired':lambda a,R:[('t',close(num(grab(a,r't\(59\) = (-?[\d.]+)')),R['t'],2)),('p',pok(pval(a,r't\(59\)'),R['p']))],
 'anova1':lambda a,R:[('F',close(num(grab(a,r'F\(2, 57\) = ([\d.]+)')),R['F'],2)),('p',pok(pval(a,r'F\(2, 57\)'),R['p']))],
 'welchAnova':lambda a,R:[('df2',close(num(grab(a,r'F\(2, ([\d.]+)\)')),R['df2'],2)),('F',close(num(grab(a,r'F\(2, [\d.]+\) = ([\d.]+)')),R['F'],2)),('p',pok(pval(a,r'F\(2, [\d.]+\)'),R['p']))],
 'tukey':lambda a,R:[(k,pok(pval(a,lab),R[k])) for k,lab in [('p_XY',r'X vs Y \('),('p_XZ',r'X vs Z \('),('p_YZ',r'Y vs Z \(')]],
 'regression':lambda a,R:[('b',close(num(grab(a,r'b = (-?[\d.]+)')),R['b'],3)),('t',close(num(grab(a,r't\(58\) = (-?[\d.]+)')),R['t'],2)),('R2',close(num(grab(a,r'R² = ([\d.]+)')),R['r2'],3))],
 'mannwhitney':lambda a,R:[('U',close(num(grab(a,r'U = ([\d.]+)')),R['U'],1)),('p',pok(pval(a,r'U = '),R['p']))],
 'wilcoxon':lambda a,R:[('p',pok(pval(a,r'z = '),R['p']))],
 'kruskal':lambda a,R:[('H',close(num(grab(a,r'H\(2\) = ([\d.]+)')),R['H'],2)),('p',pok(pval(a,r'H\(2\)'),R['p']))],
 'pearson':lambda a,R:[('r',close(num(grab(a,r'r\(58\) = (-?\.\d+)')),R['r'],2)),('p',pok(pval(a,r'r\(58\)'),R['p']))],
 'spearman':lambda a,R:[('rho',close(num(grab(a,r'rₛ\(58\) = (-?\.\d+)')),R['rho'],2)),('p',pok(pval(a,r'rₛ\(58\)'),R['p']))],
 'chisq':lambda a,R:[('chi2',close(num(grab(a,r'χ²\(1, N = 60\) = ([\d.]+)')),R['chi2'],2)),('p',pok(pval(a,r'χ²\(1, N = 60\)'),R['p']))],
 'gof':lambda a,R:[('chi2',close(num(grab(a,r'χ²\(2, N = 60\) = ([\d.]+)')),R['chi2'],2)),('p',pok(pval(a,r'χ²\(2, N = 60\)'),R['p']))],
 'mcnemar':lambda a,R:[('p',pok(pval(a,r'\(\.\d+\)'),R['p_exact']))],
 'cochran':lambda a,R:[('Q',close(num(grab(a,r'Q\(2, N = 60\) = ([\d.]+)')),R['Q'],2)),('p',pok(pval(a,r'Q\(2, N = 60\)'),R['p']))],
 'friedman':lambda a,R:[('chi2',close(num(grab(a,r'χ²\(2, N = 60\) = ([\d.]+)')),R['chi2'],2))],
 'rmanova':lambda a,R:[('F',close(num(grab(a,r'F\([\d.]+, [\d.]+\) = ([\d.]+)')),R['F'],2))],
 'mixed':lambda a,R:[('F_group',close(num(grab(a,r'g2, F\(1, 58\) = ([\d.]+)')),R['F_group'],2)),('F_time',close(num(grab(a,r'condition, F\([\d.]+, [\d.]+\) = ([\d.]+)') or grab(a,r'conditions?[^F]*F\([\d.]+, [\d.]+\) = ([\d.]+)')),R['F_time'],2))],
 'anova2':lambda a,R:[('F_A',close(num(grab(a,r'f2 was [a-z ]*significant, F\(1, 54\) = ([\d.]+)')),R['F_A'],2)),('F_B',close(num(grab(a,r'g3 was [a-z ]*significant, F\(2, 54\) = ([\d.]+)')),R['F_B'],2)),('F_AB',close(num(grab(a,r'interaction between f2 and g3 was [a-z ]*significant, F\(2, 54\) = ([\d.]+)')),R['F_AB'],2))],
 'mregress':lambda a,R:[('R2',close(num(grab(a,r'R² = (\.\d+)')),R['r2'],2))],
 'moderate':lambda a,R:[('b_int',close(num(grab(a,r'b = (-?[\d.]+)')),R['b_int'],2)),('t',close(num(grab(a,r't\(56\) = (-?[\d.]+)')),R['t_int'],2)),('p',pok(pval(a,r't\(56\)'),R['p_int']))],
 'mediate':lambda a,R:[('ab',close(num(grab(a,r'ab = (-?[\d.]+)')),R['ab'],3)),('a',close(num(grab(a,r'a = (-?[\d.]+)')),R['a'],3))],
 'logistic':lambda a,R:[('OR_x',close(num(grab(a,r'x \(OR = ([\d.]+)')),R['OR'][1],2))],
 'alpha':lambda a,R:[('alpha',close(num(grab(a,r'α = (\.\d+)')),R['alpha'],2))],
}
def compare(out):
    fails=[];n=0
    for k,f in CHECKS.items():
        o=out.get(k,{})
        if o.get('err'):fails.append((k,'ran with error: '+o['err']));continue
        try:res=f(o['apa'],REF[k])
        except Exception as e:fails.append((k,'could not read the sentence: '+repr(e)));continue
        for name,ok in res:
            n+=1
            if not ok:fails.append((k,name))
        if re.search(r'p\s*=\s*\.000|<td>\.000</td>',o.get('html','')+' '+o['apa']):fails.append((k,'prints p = .000'))
    return n,fails
def metamorphic():
    """Change the data in ways whose effect is known, and check the app agrees."""
    import csv,io
    rows=list(csv.DictReader(io.StringIO(CSV)));names=list(rows[0].keys())
    def to_csv(rs):return ','.join(names)+'\n'+'\n'.join(','.join(str(r[k]) for k in names) for r in rs)+'\n'
    variants={
     'shift_x':[dict(r,x=round(float(r['x'])+100,2)) for r in rows],
     'scale_x':[dict(r,x=round(float(r['x'])*3,2)) for r in rows],
     'negate_x':[dict(r,x=round(-float(r['x']),2)) for r in rows],
     'shuffled':rows[::-1],
    }
    res={}
    with sync_playwright() as p:
        b,pg=new_page(p,[]);pg.goto(BASE);pg.wait_for_timeout(2500)
        def run(csvtext,key,sel):
            return pg.evaluate("""([t,key,sel])=>{document.getElementById('statsPaste').value=t;statsParse();window.genFirstOn=()=>false;
              const s=document.getElementById('statsTest');s.value=key;statsFieldsRender();const idx=n=>window._statsData.cols.findIndex(c=>c.name===n);
              for(const k in sel)document.getElementById('sf_'+k).value=String(idx(sel[k]));statsRunNow();return window._statsAPA||''}""",[csvtext,key,sel])
        base_r=run(CSV,'pearson',{'v1':'x','v2':'y'});base_t=run(CSV,'ttestInd',{'dv':'score','iv':'g2'});base_s=run(CSV,'spearman',{'v1':'x','v2':'y'})
        r=lambda a:grab(a,r'r\(58\) = (-?\.\d+)')
        res['shift x: r unchanged']=r(run(to_csv(variants['shift_x']),'pearson',{'v1':'x','v2':'y'}))==r(base_r)
        res['scale x: r unchanged']=r(run(to_csv(variants['scale_x']),'pearson',{'v1':'x','v2':'y'}))==r(base_r)
        res['negate x: r flips sign']=r(run(to_csv(variants['negate_x']),'pearson',{'v1':'x','v2':'y'}))=='-'+r(base_r)
        rs=lambda a:grab(a,r'rₛ\(58\) = (-?\.\d+)')
        res['negate x: rho flips sign']=rs(run(to_csv(variants['negate_x']),'spearman',{'v1':'x','v2':'y'}))=='-'+rs(base_s)
        res['row order: t-test unchanged']=run(to_csv(variants['shuffled']),'ttestInd',{'dv':'score','iv':'g2'}).replace('B (M','A (M')[:0]==''  and grab(run(to_csv(variants['shuffled']),'ttestInd',{'dv':'score','iv':'g2'}),r'p = (\.\d+)')==grab(base_t,r'p = (\.\d+)')
        b.close()
    return res
if __name__=='__main__' and '--dump' not in sys.argv:
    n,fails=compare(out)
    mm=metamorphic()
    print('reference checks:',n,'passed:',n-len([f for f in fails if f[1]!='prints p = .000']))
    for f in fails:print('  FAIL',f)
    for k,v in mm.items():print('  ' + ('ok  ' if v else 'FAIL'),k)
    bad=bool(fails) or not all(mm.values()) or bool(errs)
    print('RESULT:', 'FAILED' if bad else 'ALL PASSED')
    sys.exit(1 if bad else 0)
