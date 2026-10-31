"""B3 matrix stance and quote columns; related papers from OpenAlex."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
def route(r):
    u=r.request.url
    if '/works/doi:' in u:
        rel={'10.1/a':['https://openalex.org/W1','https://openalex.org/W2'],'10.1/b':['https://openalex.org/W2','https://openalex.org/W3']}
        k=[k for k in rel if k.replace('/','%2F') in u or k in u]
        return r.fulfill(status=200,content_type='application/json',body=json.dumps({'related_works':rel[k[0]] if k else []}))
    if 'api.openalex.org/works?' in u:
        res=[{'id':'https://openalex.org/W1','display_name':'Paper one','publication_year':2020,'doi':'https://doi.org/10.1/one','authorships':[{'author':{'display_name':'Ravi Mehta'}}],'primary_location':{'source':{'display_name':'J One'}}},
             {'id':'https://openalex.org/W2','display_name':'Paper two shared','publication_year':2021,'doi':'https://doi.org/10.1/two','authorships':[{'author':{'display_name':'Neha Jain'}}],'primary_location':{'source':{'display_name':'J Two'}}},
             {'id':'https://openalex.org/W3','display_name':'Paper three','publication_year':2019,'doi':'https://doi.org/10.1/b','authorships':[],'primary_location':{}}]
        return r.fulfill(status=200,content_type='application/json',body=json.dumps({'results':res}))
    if 'api.crossref.org/works/' in u:
        return r.fulfill(status=200,content_type='application/json',body=json.dumps({'message':{'type':'journal-article','title':['Paper two shared'],'author':[{'family':'Jain','given':'Neha'}],'issued':{'date-parts':[[2021]]},'container-title':['J Two'],'DOI':'10.1/two'}}))
    return r.continue_()
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    pg.route('**/api.openalex.org/**',route);pg.route('**/api.crossref.org/**',route)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Matrix';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("citSaveLib([{author:'Rao, A.',year:'2020',title:'Alpha',source:'J',doi:'10.1/a',type:'Journal article',style:'apa'},{author:'Sen, B.',year:'2021',title:'Beta',source:'J',doi:'10.1/b',type:'Journal article',style:'apa'}])")
    J("subOpen('lit','B3')"); pg.wait_for_timeout(200)
    hd=J("[...document.querySelectorAll('#subMain .log-tbl th')].map(x=>x.textContent)")
    ok('For my question' in hd and 'Key line (with page)' in hd,'matrix has stance and key-line columns')
    J("logAdd('matrix');logCell('matrix',0,'paper','Rao (2020)');logCell('matrix',0,'finding','More screen time, less sleep');logCell('matrix',0,'stance','Supports');logRefresh()")
    ok('No contrasting study yet' in J("document.getElementById('subMain').innerText"),'one-sided matrix gets a nudge to search for contrasting studies')
    ok(J("document.querySelector('#subMain textarea[onchange*=quote]')!==null"),'key line is a text box')
    J("relFind()"); pg.wait_for_timeout(800)
    t=J("document.getElementById('relOut').innerText")
    ok('Paper two shared' in t and t.index('Paper two shared')<t.index('Paper one') and 'linked to 2' in t,'related papers listed, the one linked to two sources first')
    ok('Paper three' not in t,'a paper already in the library is left out')
    J("relAdd(0,null)"); pg.wait_for_timeout(500)
    ok(any(d.get('doi')=='10.1/two' for d in J("citGetLib()")),'related paper added to the library')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
