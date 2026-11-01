"""Research News on the home page: new papers on the topic within the researcher's subject, papers citing the
library, retracted library papers; news and list views; nothing without an open project."""
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
def W(i,t,d,doi,abs=None,oa=False):
    w={'id':'https://openalex.org/'+i,'display_name':t,'publication_year':2026,'publication_date':d,'doi':'https://doi.org/'+doi,'authorships':[{'author':{'display_name':'Neha Rao'}},{'author':{'display_name':'X'}}],'primary_location':{'source':{'display_name':'J Sleep'}},'open_access':{'is_oa':oa}}
    if abs:
        inv={}
        for k,word in enumerate(abs.split(' ')): inv.setdefault(word,[]).append(k)
        w['abstract_inverted_index']=inv
    return w
ABS='This study aimed to examine screen use at night. Students who used phones after midnight showed poorer sleep quality and higher exam anxiety than others.'
def route(r):
    u=r.request.url;calls.append(u)
    if 'filter=doi:' in u:
        return r.fulfill(status=200,content_type='application/json',body=json.dumps({'results':[{'id':'https://openalex.org/W10','doi':'https://doi.org/10.1/a','display_name':'Alpha','is_retracted':False},{'id':'https://openalex.org/W11','doi':'https://doi.org/10.1/b','display_name':'Beta paper','is_retracted':True}]}))
    if 'filter=cites:' in u:
        return r.fulfill(status=200,content_type='application/json',body=json.dumps({'results':[W('W20','A new study citing Alpha','2026-10-12','10.9/c1')]}))
    if 'search=' in u:
        return r.fulfill(status=200,content_type='application/json',body=json.dumps({'results':[W('W30','Night screens and sleep in students','2026-10-20','10.9/n1',ABS,True),W('W31','SLEEP LOSS AND EXAM ANXIETY IN FIRST-YEAR STUDENTS','2026-10-05','10.9/n2'),W('W10x','Alpha','2026-10-01','10.1/a'),W('W40','The influence of current ratio on stock prices','2026-10-06','10.9/f1')]}))
    return r.continue_()
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    pg.route('**/api.openalex.org/**',route)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("apHomeShow()"); pg.wait_for_timeout(300)
    ok('Research News' in J("document.querySelector('.rn-head').innerText") and 'Open or start a research project' in J("document.getElementById('fdBox').innerText"),'without an open project: Research News asks for one and fetches nothing')
    ok(not calls,'no search runs without a project')
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
    su=[u for u in calls if 'search=' in u][-1]
    ok('primary_topic.field.id%3A32%7C28' in su or 'primary_topic.field.id:32|28' in su,'search is limited to psychology fields: '+su[-160:])
    ok('current ratio' not in t,'an off-topic paper with too few of the study words is dropped')
    ok(J("!!document.querySelector('#fdBox .rn-lead svg')"),'news view opens with a lead card and a drawn cover')
    ok('poorer sleep quality and higher exam anxiety' in t,'the card shows the main finding from the abstract')
    ok('Sleep loss and exam anxiety in first-year students' in t,'an all-capitals title is shown in sentence case')
    ok(J("[...document.querySelectorAll('#fdBox .rn-vars span')].map(s=>s.textContent).join('|')").__contains__('Sleep quality'),'the card names the study variable it matches')
    J("fdFlt('oa')"); t2=J("document.getElementById('fdBox').innerText")
    ok('Night screens' in t2 and 'Sleep loss' not in t2,'Open access filter')
    J("fdFlt('all');fdViewSet('list')")
    ok(J("document.querySelectorAll('#fdBox .rn-list li').length")>=3 and not J("!!document.querySelector('#fdBox .rn-open')"),'list view shows closed rows')
    J("document.querySelector('#fdBox .rn-li').click()")
    ok(J("!!document.querySelector('#fdBox .rn-open')") and J("document.querySelector('#fdBox .rn-li').getAttribute('aria-expanded')")=='true','a row opens in place when tapped')
    J("document.querySelector('#fdBox .rn-li').click()")
    ok(not J("!!document.querySelector('#fdBox .rn-open')"),'tapping again closes it')
    ok(J("localStorage.getItem('appu_rn_view')")=='list','the chosen view is remembered')
    pg.set_viewport_size({'width':1200,'height':900}); J("fdViewSet('news')")

    pg.locator('#fdBox').screenshot(path=S+'feed.png')
    n=len(calls); J("apHomeShow()"); pg.wait_for_timeout(500)
    ok(len(calls)==n,'not fetched again within the week')
    J("fdHide('10.9/n1')")
    ok('Night screens' not in J("document.getElementById('fdBox').innerText"),'item can be hidden')
    i=J("fdStore().items.findIndex(x=>x.doi==='10.9/n2')")
    J("fdAdd(%d,null)"%i); pg.wait_for_timeout(300)
    ok(any(d.get('title')=='Sleep loss and exam anxiety in first-year students' for d in J("citGetLib()")),'item added to the library')
    J("fdRefresh(true)"); pg.wait_for_timeout(800)
    ok(len(calls)>n,'"Check now" fetches again')
    J("fdScopeSet('area','3203')"); pg.wait_for_timeout(800)
    su=[u for u in calls if 'search=' in u][-1]
    ok('subfield.id%3A3203' in su or 'subfield.id:3203' in su,'choosing an area narrows the search to that subfield')
    J("fdExtraToggle(14,true)"); pg.wait_for_timeout(800)
    su=[u for u in calls if 'search=' in u][-1]
    ok(('32%7C28%7C14' in su or '32|28|14' in su) and 'subfield' not in su,'an extra subject widens the search to the subject plus that field')
    ok('Business and management' in J("document.querySelector('.rn-scope summary').innerText"),'the scope line names the extra subject')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
