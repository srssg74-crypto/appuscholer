"""Book search by title, page numbers on quotes, Shodhganga, RIS/BibTeX import, free legal copy."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
S='/tmp/claude-0/-home-claude/d540b351-a2df-5fa6-9a88-226a4c6e6a4f/scratchpad/'
RIS="""TY  - JOUR
AU  - Rao, Asha
AU  - Sen, Vikram
TI  - Sleep and exam anxiety in Indian students
JO  - Indian Journal of Psychology
PY  - 2021
VL  - 12
IS  - 3
SP  - 45
EP  - 60
DO  - 10.5555/ijp.2021.12
ER  - 
TY  - BOOK
AU  - Bandura, Albert
TI  - Social learning theory
PB  - Prentice Hall
PY  - 1977
ER  - 
"""
BIB="""@article{iyer2019,
  author = {Iyer, Meera and Das, Rohit},
  title = {{Screen time} and sleep},
  journal = {Journal of Youth Studies},
  year = {2019},
  volume = {8},
  pages = {10--20},
  doi = {10.5555/jys.8}
}
@phdthesis{verma2018,
  author = {Verma, Kiran},
  title = {Stress among college students in Rajasthan},
  school = {University of Rajasthan},
  year = 2018
}
"""
def route(r):
    u=r.request.url
    if 'openlibrary.org/search.json' in u:
        return r.fulfill(status=200,content_type='application/json',body=json.dumps({'docs':[{'title':'Psychological testing','subtitle':'Principles and applications','author_name':['Kevin R. Murphy','Charles O. Davidshofer'],'first_publish_year':1988,'publisher':['Prentice Hall'],'edition_count':6}]}))
    if 'api.openalex.org/works/doi:' in u:
        if 'ijp' in u: return r.fulfill(status=200,content_type='application/json',body=json.dumps({'best_oa_location':{'pdf_url':'https://example.org/free.pdf'}}))
        return r.fulfill(status=200,content_type='application/json',body=json.dumps({'best_oa_location':None,'open_access':{'oa_url':None}}))
    return r.continue_()
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    pg.route('**/openlibrary.org/**',route);pg.route('**/api.openalex.org/**',route)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Books2';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("showTool('cite');document.getElementById('citTitle').value='Psychological testing Murphy';bkSearch()"); pg.wait_for_timeout(500)
    ok('Psychological testing' in J("document.getElementById('bkOut').innerText"),'book found by title')
    J("bkPick(0)")
    ok(J("document.getElementById('citAuthor').value")=='Murphy, Kevin R.; Davidshofer, Charles O.' and J("document.getElementById('citType').value")=='Book','picked book fills the form')
    J("document.getElementById('citYear').value='2005';setEditorHTML('<p>Testing is </p>');placeCaretAtEnd&&placeCaretAtEnd();document.getElementById('citQuoteText').value='a systematic procedure';document.getElementById('citQuotePage').value='3';citInsertQuote()"); pg.wait_for_timeout(300)
    ed=J("getEditorHTML()")
    ok('a systematic procedure' in ed and 'p. 3)' in ed and 'data-pg="3"' in ed,'quote carries its page: (Murphy & Davidshofer, 2005, p. 3)')
    ok(J("document.querySelector('span.cit').textContent").endswith('2005, p. 3)'),'page shows inside the citation: '+J("document.querySelector('span.cit').textContent"))
    J("document.getElementById('citStyle').value='harvard';citStyleChanged&&citStyleChanged();citRefreshDoc()")
    ok('p. 3' in J("document.querySelector('span.cit').textContent"),'page kept when the style changes')
    J("document.getElementById('citURL').value='https://shodhganga.inflibnet.ac.in/handle/10603/12345';citLookup()")
    ok(J("document.getElementById('citType').value")=='Thesis','Shodhganga link sets the thesis type')
    n0=J("citGetLib().length")
    J("impFile({files:[new File([%s],'lib.ris')],value:''})"%json.dumps(RIS)); pg.wait_for_timeout(400)
    J("impFile({files:[new File([%s],'lib.bib')],value:''})"%json.dumps(BIB)); pg.wait_for_timeout(400)
    lib=J("citGetLib()")
    ok(len(lib)==n0+4,'RIS (2) and BibTeX (2) imported')
    rao=[d for d in lib if d['title'].startswith('Sleep and exam')][0]
    ok(rao['author']=='Rao, Asha; Sen, Vikram' and rao['pages']=='45–60' and rao['doi']=='10.5555/ijp.2021.12','RIS article read fully')
    iy=[d for d in lib if d['title']=='Screen time and sleep'][0]; vt=[d for d in lib if d['title'].startswith('Stress among')][0]
    ok(iy['author']=='Iyer, Meera; Das, Rohit' and iy['pages']=='10–20' and vt['type']=='Thesis' and vt['source']=='University of Rajasthan','BibTeX article and thesis read fully')
    i=J("citGetLib().findIndex(d=>d.doi==='10.5555/ijp.2021.12')")
    J("citRender();oaFind(%d,document.querySelector('#citItem%d button[onclick^=oaFind]'))"%(i,i)); pg.wait_for_timeout(500)
    ok('example.org/free.pdf' in J("document.getElementById('citItem%d').innerHTML"%i),'free legal copy found and linked')
    j=J("citGetLib().findIndex(d=>d.doi==='10.5555/jys.8')")
    J("oaFind(%d,document.querySelector('#citItem%d button[onclick^=oaFind]'))"%(j,j)); pg.wait_for_timeout(500)
    ok('No free copy' in J("document.getElementById('citItem%d').innerText"%j),'no free copy said plainly')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
