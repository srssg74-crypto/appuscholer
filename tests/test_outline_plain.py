"""Outline panel lists the headings of any document, with word counts; a tap scrolls to the heading."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Q';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("document.getElementById('editor').innerHTML='<h1></h1><h1>Introduction</h1><p>one two three four five</p><h2>Background</h2><p>six seven</p><h2>Method</h2><p>"+"word "*400+"</p>'")
    J("bbOutlineToggle()"); pg.wait_for_timeout(300)
    if J("document.getElementById('bbOutline').style.display")!='block': J("bbOutlineToggle()")
    J("bbOutlineRender()")
    rows=J("[...document.querySelectorAll('#bbOutline a.bb-row')].map(a=>a.textContent)")
    ok(len(rows)==3,'three headings listed, the empty one skipped: %s'%rows)
    ok('Introduction' in rows[0] and '5 words' in rows[0],'word count under each heading')
    ok('Method' in rows[2] and '400 words' in rows[2],'long section counted')
    J("document.getElementById('editor').scrollTop=0")
    J("document.querySelectorAll('#bbOutline a.bb-row')[2].click()"); pg.wait_for_timeout(600)
    ok(J("(()=>{const s=getSelection();return s.rangeCount&&s.anchorNode&&(s.anchorNode.parentNode.closest('h2')||s.anchorNode).textContent.indexOf('Method')>=0})()"),'tapping a row puts the cursor in that heading')
    # typing a new heading refreshes the list
    J("document.getElementById('editor').insertAdjacentHTML('beforeend','<h2>Results</h2>');document.getElementById('editor').dispatchEvent(new Event('input'))"); pg.wait_for_timeout(1100)
    ok(J("document.querySelectorAll('#bbOutline a.bb-row').length")==4,'a new heading appears after typing')
    J("document.getElementById('editor').innerHTML='<p>no headings</p>';bbOutlineRender()")
    ok('No headings yet' in J("document.getElementById('bbOutline').textContent"),'no headings: says so')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
