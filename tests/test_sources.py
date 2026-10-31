"""Books by ISBN, website check and capture, own reference list."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
OL={'ISBN:9780138167448':{'title':'Social learning theory','authors':[{'name':'Albert Bandura'}],'publishers':[{'name':'Prentice Hall'}],'publish_date':'1977'}}
CR_DOI={'message':{'type':'journal-article','title':['The magical number seven, plus or minus two'],'author':[{'family':'Miller','given':'George A.'}],'issued':{'date-parts':[[1956]]},'container-title':['Psychological Review'],'volume':'63','issue':'2','page':'81-97','DOI':'10.1037/h0043158'}}
CR_Q={'message':{'items':[{'type':'journal-article','title':['Self-efficacy: Toward a unifying theory of behavioral change'],'author':[{'family':'Bandura','given':'Albert'}],'issued':{'date-parts':[[1977]]},'container-title':['Psychological Review'],'volume':'84','issue':'2','page':'191-215','DOI':'10.1037/0033-295x.84.2.191'}]}}
def route(r):
    u=r.request.url
    if 'openlibrary.org' in u:
        k=[k for k in OL if k.split(':')[1] in u]
        return r.fulfill(status=200,content_type='application/json',body=json.dumps({k[0]:OL[k[0]]} if k else {}))
    if 'googleapis.com/books' in u: return r.fulfill(status=200,content_type='application/json',body='{"totalItems":0}')
    if 'api.crossref.org/works/' in u: return r.fulfill(status=200,content_type='application/json',body=json.dumps(CR_DOI))
    if 'api.crossref.org/works?' in u:
        if 'Self-efficacy' in u: return r.fulfill(status=200,content_type='application/json',body=json.dumps(CR_Q))
        return r.fulfill(status=200,content_type='application/json',body=json.dumps({'message':{'items':[{'title':['Something else entirely'],'issued':{'date-parts':[[2001]]}}]}}))
    return r.continue_()
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    pg.route('**/openlibrary.org/**',route);pg.route('**/www.googleapis.com/**',route);pg.route('**/api.crossref.org/**',route)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Sources';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    ok(J("citIsbn('ISBN 978-0-13-816744-8')")=='9780138167448' and J("citIsbn('0-306-40615-2')")=='0306406152' and J("citIsbn('978-0-13-816744-9')")=='' and J("citIsbn('10.1037/h0043158')")=='','ISBN read with check digit; a wrong digit and a DOI are refused')
    J("showTool('cite');document.getElementById('citURL').value='ISBN 978-0-13-816744-8'"); J("citLookup()"); pg.wait_for_timeout(600)
    ok(J("document.getElementById('citTitle').value")=='Social learning theory' and J("document.getElementById('citAuthor').value")=='Bandura, Albert' and J("document.getElementById('citType').value")=='Book' and J("document.getElementById('citSource').value")=='Prentice Hall','ISBN lookup fills a book')
    J("document.getElementById('citType').value='Website';citTypeChanged()")
    ok(J("!!document.getElementById('citWc_ev')&&document.getElementById('citWebBox').style.display!=='none'"),'website check shown for a website')
    J("document.getElementById('citWc_ev').value='links';citWebAdvice()")
    ok('cite the original study' in J("document.getElementById('citWebAdv').textContent"),'page citing research: advice to cite the original study')
    J("document.getElementById('citWc_who').value='none';document.getElementById('citAuthor').value='WHO';document.getElementById('citTitle').value='Mental health page';document.getElementById('citURL').value='https://example.org/mh';citAdd()")
    ok(J("citGetLib().slice(-1)[0].wc.who")=='none' and 'weak website' in J("document.getElementById('citLib').innerText"),'website check saved with the source and weak page flagged')
    J("document.getElementById('citType').value='Journal article';citTypeChanged()")
    ok(J("document.getElementById('citWebBox').style.display")=='none','check hidden for other types')
    # bulk
    J("""document.getElementById('citBulk').value=['10.1037/h0043158','ISBN 978-0-13-816744-8','Bandura, A. (1977). Self-efficacy: Toward a unifying theory of behavioral change. Psychological Review, 84(2), 191–215.','Sharma, R., & Gupta, P. (2019). Exam stress in Rajasthan colleges. Indian Journal of Psychology, 12(3), 45–60.'].join('\\n')""")
    n0=J("citGetLib().length"); J("citBulkAdd()"); pg.wait_for_timeout(1500)
    lib=J("citGetLib()"); out=J("document.getElementById('citBulkOut').textContent")
    ok(len(lib)==n0+4,'four lines, four sources added: '+out)
    typed=[d for d in lib if d.get('unverified')]
    ok(len(typed)==1 and typed[0]['author'].startswith('Sharma, R.; Gupta') and typed[0]['volume']=='12' and typed[0]['source']=='Indian Journal of Psychology','unfound reference kept as typed, parsed and marked')
    ok(any(d.get('doi')=='10.1037/0033-295x.84.2.191' for d in lib),'title match found its DOI')
    ok('kept as you typed it' in J("document.getElementById('citLib').innerText"),'library marks the unchecked one')
    J("citBulkAdd()") if False else None
    J("document.getElementById('citBulk').value='10.1037/h0043158';citBulkAdd()"); pg.wait_for_timeout(600)
    ok('already there' in J("document.getElementById('citBulkOut').textContent") and len(J("citGetLib()"))==n0+4,'duplicate not added twice')
    # bookmarklet on a web page
    src=J("decodeURIComponent(document.getElementById('citBookmarklet').getAttribute('href').slice(11))")
    pg2=b.new_page() if hasattr(b,'new_page') else None
    page=pg.context.new_page()
    page.set_content('<html><head><title>Sleep and screens</title><meta property="og:site_name" content="Sleep Foundation"><meta property="article:published_time" content="2025-03-14T10:00:00Z"><meta name="author" content="Asha Rao"></head><body><p>Screens before bed delay sleep (see doi.org/10.1037/h0043158 and https://doi.org/10.1037/0033-295x.84.2.191).</p></body></html>')
    page.evaluate("window.open=u=>{window._u=u}")
    page.evaluate(src)
    u=page.evaluate("window._u"); page.close()
    import base64,urllib.parse
    d=json.loads(base64.b64decode(urllib.parse.unquote(u.split('#capture=')[1])).decode())
    ok(d.get('kind')=='web' and d['site']=='Sleep Foundation' and d['author']=='Asha Rao' and len(d['dois'])==2,'capture button reads a web page and the 2 papers it links to: '+json.dumps(d)[:160])
    n1=len(J("citGetLib()"))
    J("citCaptureWeb(%s)"%json.dumps(d)); pg.wait_for_timeout(800)
    lib=J("citGetLib()")
    w=[x for x in lib if x.get('type')=='Website' and x.get('title')=='Sleep and screens']
    ok(len(w)==1 and w[0]['year']=='2025' and w[0]['month']=='3' and w[0]['accessed'],'website saved with date and accessed date')
    ok(len(lib)==n1+1,'both linked papers were already in the library, so only the website was added')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
