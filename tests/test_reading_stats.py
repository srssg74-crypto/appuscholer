"""Reading shelf: statistics the paper prints, listed by kind, tap to page.
Also: the copy of the finder inside index.html is identical to tools/stats/statsfind.js."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
root=os.path.join(os.path.dirname(__file__),'..')
mod=open(os.path.join(root,'tools','stats','statsfind.js'),encoding='utf-8').read().rstrip('\n')
html=open(os.path.join(root,'index.html'),encoding='utf-8').read()
ok(mod in html,'index.html carries the statistics finder, identical to tools/stats/statsfind.js')
P1="Participants (N = 120) were students. Mean anxiety was M = 4.2, SD = 1.1."
P2="Sleep predicted anxiety, r = -.41, p < .001. The groups differed, t(118) = 2.31, p = .023, d = 0.42."
P3="Nothing numeric is printed on this page, only prose about the sample and the setting."
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Stats';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("shOpen()"); pg.wait_for_timeout(500)
    J("(async()=>{const r={id:'st1',title:'Stats paper',file:'s.pdf',size:9,added:'2026-11-15',pages:%s,total:3,notes:[],cells:{},sections:[]};await shPut(r);await shRefresh();shRead('st1',1)})()"%json.dumps([P1,P2,P3])); pg.wait_for_timeout(600)
    t=J("document.getElementById('shBody').innerText")
    ok('Statistics in this paper' in t,'the reader shows the Statistics list')
    n=J("SH.stats.hits.length")
    ok(n==7,'hits found from the page text (%d)'%n)
    J("document.querySelectorAll('#shBody details')[1].open=true") if J("document.querySelectorAll('#shBody details').length")>1 else J("document.querySelector('#shBody details').open=true")
    J("Array.from(document.querySelectorAll('#shBody button')).find(x=>x.textContent.startsWith('t tests')).click()"); pg.wait_for_timeout(300)
    ok(J("SH.statKind")=='t','a kind button filters the list')
    J("document.querySelectorAll('#shBody details').forEach(d=>{if(d.innerText.indexOf('Statistics in this paper')===0||d.querySelector('summary').innerText.indexOf('Statistics')===0)d.open=true})")
    codes=J("Array.from(document.querySelectorAll('#shBody code')).map(x=>x.textContent)")
    ok(codes==['t(118) = 2.31'],'only the t test is listed: %s'%codes)
    J("Array.from(document.querySelectorAll('#shBody code')).forEach(c=>c.previousElementSibling.click())"); pg.wait_for_timeout(300)
    ok(J("SH.page")==2,'tapping a hit jumps to its page')
    J("(async()=>{const r={id:'st2',title:'No stats',file:'n.pdf',size:9,added:'2026-11-15',pages:%s,total:1,notes:[],cells:{},sections:[]};await shPut(r);await shRefresh();shRead('st2',1)})()"%json.dumps([P3])); pg.wait_for_timeout(500)
    ok('No reported statistics were found' in J("document.getElementById('shBody').innerText"),'a paper with none says so')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
