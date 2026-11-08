"""B2 search log fills itself (build 2026.11.08f): every search that is answered adds one row per database
(date, database, exact string, filters, number of records the database reports). Old rows stay."""
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
        body={"meta":{"count":1234},"results":[{"id":"https://openalex.org/W%d"%i,"display_name":"Sleep and exam stress %d"%i,"publication_year":2020,"authorships":[],"primary_location":{},"cited_by_count":1,"doi":None,"referenced_works":[],"open_access":{},"is_retracted":False} for i in range(1,4)]}
        return r.fulfill(status=200,content_type='application/json',body=json.dumps(body))
    if 'esearch.fcgi' in u:
        return r.fulfill(status=200,content_type='application/json',body=json.dumps({"esearchresult":{"count":"57","idlist":[]}}))
    return r.fulfill(status=200,content_type='application/json',body='{}')
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.route('**/api.openalex.org/**',route); pg.route('**/eutils.ncbi.nlm.nih.gov/**',route)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true;window.callAI=async function(){return ''}")
    J("openSaveAsProject();document.getElementById('sapName').value='B2 log';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("logSaveRows('search',[{date:'2026-01-01',db:'Other',q:'old hand-written row',hits:'9'}])")
    q="sleep quality and exam stress in hostel students"
    J("document.getElementById('rsTopic').value=%s"%json.dumps(q))
    J("document.getElementById('rsSrcOA').checked=true;document.getElementById('rsSrcPubmed').checked=true")
    J("researchSearch()"); pg.wait_for_timeout(1500)
    rows=json.loads(J("JSON.stringify(logRows(studyGet(),'search'))"))
    ok(len(rows)==3,'old row kept, two new rows (OpenAlex and PubMed): %d'%len(rows))
    ok(rows[0]['q']=='old hand-written row','old row untouched')
    oa=[r for r in rows if r.get('db')=='OpenAlex']; pm=[r for r in rows if r.get('db')=='PubMed']
    ok(len(oa)==1 and oa[0]['hits']=='1234','OpenAlex row carries the number the database reports (1234)')
    ok(len(pm)==1 and pm[0]['hits']=='57','PubMed row with zero records read still carries its count (57)')
    ok(oa[0]['q'] and 'sleep' in oa[0]['q'].lower(),'exact search string saved: '+oa[0]['q'][:60])
    ok(oa[0]['date']==J("new Date().toISOString().slice(0,10)"),'today\'s date on the row')
    ok('first 3 read' in oa[0]['lim'],'filters column says how many were read')
    J("researchSearch()"); pg.wait_for_timeout(1500)
    n=len(json.loads(J("JSON.stringify(logRows(studyGet(),'search'))")))
    ok(n==5,'a repeat search adds two more rows, nothing replaced (%d)'%n)
    # one database off
    J("document.getElementById('rsSrcPubmed').checked=false"); J("researchSearch()"); pg.wait_for_timeout(1500)
    n2=len(json.loads(J("JSON.stringify(logRows(studyGet(),'search'))")))
    ok(n2==6,'only OpenAlex ticked: one row added (%d)'%n2)
    # failure: nothing logged
    pg.unroute('**/api.openalex.org/**'); pg.route('**/api.openalex.org/**',lambda r:r.fulfill(status=500,body='x'))
    J("researchSearch()"); pg.wait_for_timeout(1500)
    n3=len(json.loads(J("JSON.stringify(logRows(studyGet(),'search'))")))
    ok(n3==6,'database that fails is not logged (%d)'%n3)
    J("subOpen('lit','B2')")
    t=J("Array.from(document.querySelectorAll('#subMain table.log-tbl input,#subMain table.log-tbl select')).map(e=>e.value).join('|')")
    ok('1234' in t and 'OpenAlex' in t,'B2 page shows the filled log')
    ok(J("logsDone('B2',studyGet())")==True,'B2 counts as done once a database and words are logged')
    errors=[e for e in errors if '500' not in str(e)]
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
