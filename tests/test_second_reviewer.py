"""Second reviewer, blind (build 2026.11.08l): reviewer file, answers import, disagreements, Cohen's kappa."""
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
    J("window.confirm=()=>true")
    # kappa maths: textbook 2x2 (a=20,b=5,c=10,d=15) -> po .7, pe .5, kappa .4
    pairs=[['i','i']]*20+[['i','e']]*5+[['e','i']]*10+[['e','e']]*15
    k=json.loads(J("JSON.stringify(b3Kappa(%s))"%json.dumps(pairs)))
    ok(abs(k['po']-0.7)<1e-9 and abs(k['pe']-0.5)<1e-9 and abs(k['k']-0.4)<1e-9,'kappa .40 for the textbook table %s'%k)
    ok(json.loads(J("JSON.stringify(b3Kappa([['i','i'],['e','e']]))"))['k']==1,'perfect agreement is 1')
    ok(json.loads(J("JSON.stringify(b3Kappa([['i','i'],['i','i']]))"))['k']==1,'everyone includes everything: 1, no divide by zero')
    ok(json.loads(J("JSON.stringify(b3Kappa([]))"))['k'] is None,'no pairs: no kappa')
    J("openSaveAsProject();document.getElementById('sapName').value='Second';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("citSaveLib([%s])"%','.join("{author:'A, B.',year:'2020',title:'Paper %d',type:'Journal article',style:'apa',abs:'Abstract %d </script> text',scr:{st:'%s',why:'r'}}"%(i,i,st) for i,st in enumerate(['included','included','excluded','excluded','toread'])))
    T=lambda: J("document.getElementById('subMain').innerText")
    J("wPatch('B1','type','narr')"); J("subOpen('lit','B3')")
    ok('Second reviewer' not in T(),'narrative: second reviewer part hidden')
    J("wPatch('B1','type','sys')"); J("subOpen('lit','B3')")
    ok('Second reviewer' in T() and 'recommended' in T() and 'Make the file for the reviewer (5 papers)' in T(),'systematic: shown as recommended with the paper count')
    # the reviewer page
    html=J("b3ReviewerHTML(citGetLib().map(function(d){return{c:d.cid,t:d.title,a:d.abs}}),'Does sleep affect grades?')")
    ok('Paper 0' in html and 'included' not in html.split('<script')[0] and '"included"' not in html,'reviewer file carries titles and abstracts, no decisions')
    ok(html.count('</script>')==2,'abstract containing a closing script tag does not break the page')
    pg2=b.new_page(); pg2.set_content(html)
    ok(pg2.evaluate("document.getElementById('c').textContent")=='Paper 1 of 5 (0 decided)','reviewer page opens on paper 1')
    pg2.evaluate("pick('i');pick('e');pick('i');pick('e');pick('u')")
    ok(pg2.evaluate("document.getElementById('end').style.display")=='block','finish box appears when all 5 are decided')
    ids=json.loads(J("JSON.stringify(citGetLib().map(d=>d.cid))"))
    # reviewer answers: i, e, i, e, u  vs mine i, i, e, e, toread(u)
    ans={"v":1,"kind":"appuscholar-screen-answers","reviewer":"Dr R","at":"2026-11-08T10:00:00Z","decisions":dict(zip(ids,['i','e','i','e','u']))}
    open('/tmp/ans.json','w').write(json.dumps(ans))
    J("subOpen('lit','B3')")
    pg.set_input_files("#subMain input[type=file]","/tmp/ans.json"); pg.wait_for_timeout(600)
    t=T()
    ok('Compared with Dr R' in t,'reviewer name shown')
    ok('4 papers decided by both' in t and 'Agreement 50%' in t and 'kappa 0.00' in t,'4 decided by both, 50% agreement, kappa 0.00')
    ok('To settle (3)' in t,'two disagreements and one unsure listed (3)')
    J("b3Resolve(%s,'i')"%json.dumps(ids[2]))
    ok(json.loads(J("JSON.stringify(citGetLib()[2].scr.st)"))=='included' and 'Settled: include' in T(),'settling sets the library status')
    ok('kappa 0.00' in T(),'kappa does not move after settling')
    J("wPatch('B3','second',{theirs:{x:1},own:{}})")
    pg.set_input_files("#subMain input[type=file]","/tmp/ans.json")
    open('/tmp/bad.json','w').write('{"hello":1}')
    pg.set_input_files("#subMain input[type=file]","/tmp/bad.json"); pg.wait_for_timeout(500)
    ok('not a screening answers file' in J("document.body.innerText"),'a wrong file is refused with a message')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
