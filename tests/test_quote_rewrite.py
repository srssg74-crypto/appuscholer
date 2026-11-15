"""Tap an amber quote, press 'Switch to my own words': rewritten, citation kept, copy-heavy rewrites refused."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
PAGE="Sleep loss raised exam anxiety in first-year students across three colleges. Students who slept less than six hours reported the highest anxiety scores of the whole sample."
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Q';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("citSaveLib([{cid:'c1',author:'Rao, A.',title:'Sleep and exam anxiety in first-year students',year:'2021',journal:'Journal of Sleep',type:'journal'}])")
    J("shOpen()"); pg.wait_for_timeout(400)
    J("(async()=>{await shPut({id:'q1',title:'Sleep and exam anxiety in first-year students',file:'a.pdf',size:9,added:'2026-11-15',pages:[%s],total:1,notes:[],cells:{},sections:[],lib:'c1'});await shRefresh();shRead('q1',1)})()"%json.dumps(PAGE)); pg.wait_for_timeout(600)
    SELECT="""(()=>{const el=document.getElementById('shText');const tn=(function f(n){for(const c of n.childNodes){if(c.nodeType===3&&c.nodeValue.indexOf('slept less')>=0)return c;const r=f(c);if(r)return r}return null})(el);
      const a=tn.nodeValue.indexOf('Students who slept'),b=tn.nodeValue.indexOf('whole sample.')+'whole sample.'.length;const r=document.createRange();r.setStart(tn,a);r.setEnd(tn,b);const s=getSelection();s.removeAllRanges();s.addRange(r);return s.toString()})()"""
    Q="Students who slept less than six hours reported the highest anxiety scores of the whole sample."
    def put():
        J("document.getElementById('editor').innerHTML='<p>My sentence.</p>'")
        J("(()=>{const ed=document.getElementById('editor');ed.focus();const r=document.createRange();r.selectNodeContents(ed);r.collapse(false);const s=getSelection();s.removeAllRanges();s.addRange(r);savedRange=null;shQuoteInsert({id:'q1',text:%s,page:1})})()"%json.dumps(Q)); pg.wait_for_timeout(300)
        J("try{document.getElementById('shelfDlg').close()}catch(e){}")
    # run helper
    ok(J("sqRun('a b c d e f g h i','x b c d e f g h y')")==7,'run counter finds the longest shared run')
    # 1 good rewrite
    put()
    J("window.callAI=async()=>'Those who got under six hours of sleep scored highest on anxiety in the full sample.';true")
    pg.click('#editor span.sq'); pg.wait_for_timeout(200)
    ok(J("document.getElementById('sqBar').style.display")=='block','tapping a quote shows the button')
    pg.click('#sqBtn'); pg.wait_for_timeout(500)
    ed=J("document.getElementById('editor').innerHTML")
    ok('class="sq"' not in ed and 'Those who got under six hours' in ed,'the quote becomes the rewrite, no amber bar')
    ok('“' not in J("document.getElementById('editor').textContent"),'no quotation marks left')
    ok('data-cid="c1"' in ed and 'data-pg="1"' in ed,'the citation stays')
    ok(J("document.getElementById('sqBar').style.display")=='none','the button hides afterwards')
    # 2 copy-heavy rewrite refused
    put()
    J("window.callAI=async()=>'Students who slept less than six hours reported the highest anxiety scores of the whole sample, it says.';true")
    pg.click('#editor span.sq'); pg.click('#sqBtn'); pg.wait_for_timeout(500)
    ok(J("document.querySelectorAll('#editor span.sq').length")==1,'a rewrite that copies eight words is refused and the quote stays')
    # 3 AI error leaves quote alone
    J("window.callAI=async()=>{throw new Error('x')};true")
    pg.click('#editor span.sq'); pg.click('#sqBtn'); pg.wait_for_timeout(500)
    ok(J("document.querySelectorAll('#editor span.sq').length")==1,'an AI error leaves the quote unchanged')
    # 4 clicking elsewhere hides the bar
    pg.click('#editor span.sq'); J("document.querySelector('#editor p').click()")
    ok(J("document.getElementById('sqBar').style.display")=='none','clicking elsewhere hides the button')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
