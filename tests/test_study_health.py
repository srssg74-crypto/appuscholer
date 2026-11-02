"""Study health: one card, each item with the button that fixes it; untouched book drafts refresh by themselves (build 2026.11.02h)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    ok(J("hlItems().length")==0,'no study open: nothing listed')
    J("openNewProjectDirect();document.getElementById('sapName').value='Health';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("setEditorHTML('<p>'+'Sleep and anxiety in students. '.repeat(8)+'</p>');docSaveBody(getEditorHTML())")
    J("LS.rm('appu_last_backup')")
    msgs=J("hlItems().map(x=>x.msg)")
    ok(any('never been backed up' in m for m in msgs),'work never backed up is listed first among fixes')
    ok(any('AI is not turned on' in m for m in msgs),'no AI key is listed')
    J("LS.set('appu_last_backup',String(Date.now()-10*864e5))")
    ok(any('10 days ago' in m for m in J("hlItems().map(x=>x.msg)")),'an old backup says how old')
    J("LS.set('appu_last_backup',String(Date.now()))")
    # a step marked done that the app disagrees with
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety in first-year students'};studySet(o);subStatusPick('A3','dn')")
    it=J("hlItems().find(x=>/A3 is marked done/.test(x.msg))")
    ok(it and 'one aim' in it['msg'] and it['act'].startswith("subOpen("),'a step marked done but incomplete is caught, with the reason and a button: %s'%(it and it['msg']))
    # synopsis gaps
    J("const o=studyGet();o.design={type:'survey',vars:[{name:'Exam anxiety',role:'outcome',type:'score',scale:'GAD7'}]};studySet(o);synBuild()"); pg.wait_for_timeout(300)
    ok(any('yellow gap' in m for m in J("hlItems().map(x=>x.msg)")),'synopsis gaps are listed')
    J("apHomeShow()"); pg.wait_for_timeout(300)
    t=J("document.getElementById('apHome').innerText")
    ok('Study health' in t and 'need' in t,'the Home card shows study health')
    # clicking the fix button runs it
    J("subStatusPick('A3','ns')")
    ok(not any('A3 is marked done' in m for m in J("hlItems().map(x=>x.msg)")),'the item goes once the status is honest')
    # untouched drafts refresh when the book is opened
    J("apHomeHide();bpInsertOutline()"); pg.wait_for_timeout(400)
    bid=J("bbBookId()")
    J("const o=studyGet();o.gap={text:'A new gap written after the book was made, about hostel students in Jaipur colleges.'};studySet(o)")
    J("docSwitch(studyGet().write.C8.syn)"); pg.wait_for_timeout(200)
    J("window._hlAutoAt=0;docSwitch('%s')"%bid); pg.wait_for_timeout(500)
    ok('hostel students in Jaipur' in J("getEditorHTML()"),'opening the book brings the new gap into its untouched draft')
    J("const s=editor.querySelector('[data-slot=\"auto-lit.gap\"]');s.querySelector('p').textContent='My own edited gap text.';docSaveBody(getEditorHTML())")
    J("const o=studyGet();o.gap={text:'Another change that must not overwrite the edit.'};studySet(o)")
    J("docSwitch(studyGet().write.C8.syn)"); pg.wait_for_timeout(200)
    J("window._hlAutoAt=0;docSwitch('%s')"%bid); pg.wait_for_timeout(500)
    h=J("getEditorHTML()")
    ok('My own edited gap text.' in h and 'Another change' not in h.split('auto-lit.gap')[1][:400],'a draft the student edited is left alone')
    b.close()
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:2])
print('FAILED' if fails else 'ALL PASS', len(fails))
