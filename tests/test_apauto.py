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
    ok(J("__f.level")=='full' and J("__f.kind")=='research','full text recognised as a research article')
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

    # real-paper lessons (build 2026.11.08a): intro numbers, numbered headings, running headers, not-a-paper files
    pages=[
     "Journal of Examples 12 (3)\n1\nABSTRACT\nMethods: The study involved 107 women aged 30-45 years at a crisis centre.\nINTRODUCTION\nAccording to estimates, approximately 736 million women worldwide have experienced violence by a partner in their lifetime. The present study addresses this gap by examining stress and well-being among survivors. Future longitudinal studies are needed.",
     "Journal of Examples 12 (3)\n2\n2. METHODS\n2.1. Participants\nThe study included 107 women aged 30-45 years. Oral informed consent was obtained from each participant.\n2.2. Measures\nWell-being was assessed using the PERMA-Profiler and stress with the Perceived Stress Scale.",
     "Journal of Examples 12 (3)\n3\n2.7. Statistical Analysis\nStatistical analyses were performed using IBM SPSS Statistics, version 27. Pearson's correlation analysis and multiple linear regression analysis were conducted to examine associations.\n3. RESULTS\nThe correlation between stress and well-being was strong, r = -0.52, p < 0.01, in this sample of women.",
     "Journal of Examples 12 (3)\n4\nDISCUSSION\nThe relatively small sample may have limited the statistical power of the analyses. Future research should use larger samples.\nREFERENCES\n1. Someone A. Violence in 2019. 107 women were studied here."]
    J("window.__r=apBuild('r',%s,'pdf');window.__rf=apFacts(__r);window.__rs=apStageSentences(__r,2)"%__import__('json').dumps(pages))
    ok(J("__rf.n.recruited")==107,'sample size comes from the methods, not from "736 million women" in the introduction')
    ok(J("__rf.ageRange.join('-')")=='30-45','age range 30-45')
    ok('multiple linear regression' in J("__rf.tests.join('|')") and 'SPSS' in J("__rf.software.join()") and "Pearson's correlation" in J("__rf.tests.join('|')"),'tests and software from a numbered "2.7. Statistical Analysis" heading')
    ok('PERMA-Profiler' in J("__rf.scales.join('|')") and 'Perceived Stress Scale' in J("__rf.scales.join('|')"),'scales: PERMA-Profiler and Perceived Stress Scale')
    ok(J("__rf.design.join()").find('longitudinal')<0,'"Future longitudinal studies" is not read as the design')
    ok('Statistical analyses were performed' in J("(__rs.stats[0]||{}).text||''"),'stats stage picks the sentence under the numbered heading')
    ok('addresses this gap' in J("(__rs.gap[0]||{}).text||''"),'gap stage picks "the present study addresses this gap"')
    ok(J("Object.keys(__rs).every(k=>__rs[k].every(x=>x.text.indexOf('Journal of Examples')<0))"),'running page headers are dropped')
    ok(J("Object.keys(__rs).every(k=>__rs[k].every(x=>x.text.indexOf('Violence in 2019')<0))"),'nothing after References is used')
    ok(J("apFacts(apBuild('h',['MENTAL WELLNESS HANDBOOK\\n'+Array(40).join('A guide to looking after yourself. Take a walk each day and talk to a friend when you feel low. Keep a diary of how your week went and what helped you most. ')],'pdf')).kind")=='notpaper','a handbook is marked as not a paper')

    # second round of lessons (build 2026.11.08a): journal heading styles, capital P, mixed models, fMRI software
    pages2=[
     "1 | INTRODUCTION\nPeople often delay tasks. We hypothesized that procrastination relates to effort cost.\n2 | METHODS\n2.1 | Participants\nThirty-two students (9 males; mean age 21.1 years, SD = 1.65) took part. All gave informed consent.",
     "2.5 | Statistical analysis\nWe fitted mixed linear models and compared them with a likelihood ratio test. Data were analyzed using SPM12.\n3 | BEHAVIORAL RESULTS\nProcrastination was linked to aversiveness (t = \u22123.64, P < 0.001, N = 232), and to value (r = -0.40, P = 0.01).\n5 | DISCUSSION\nThis suggests a role for effort.\nACKNOWLEDGMENTS\nThanks to all. Zhang T. A meta-analysis of delay. Brain 2019.",
     "Journal 5\n","Journal 6\n"]
    J("window.__q=apBuild('q',%s,'pdf');window.__qf=apFacts(__q);window.__qs=apStageSentences(__q,2)"%__import__('json').dumps(pages2))
    ok(J("__qf.kind")=='research','pipe-style headings ("2 | METHODS", "3 | BEHAVIORAL RESULTS") give a research article')
    ok('mixed linear models' in J("__qf.tests.join('|')") and 'SPM12' in J("__qf.software.join()"),'mixed linear models and SPM12 are found')
    ok(J("__qf.pcount")>=2,'capital P in "P < 0.001" is counted')
    ok(J("__qf.age.mean")==21.1 and J("__qf.n.recruited")==32,'thirty-two students, mean age 21.1')
    ok('meta-analysis' not in J("__qf.design.join()"),'text after the Acknowledgments heading is not read')
    ok(not errors,'no page errors: '+str(errors[:2]))
    b.close()
print('failures:',len(fails))
sys.exit(1 if fails else 0)
