"""Home feed: new papers on the topic, papers citing the library, retracted library papers."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
S='/tmp/claude-0/-home-claude/d540b351-a2df-5fa6-9a88-226a4c6e6a4f/scratchpad/'
calls=[]
def W(i,t,d,doi):return{'id':'https://openalex.org/'+i,'display_name':t,'publication_year':2026,'publication_date':d,'doi':'https://doi.org/'+doi,'authorships':[{'author':{'display_name':'Neha Rao'}},{'author':{'display_name':'X'}}],'primary_location':{'source':{'display_name':'J Sleep'}}}
def route(r):
    u=r.request.url;calls.append(u)
    if 'filter=doi:' in u:
        return r.fulfill(status=200,content_type='application/json',body=json.dumps({'results':[{'id':'https://openalex.org/W10','doi':'https://doi.org/10.1/a','display_name':'Alpha','is_retracted':False},{'id':'https://openalex.org/W11','doi':'https://doi.org/10.1/b','display_name':'Beta paper','is_retracted':True}]}))
    if 'filter=cites:' in u:
        return r.fulfill(status=200,content_type='application/json',body=json.dumps({'results':[W('W20','A new study citing Alpha','2026-10-12','10.9/c1')]}))
    if 'search=' in u:
        return r.fulfill(status=200,content_type='application/json',body=json.dumps({'results':[W('W30','Night screens and sleep in students','2026-10-20','10.9/n1'),W('W31','Sleep loss and exam anxiety','2026-10-05','10.9/n2'),W('W10x','Alpha','2026-10-01','10.1/a')]}))
    return r.continue_()
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    pg.route('**/api.openalex.org/**',route)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Feed';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("apHomeShow()"); pg.wait_for_timeout(300)
    ok('Write your topic' in J("document.getElementById('fdBox').innerText"),'empty study: the box says what to do')
    J("const o=studyGet();o.idea={topic:'Does screen time at night affect sleep and exam anxiety?'};o.design={vars:[{name:'Screen time'},{name:'Sleep quality'},{name:'Exam anxiety'}]};studySet(o)")
    J("citSaveLib([{author:'Rao, A.',year:'2020',title:'Alpha',source:'J',doi:'10.1/a',type:'Journal article',style:'apa'},{author:'Sen, B.',year:'2021',title:'Beta paper',source:'J',doi:'10.1/b',type:'Journal article',style:'apa'}])")
    ok(J("fdWords()").__contains__('sleep') and 'does' not in J("fdWords()"),'search words from the topic and variables: '+', '.join(J("fdWords()")))
    J("apHomeShow()"); pg.wait_for_timeout(1500)
    t=J("document.getElementById('fdBox').innerText")
    ok('Retracted' in t and 'Beta paper' in t,'retracted library paper shown first')
    ok('A new study citing Alpha' in t and 'Cites your sources' in t,'new paper citing a library source')
    ok('Night screens and sleep in students' in t and 'New on your topic' in t,'new paper on the topic')
    ok(t.count('Alpha')==1,'a paper already in the library is not offered again')
    pg.locator('#fdBox').screenshot(path=S+'feed.png')
    n=len(calls); J("apHomeShow()"); pg.wait_for_timeout(500)
    ok(len(calls)==n,'not fetched again within the week')
    J("fdHide('10.9/n1')")
    ok('Night screens' not in J("document.getElementById('fdBox').innerText"),'item can be hidden')
    i=J("fdStore().items.findIndex(x=>x.doi==='10.9/n2')")
    J("fdAdd(%d,null)"%i); pg.wait_for_timeout(300)
    ok(any(d.get('title')=='Sleep loss and exam anxiety' for d in J("citGetLib()")),'item added to the library')
    J("fdRefresh(true)"); pg.wait_for_timeout(800)
    ok(len(calls)>n,'"Check now" fetches again')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
