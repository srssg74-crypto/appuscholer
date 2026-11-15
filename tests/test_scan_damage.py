"""Damaged-word warning for scanned papers: a note on the paper and a warning on a quote that contains damaged words."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
GOOD="Students who slept less than six hours reported higher anxiety scores across the whole sample of colleges. "*6
BAD=("Elic~ting a co~~lete_history and ~mmunity of the pa~ient is need~d before cond1t1ons are named. "*4)+GOOD
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true;true")
    J("openSaveAsProject();document.getElementById('sapName').value='Q';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("citSaveLib([{cid:'c1',author:'Rao, A.',title:'Sleep paper',year:'2021',journal:'J',type:'journal'}])")
    d=J("shDamaged('Clean words here. PHQ-9 and GAD-7, IL-12, DSM-5, https://a.b/c_d, Mesh2Motion, E2EE and | | a table | done.')")
    ok(len(d['bad'])==0,'clean text, scale names, URLs, table bars: no false marks %s'%d['bad'])
    d=J("shDamaged('Elic~ting a co~~lete_history and ~mmunity of cond1t1ons')")
    ok(len(d['bad'])>=4,'damaged words found: %s'%d['bad'])
    J("shOpen()"); pg.wait_for_timeout(400)
    J("(async()=>{await shPut({id:'g1',title:'Sleep paper',file:'a.pdf',size:9,added:'2026-11-16',pages:[%s],total:1,notes:[],cells:{},sections:[],lib:'c1'});await shPut({id:'b1',title:'Scanned paper',file:'b.pdf',size:9,added:'2026-11-16',pages:[%s],total:1,notes:[],cells:{},sections:[]});await shRefresh();shRead('g1',1)})()"%(json.dumps(GOOD),json.dumps(BAD))); pg.wait_for_timeout(600)
    ok('damaged by the scan' not in J("document.getElementById('shelfDlg').innerText"),'a clean paper shows no warning')
    J("shRead('b1',1)"); pg.wait_for_timeout(400)
    ok('damaged by the scan' in J("document.getElementById('shelfDlg').innerText"),'a damaged scan shows the warning with a percentage')
    SEL="""(()=>{const el=document.getElementById('shText');const tn=(function f(n){for(const c of n.childNodes){if(c.nodeType===3&&c.nodeValue.indexOf('Elic')>=0)return c;const r=f(c);if(r)return r}return null})(el);
      const a=tn.nodeValue.indexOf('Elic'),b=tn.nodeValue.indexOf('before cond1t1ons')+17;const r=document.createRange();r.setStart(tn,a);r.setEnd(tn,b);const s=getSelection();s.removeAllRanges();s.addRange(r);return s.toString()})()"""
    J("window.__t=[];const st=showToast;window.showToast=function(m){window.__t.push(m);return st(m)};true")
    J("document.getElementById('editor').innerHTML='<p>x</p>'"); J(SEL); J("shQuoteToDraft()"); pg.wait_for_timeout(300)
    t=J("window.__t.join(' || ')")
    ok('damaged word' in t and 'page picture' in t,'quoting a damaged passage warns: '+t[:120])
    ok('class="sq"' in J("document.getElementById('editor').innerHTML"),'the quote is still inserted (amber), the student decides')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
