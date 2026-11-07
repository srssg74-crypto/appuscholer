"""Reading a paper without AI (build 2026.11.07a): facts, best sentences, batch queue. Pure functions, nothing wired to the screen yet."""
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
    J("window.__d=apBuild('s',AP_SAMPLE.slice(),'pdf');window.__f=apFacts(window.__d);window.__s=apStageSentences(window.__d,2)")
    ok(J("__f.n.recruited")==60 and J("__f.n.analysed")==58 and J("__f.n.groups.join()")=='29,29','sample size: 60 recruited, 58 analysed, groups 29 and 29')
    ok(J("__f.age.mean")==18.7 and J("__f.age.sd")==0.8,'mean age and SD')
    ok(J("__f.tests.join('|')").lower().find('independent-samples t-test')>=0 and 'Pearson' in J("__f.tests.join('|')"),'tests named: t-test and Pearson')
    ok(J("__f.scales.join('|')")=='Exam Worry Scale' and J("__f.alpha.join()")=='.86' and J("__f.items.join()")=='12','scale name, 12 items, alpha .86')
    ok(J("__f.effect.length")==1 and J("__f.effect[0].v")=='0.61','effect size d = 0.61 found once')
    c=lambda k: J("__f.checks.find(x=>x.k==='%s').v"%k)
    ok(c('ethics')=='yes' and c('consent')=='yes','ethics and consent are found')
    ok(c('power')=='no' and c('normality')=='no','"no power calculation" and "did not test for normality" read as not done')
    ok(c('prereg')=='','pre-registration is not found, so the cell stays empty')
    ok(J("__f.level")=='full','full text recognised')
    ok(all(J("(__s.%s||[]).length>0"%k) for k in ['gap','design','sample','measures','procedure','data','stats','results','limits','recs']),'every main stage gets at least one sentence from the sample paper')
    ok('randomised two-group design' in J("__s.design[0].text"),'design stage picks the design sentence')
    ok(J("Object.keys(__s).every(k=>__s[k].every(x=>__d.fullSq.indexOf(apSquash(x.text))>=0))"),'every picked sentence is word for word in the paper')
    J("window.__a=apBuild('a',[AP_SAMPLE[0].split('\\n\\n')[1]],'txt')")
    ok(J("apFacts(__a).level")=='abstract' and J("Object.keys(apStageSentences(__a)).filter(k=>apStageSentences(__a)[k].length).length")>=3,'abstract only: marked abstract, still fills a few stages')
    ok(J("Object.keys(apStageSentences(apBuild('x',['',' '],'pdf'))).every(k=>apStageSentences(apBuild('x',['',' '],'pdf'))[k].length===0)"),'a scanned (empty) PDF gives empty cells, no crash')
    ok(J("apSentences('Smith et al. (2019) found d = 0.45, p = .03. J. K. Rowling was not involved. See Fig. 2 for details.').length")==3,'sentence splitter keeps decimals, initials, et al. and Fig.')
    ok(J("apNumWord('sixty-four')")==64 and J("apNumWord('1,250')")==1250,'number words')
    lib="[{id:1,title:'Sleep and exam anxiety in students',abstract:'sleep anxiety',year:2024,cited:40},{id:2,title:'Cooking oil prices',abstract:'oil',year:2025},{id:3,title:'Bedtime routine and anxiety',abstract:'randomised trial of sleep routine and exam anxiety',year:2022,cited:5},{id:4,title:'Sleep anxiety retracted',abstract:'sleep anxiety',year:2023,retracted:true}]"
    ok(J("apQueue(%s,'sleep exam anxiety students',[],2).map(p=>p.id).join()"%lib)=='1,3','queue: best two first, retracted paper never offered')
    ok(J("apQueue(%s,'sleep exam anxiety students',[1,3],2).map(p=>p.id).join()"%lib)=='2','queue: next batch skips the ones already read')
    J("window.__seen=new Set()")
    r1=J("apBatchNovelty(['Routine lowered anxiety in students'],__seen).ratio"); r2=J("apBatchNovelty(['Routine lowered anxiety in students again'],__seen).ratio")
    ok(r1==1 and r2<0.5,'novelty hint falls when a batch repeats earlier words')
    ok(not errors,'no page errors: '+str(errors[:2]))
    b.close()
print('failures:',len(fails))
sys.exit(1 if fails else 0)
