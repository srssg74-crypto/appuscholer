"""The book, part 2: one book per study, outline like bookmarks, guide card at the cursor, and placement of a
step's draft into its section with replace or keep-both."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='Book2';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.design=Object.assign(o.design||{},{type:'survey'});studySet(o)")
    J("bbOutlineToggle()")
    ok('Make the book' in J("document.getElementById('bbOutline').innerText"),'outline offers to make the book when there is none')
    J("bpInsertOutline()")
    bid=J("studyGet().bookDoc")
    ok(bid and bid==J("docCurrentId()"),'making the outline makes it the book of this study')
    t=J("document.getElementById('bbOutline').innerText")
    ok('Chapter 3: Method' in t and '3.3.3 Sample size' in t and 'empty' in t,'outline lists chapters and sections with an empty badge')
    # guide card follows the cursor
    J("const h=editor.querySelector('[data-sec=\"method.size\"]');const p=h.nextElementSibling;const r=document.createRange();r.selectNodeContents(p);r.collapse(true);const s=getSelection();s.removeAllRanges();s.addRange(r);editor.focus();bbGuideUpdate()")
    g=J("({on:document.getElementById('bbGuide').style.display,t:document.getElementById('bbGuide').innerText})")
    ok(g['on']=='block' and 'Sample size' in g['t'] and 'Method' in g['t'] and 'C3' in g['t'],'guide card shows the section, its writing mode and its step')
    # placement with replace
    J("bbPut('<p>Result text A</p>','results.main','res-res','Results')")
    ok(J("document.getElementById('bbPlaceDlg').open") and J("document.getElementById('bbPlaceSel').value")=='results.main','dialog says where it will go')
    J("bbPlaceGo()")
    inside=J("(()=>{const h=editor.querySelector('[data-sec=\"results.main\"]');return bbRange(h).map(x=>x.textContent).join('|')})()")
    ok('Result text A' in inside,'draft lands inside its section')
    J("bbPut('<p>Result text B</p>','results.main','res-res','Results')")
    ok('Replace the earlier draft' in J("document.getElementById('bbPlaceInfo').innerText"),'a second draft from the same step offers to replace the first')
    J("bbPlaceGo()")
    r=J("({n:editor.querySelectorAll('[data-slot=\"res-res\"]').length,t:editor.innerText})")
    ok(r['n']==1 and 'Result text B' in r['t'] and 'Result text A' not in r['t'],'replace keeps one draft, the newer one')
    J("bbPut('<p>Result text C</p>','results.main','res-res');document.querySelector('input[name=bbRep][value=keep]').checked=true;bbPlaceGo()")
    ok(J("editor.querySelectorAll('[data-slot=\"res-res\"]').length")==2,'keep both keeps two drafts')
    ok(J("docsGet().find(d=>d.id===studyGet().bookDoc).body.indexOf('Result text C')>=0"),'the book is saved after placement')
    # from another document: switches to the book
    J("docCreateWith('Notes','<p>my notes</p>')")
    ok(J("docCurrentId()")!=bid,'a notes document is open')
    J("bbPut('<p>Sample text from C3</p>','method.size','ss');bbPlaceGo()")
    ok(J("docCurrentId()")==bid and 'Sample text from C3' in J("bbRange(editor.querySelector('[data-sec=\"method.size\"]')).map(x=>x.textContent).join('|')"),'placement from another document opens the book and puts it in 3.3.3')
    # missing section comes back in plan order
    J("const h=editor.querySelector('[data-sec=\"method.vars\"]');bbRange(h).forEach(x=>x.remove());h.remove();docSaveBody(getEditorHTML());bbOutlineRender()")
    ok('3.4 Variables' in J("document.getElementById('bbOutline').innerText") and 'not in the book' in J("document.getElementById('bbOutline').innerText"),'outline lists a plan section missing from the book')
    J("bbAddMissing('method.vars')")
    order=J("[...editor.querySelectorAll('[data-sec]')].map(h=>h.getAttribute('data-sec'))")
    ok(order.index('method.vars')==order.index('method.qsample' if 'method.qsample' in order else 'method.size')+1 and order.index('method.vars')<order.index('method.tools'),'missing section is added back in plan order')
    # design change: qualitative sections appear as missing, numbering follows
    J("const o=studyGet();o.design.type='qualitative';studySet(o);bbOutlineRender()")
    ok('Findings by theme' in J("document.getElementById('bbOutline').innerText"),'after switching to a qualitative design the themes section is listed as missing')
    J("bbAddMissing('results.themes')")
    ok(J("!!editor.querySelector('h2[data-sec=\"results.themes\"]')"),'themes section added as a section heading')
    # a second outline does not make a second book
    n=J("docsStudy().length")
    J("bpInsertOutline()")
    ok(J("docsStudy().length")==n and J("docCurrentId()")==bid,'asking for the outline again opens the existing book')
    # at my cursor instead
    J("const h=editor.querySelector('[data-sec=\"intro.background\"]');const r=document.createRange();r.setStartAfter(h);r.collapse(true);const s=getSelection();s.removeAllRanges();s.addRange(r);savedRange=r.cloneRange()")
    J("bbPut('<p>Cursor text</p>','results.main','x');bbPlaceCursor()")
    ok('Cursor text' in J("editor.innerText"),'at my cursor instead puts it where the cursor was')
    # without a book, inserts behave as before
    J("const o=studyGet();o.bookDoc='';studySet(o)")
    ok(J("bbPut('<p>z</p>','results.main','k')")==False,'without a book nothing is redirected')
    real=[e for e in errors if 'favicon' not in e[1]]
    ok(not real,'no page errors %s'%real[:3])
    b.close()
print('\n%d failures'%len(fails) if fails else '\nALL PASS')
sys.exit(1 if fails else 0)
