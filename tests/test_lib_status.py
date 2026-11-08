"""Library paper status (build 2026.11.08i): to read / reading / included / excluded, a one-line reason,
the search it came from, and the earlier reason shown when the paper comes back in a new search."""
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
    if 'api.openalex.org' in u:
        body={"meta":{"count":3},"results":[{"id":"https://openalex.org/W%d"%i,"display_name":"Sleep and exam stress %d"%i,"publication_year":2020,"authorships":[],"primary_location":{},"cited_by_count":1,"doi":None,"referenced_works":[],"open_access":{},"is_retracted":False} for i in range(1,4)]}
        return r.fulfill(status=200,content_type='application/json',body=json.dumps(body))
    return r.fulfill(status=200,content_type='application/json',body='{}')
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.route('**/api.openalex.org/**',route); pg.route('**/eutils.ncbi.nlm.nih.gov/**',route)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true;window.callAI=async function(){return ''}")
    J("openSaveAsProject();document.getElementById('sapName').value='Status';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("document.getElementById('rsTopic').value='sleep quality and exam stress in hostel students';document.getElementById('rsSrcPubmed').checked=false")
    J("researchSearch()"); pg.wait_for_timeout(1200)
    J("rsAddToLibrary(0,true);rsAddToLibrary(1,true)")
    lib=lambda: json.loads(J("JSON.stringify(citGetLib())"))
    L=lib()
    ok(len(L)==2 and all(d['scr']['st']=='toread' for d in L),'new papers start as to read')
    ok(L[0]['scr']['src'].endswith('OpenAlex') and L[0]['scr']['src'][:4]=='2026','source-search label kept: '+L[0]['scr']['src'])
    J("citScrSet(0,'st','included')"); J("citScrSet(0,'why','sleep link is the core of my question')")
    J("citScrSet(1,'st','excluded')")
    html=J("citScrHTML(citGetLib()[1],1)")
    ok('PRISMA needs one for every excluded paper' in html,'excluded without a reason is flagged')
    J("citScrSet(1,'why','Wrong population: school children')")
    L=lib()
    ok(L[0]['scr']['st']=='included' and L[0]['scr']['why'].startswith('sleep') and L[1]['scr']['st']=='excluded' and L[1]['scr']['at'][:4]=='2026','status, reason and date saved')
    ok('PRISMA needs' not in J("citScrHTML(citGetLib()[1],1)"),'flag goes once the reason is written')
    ok('1 included' in J("document.getElementById('citCount').textContent") and '1 excluded' in J("document.getElementById('citCount').textContent"),'library count line shows the split')
    J("researchSearch()"); pg.wait_for_timeout(1200)
    t=J("document.getElementById('rsResults').innerText")
    ok('Excluded earlier: Wrong population: school children' in t,'re-search shows the earlier exclusion reason')
    ok(t.count('Already in library')==1,'included paper shows Already in library, the excluded one shows its reason instead')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
