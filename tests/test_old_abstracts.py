"""Fetch missing abstracts by DOI for older library papers (build 2026.11.09b)."""
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
    calls=[]
    def r(route):
        u=route.request.url; calls.append(u)
        body={"results":[{"doi":"https://doi.org/10.1000/aaa","abstract_inverted_index":{"Sleep":[0],"affects":[1],"learning":[2],"in":[3],"many":[4],"hostel":[5],"students":[6],"according":[7],"to":[8],"this":[9],"survey":[10],"of":[11],"four":[12],"hundred":[13],"people.":[14]}},{"doi":"https://doi.org/10.1000/bbb","abstract_inverted_index":None}]}
        route.fulfill(status=200,content_type='application/json',body=json.dumps(body))
    pg.route('**/api.openalex.org/works**',r)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Ab';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("citSaveLib(%s)"%json.dumps([
      {"author":"A, B.","year":"2019","title":"One","type":"Journal article","style":"apa","doi":"https://doi.org/10.1000/AAA","scr":{"st":"included","why":""}},
      {"author":"C, D.","year":"2020","title":"Two","type":"Journal article","style":"apa","doi":"10.1000/bbb"},
      {"author":"E, F.","year":"2021","title":"Three no doi","type":"Journal article","style":"apa"},
      {"author":"G, H.","year":"2022","title":"Four has one","type":"Journal article","style":"apa","doi":"10.1000/ccc","abs":"Already here and long enough to count as text."}]))
    ok(J("JSON.stringify(b3NoAbs())")=='{"withDoi":2,"noDoi":1}','counts: 2 can be looked up, 1 has no DOI')
    J("subOpen('lit','B3')"); pg.wait_for_timeout(600)
    ok('Get 2 missing abstracts by DOI' in J("document.getElementById('subMain').innerText"),'button shows the count')
    J("b3GetAbstracts()"); pg.wait_for_timeout(1500)
    L=json.loads(J("JSON.stringify(citGetLib())"))
    ok(L[0].get('abs','').startswith('Sleep affects learning'),'abstract rebuilt and stored (DOI case and prefix ignored)')
    ok(not L[1].get('abs'),'paper OpenAlex holds no abstract for stays empty')
    ok(L[3]['abs'].startswith('Already here'),'an existing abstract is never replaced')
    ok(len(calls)==1 and 'filter=doi' in calls[0],'one call for both papers')
    ok('1 abstracts found, 1 not held' in J("document.body.innerText"),'result is told')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
