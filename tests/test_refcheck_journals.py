"""Reference check against Crossref: journal, volume, issue, first page, and corrections or retractions
(updated-by). Journal finder: keywords, grouping by journal, flags. Network is replaced by a fake fetch."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright

fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

CR = {
 '10.1037/ok1': {'DOI':'10.1037/ok1','title':['Exam anxiety in nursing students'],'issued':{'date-parts':[[2020]]},'author':[{'family':'Sharma'}],
             'container-title':['Journal of Personality and Social Psychology'],'short-container-title':['J Pers Soc Psychol'],'volume':'12','issue':'3','page':'45-60'},
 '10.1016/bad1': {'DOI':'10.1016/bad1','title':['Sleep and memory'],'issued':{'date-parts':[[2019]]},'author':[{'family':'Lee'}],
             'container-title':['Sleep Medicine'],'volume':'40','page':'101-110',
             'updated-by':[{'DOI':'10.1016/ret1','type':'retraction','source':'publisher','label':'Retraction','updated':{'date-parts':[[2023,2,1]]}},
                           {'DOI':'10.1016/ret1','type':'retraction','source':'retraction-watch','label':'Retraction','updated':{'date-parts':[[2023,2,1]]}},
                           {'DOI':'10.1016/cor1','type':'correction','source':'publisher','label':'Correction','updated':{'date-parts':[[2021]]}}]},
}
LIB = [
 {'cid':'c1','author':'Sharma, R.','year':'2020','title':'Exam anxiety in nursing students','source':'J. Pers. Soc. Psychol.','volume':'12','issue':'3','pages':'45-60','doi':'10.1037/ok1','type':'Journal article'},
 {'cid':'c2','author':'Lee, K.','year':'2019','title':'Sleep and memory','source':'Journal of Sleep Research','volume':'41','pages':'99-110','doi':'10.1016/bad1','type':'Journal article'},
]
WORKS = {'results': [{'primary_location':{'source':{'id':'https://openalex.org/S1','display_name':'Indian Journal of Psychiatry','host_organization_name':'Wolters Kluwer','issn_l':'0019-5545','is_oa':True,'is_in_doaj':True,'type':'journal'}}}]*5
 + [{'primary_location':{'source':{'id':'https://openalex.org/S2','display_name':'Some OA Journal','issn_l':'1111-2222','is_oa':True,'is_in_doaj':False,'type':'journal'}}}]*3
 + [{'primary_location':{'source':{'id':'https://openalex.org/S3','display_name':'A Repository','type':'repository'}}}]*4
 + [{'primary_location':None}]}

with sync_playwright() as p:
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 1280, 'height': 900})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    pg.evaluate("""([cr,works])=>{window.__urls=[];window.fetch=async(u)=>{u=String(u);window.__urls.push(u);
      const J=o=>new Response(JSON.stringify(o),{status:200,headers:{'Content-Type':'application/json'}});
      let m=u.match(/api\\.crossref\\.org\\/works\\/(.+)$/);if(m){const d=decodeURIComponent(m[1]);return cr[d]?J({message:cr[d]}):new Response('',{status:404})}
      if(/openalex\\.org\\/works\\?/.test(u))return J(works);
      m=u.match(/openalex\\.org\\/sources\\/(S\\d)/);if(m)return J(m[1]==='S1'?{homepage_url:'https://journals.lww.com/indianjpsychiatry',apc_usd:0,summary_stats:{h_index:60},works_count:9000}:{apc_usd:450,summary_stats:{h_index:5}});
      return new Response('',{status:404})}}""", [CR, WORKS])
    pg.evaluate("l=>citSaveLib(l)", LIB)
    pg.evaluate("rcJMatch('J. Pers. Soc. Psychol.','Journal of Personality and Social Psychology')")
    ok(pg.evaluate("rcJMatch('J. Pers. Soc. Psychol.','Journal of Personality and Social Psychology')"), 'abbreviated journal name matches the full one')
    ok(not pg.evaluate("rcJMatch('Journal of Sleep Research','Sleep Medicine')"), 'different journals do not match')
    pg.evaluate("showTool('cite')"); pg.wait_for_timeout(200)
    pg.evaluate("rcRun(true)"); pg.wait_for_timeout(2000)
    c = pg.evaluate("(()=>{const c=rcCache();return citGetLib().map(d=>c[citKey(d)])})()")
    ok(c[0]['s'] == 'ok' and not c[0].get('upd'), 'matching source is ok, no updates: %s' % c[0].get('m'))
    ks = sorted(x['k'] for x in c[1].get('m', []))
    ok(ks == ['pages','source','volume'], 'journal, volume and first page differences are flagged: %s' % ks)
    up = c[1].get('upd') or []
    ok(len(up) == 2 and sorted(u['k'] for u in up) == ['corr','retr'] and [u for u in up if u['k']=='retr'][0]['src'] == 'publisher,retraction-watch', 'one retraction line naming both sources, and a correction: %s' % up)
    html = pg.inner_html('#citLib')
    ok('Retracted. Do not cite it as evidence.' in html and 'Retraction Watch' in html and 'A correction was published' in html, 'library shows retraction and correction lines')
    ok('Journal differs. Crossref has: Sleep Medicine' in html, 'library shows the journal difference')

    # Journal finder
    kw = pg.evaluate("jfKeywords('Exam anxiety and sleep quality among first-year nursing students in Jaipur: a cross-sectional study of anxiety, sleep and coping')")
    ok('anxiety' in kw and 'sleep' in kw and 'study' not in kw and 'among' not in kw, 'keywords skip common words: %s' % kw)
    pg.evaluate("jfOpen()"); pg.wait_for_timeout(200)
    ok(pg.is_visible('#jfDlg'), 'journal finder opens')
    pg.fill('#jfText', 'short')
    pg.click('#jfRunBtn'); pg.wait_for_timeout(200)
    ok('Add a few more words' in pg.inner_text('#jfOut'), 'too little text asks for more')
    pg.fill('#jfText', 'Exam anxiety and sleep quality among first-year nursing students in Jaipur hospitals, with coping styles')
    pg.click('#jfRunBtn'); pg.wait_for_timeout(800)
    out = pg.inner_text('#jfOut')
    ok(out.find('Indian Journal of Psychiatry') >= 0 and out.find('Indian Journal of Psychiatry') < out.find('Some OA Journal'), 'journals ranked by count')
    ok('A Repository' not in out, 'repositories are left out')
    ok('listed in DOAJ' in out and 'not in DOAJ' in out and 'US$450' in out and 'h-index 60' in out, 'flags: DOAJ, fee, h-index')
    wurl = [u for u in pg.evaluate("window.__urls") if '/works?' in u][-1]
    ok('per-page=200' in wurl and 'type:article' in wurl and '%20OR%20' in wurl, 'query asks OpenAlex for 200 recent articles')
    ok(pg.evaluate("LS.get(pkey('appu_jf_text'))").startswith('Exam anxiety'), 'text is kept for next time')
    ok('Springer Nature Journal Suggester' in pg.inner_text('#jfDlg') or pg.evaluate("document.querySelectorAll('#jfDlg a[href*=springer]').length") > 0, 'publisher finders listed')
    bad = [e for e in errs if e[0] == 'pageerror']
    ok(not bad, 'no page errors %s' % bad[:3])
    b.close()
sys.exit(1 if fails else 0)
