"""Search results quote the sentence that meets the question and carry a journal badge; Find papers on a
selected sentence looks up the cited study (build 2026.11.02j)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
def inv(text):
    d={}
    for i,w in enumerate(text.split(' ')): d.setdefault(w,[]).append(i)
    return d
W1={'id':'https://openalex.org/W1','display_name':'Sleep duration and exam anxiety in Indian undergraduates','publication_year':2021,
    'authorships':[{'author':{'display_name':'Rohit Sharma'}}],'primary_location':{'source':{'id':'https://openalex.org/S11','display_name':'Indian Journal of Psychology','is_in_doaj':True}},
    'abstract_inverted_index':inv('Exam anxiety is common in college. We surveyed 400 undergraduate students in Jaipur. Students who slept fewer hours reported higher exam anxiety than those who slept longer. Implications are discussed.'),
    'cited_by_count':12,'doi':'https://doi.org/10.1/x','referenced_works':[],'cited_by_api_url':'','open_access':{'is_oa':False},'is_retracted':False,'biblio':{},'type':'article'}
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    calls=[]
    def oa(route):
        u=route.request.url;calls.append(u)
        if '/sources' in u: return route.fulfill(status=200,content_type='application/json',body=json.dumps({'results':[{'id':'https://openalex.org/S11','summary_stats':{'h_index':42,'2yr_mean_citedness':1.8},'is_in_doaj':True,'works_count':900}]}))
        return route.fulfill(status=200,content_type='application/json',body=json.dumps({'results':[W1],'meta':{'count':1}}))
    pg.context.route('**/api.openalex.org/**',oa)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    ok(J("rsQParts('Is sleep related to exam anxiety among students?').map(x=>x.w).join(',')")=='sleep,related,exam,anxiety,students','question split into its parts')
    J("showTool('research');document.getElementById('rsTopic').value='sleep and exam anxiety in students';document.getElementById('rsSrcPubmed').checked=false;RS_NARROW.warned='sleep and exam anxiety in students';researchSearch()"); pg.wait_for_timeout(1500)
    t=J("document.getElementById('rsResults').innerText")
    ok('Where it meets your question' in t and 'slept fewer hours reported higher exam anxiety' in t,'the abstract sentence that answers is quoted: %s'%t[:200])
    ok(J("document.querySelectorAll('#rsResults .rs-ans mark').length")>=3,'matched words are marked')
    ok('h 42' in t and 'DOAJ' in t,'journal badge shows h-index and DOAJ from OpenAlex')
    ok(J("!!rsJCache().S11"),'journal data is cached')
    # Find papers from a sentence with a citation
    J("setEditorHTML('<p id=\"s1\">Shorter sleep goes with more exam anxiety (Sharma, 2021).</p>');const r=document.createRange();r.selectNodeContents(document.getElementById('s1'));const s=getSelection();s.removeAllRanges();s.addRange(r)")
    calls.clear(); J("selFind()"); pg.wait_for_timeout(1500)
    ok(any('publication_year:2021' in c and 'Sharma' in c for c in calls),'the cited author and year are looked up')
    ok('cited in your sentence' in J("document.getElementById('rsStatus').textContent"),'the cited paper is shown first')
    ok('(Sharma' not in J("document.getElementById('rsTopic').value"),'the search box keeps the claim without the citation')
    # a sentence without a citation is cut to key words
    J("setEditorHTML('<p id=\"s2\">It is well known that hostel students sleep less during the examination period.</p>');const r=document.createRange();r.selectNodeContents(document.getElementById('s2'));const s=getSelection();s.removeAllRanges();s.addRange(r)")
    J("selFind()"); pg.wait_for_timeout(800)
    v=J("document.getElementById('rsTopic').value")
    ok('well known' not in v and 'hostel' in v and 'sleep' in v,'plain sentences become key words: %s'%v)
    b.close()
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:2])
print('FAILED' if fails else 'ALL PASS', len(fails))
