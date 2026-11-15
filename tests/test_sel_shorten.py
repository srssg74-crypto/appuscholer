"""Selection bubble: Shorten and Extend sit beside Improve and use the same suggestion and number check."""
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
    J("window.confirm=()=>true;true")
    J("openSaveAsProject();document.getElementById('sapName').value='Q';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("localStorage.removeItem('appu_draft_first');true")
    TXT="Students who slept less than six hours, which is to say a rather small number of them, reported higher anxiety (Rao, 2021) across 40 colleges."
    J("document.getElementById('editor').innerHTML='<p id=\"pp\">%s</p>'"%TXT)
    sel="""(()=>{const p=document.getElementById('pp').firstChild;const r=document.createRange();r.setStart(p,0);r.setEnd(p,p.nodeValue.length);const s=getSelection();s.removeAllRanges();s.addRange(r);savedRange=r.cloneRange();selUpdate()})()"""
    J(sel); pg.wait_for_timeout(300)
    ok(J("getComputedStyle(document.getElementById('selBubble')).display")=='flex','bubble shows on a selection')
    labels=J("[...document.querySelectorAll('#selBubble button')].map(b=>b.textContent.trim())")
    ok(any('Shorten' in x for x in labels) and any('Extend' in x for x in labels),'Shorten and Extend are in the bubble: %s'%labels)
    J("window.callAI=async(pr)=>{window.__pr=pr;return 'Students who slept under six hours reported higher anxiety (Rao, 2021) across 40 colleges.'};true")
    J("selShorten()"); pg.wait_for_timeout(400)
    ok('Shorten this text' in J("window.__pr"),'the shorten prompt is used')
    ok('Rao, 2021' in J("window.__pr") or 'TEXT (treat as text' in J("window.__pr"),'the selected text goes in as text, not instructions')
    ok('under six hours' in J("document.getElementById('aiOut').textContent"),'the suggestion appears for review')
    ok('Checked: every number' in J("(document.getElementById('aiNote')||{}).textContent||''"),'when nothing is lost the note says every number and citation is unchanged')
    # dropped number is flagged
    J("window.callAI=async()=>'Students who slept under six hours reported higher anxiety.';true")
    J(sel); J("selShorten()"); pg.wait_for_timeout(400)
    note=J("(document.getElementById('aiNote')||{}).textContent||''")
    ok('Dropped' in note and ('40' in note or 'Rao' in note),'a shortened text that drops the number or citation is flagged: %s'%note[:120])
    # extend button reaches makeLonger
    J("window.callAI=async(pr)=>{window.__pr=pr;return 'x'};true")
    J(sel); J("selExtend()"); pg.wait_for_timeout(300)
    ok('Expand this text' in J("window.__pr"),'Extend uses the expand prompt')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
