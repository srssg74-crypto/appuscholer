"""Meta-analysis B5: a numbers table for each included study with CSV export (build 2026.11.08k)."""
import sys, os, json
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
    J("window.confirm=()=>true;window.callAI=async function(){return ''}")
    J("openSaveAsProject();document.getElementById('sapName').value='Meta';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("citSaveLib([{author:'Lee, A.; Wong, B.',year:'2019',title:'Sleep and grades',type:'Journal article',style:'apa',scr:{st:'included',why:'core'}},{author:'Rao, C.',year:'2021',title:'Sleep in school',type:'Journal article',style:'apa',scr:{st:'excluded',why:'x',rd:'2'}}])")
    T=lambda: J("document.getElementById('subMain').innerText")
    for ty in ('narr','scop','sys'):
        J("wPatch('B1','type','%s')"%ty); J("subOpen('lit','B5')")
        ok('Numbers from each study' not in T(),'%s: numbers table hidden'%ty)
    J("wPatch('B1','type','meta')"); J("subOpen('lit','B5')")
    ok('Numbers from each study' in T(),'meta-analysis: numbers table shown')
    J("logFromLibrary('effects')")
    rows=json.loads(J("JSON.stringify(logRows(studyGet(),'effects'))"))
    ok(len(rows)==1 and 'Lee' in rows[0]['paper'],'only the included paper comes from the library')
    J("logCell('effects',0,'es','-0.32');logCell('effects',0,'lo','-0.55');logCell('effects',0,'hi','-0.09');logCell('effects',0,'measure','Hedges g');logCell('effects',0,'n','240');logRefresh()")
    ok('All rows are complete' in T(),'negative effect size accepted and rows complete')
    J("logAdd('effects');logCell('effects',1,'measure','Pearson r');logCell('effects',1,'es','0.4');logCell('effects',1,'lo','0.5');logCell('effects',1,'hi','0.6');logRefresh()")
    t=T()
    ok('Different measures are mixed' in t and '1 row(s)' in t,'mixed measures and an interval that misses the effect are flagged')
    ok(J("document.querySelector('#subMain table.log-tbl input[type=number][step=any]')!==null"),'effect size box takes decimals and negatives')
    csv=J("(function(){var q=v=>'\"'+String(v==null?'':v).replace(/\"/g,'\"\"')+'\"',d=logDef('effects'),r=logRows(studyGet(),'effects');return [d.cols.map(c=>q(c[1])).join(',')].concat(r.map(x=>d.cols.map(c=>q(x[c[0]])).join(','))).join('\\n')})()")
    ok('Effect size' in csv.split('\n')[0] and '-0.32' in csv,'CSV has the header and the numbers')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
