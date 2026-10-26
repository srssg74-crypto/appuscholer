"""One study everywhere: documents, references and Stats Lab data follow the open study."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
J=lambda pg,js: pg.evaluate(js)
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J(pg,"window.confirm=()=>true;window.prompt=(a,b)=>b")
    # scratch work: text, a reference, stats data
    J(pg,"setEditorHTML('<p>Scratch draft about stress</p>');docSaveBody(getEditorHTML())")
    J(pg,"citSaveLib([{author:'Cohen, J.',year:'1988',title:'Statistical power analysis',type:'book'}])")
    # save as a new research project A
    J(pg,"openSaveAsProject();document.getElementById('sapName').value='Study A';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    pg.wait_for_timeout(400)
    ok('Scratch draft' in J(pg,"getEditorHTML()"),'A: scratch draft came into study A')
    ok(J(pg,"citGetLib().length")==1,'A: reference came into study A')
    ok(J(pg,"docsStudy().length")==1 and J(pg,"docsStudy()[0].pid")==J(pg,"getActiveProjectId()"),'A: document tagged with study A')
    pidA=J(pg,"getActiveProjectId()")
    # stats data in A
    J(pg,"showTool('stats')"); pg.wait_for_timeout(200)
    J(pg,"document.getElementById('statsPaste').value='g,score\\nA,1\\nA,2\\nB,3\\nB,4';statsParse()"); pg.wait_for_timeout(300)
    # new project B from the New Research Project path: starts clean
    J(pg,"openNewProjectDirect();document.getElementById('sapName').value='Study B';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    pg.wait_for_timeout(600)
    ok('Scratch draft' not in J(pg,"getEditorHTML()"),'B: editor does not show study A text')
    ok('Study B' in J(pg,"docsStudy()[0].title"),'B: main paper made for study B: '+J(pg,"docsStudy()[0].title"))
    ok(J(pg,"citGetLib().length")==0,'B: reference library starts empty')
    ok(J(pg,"document.getElementById('statsPaste').value")=='','B: Stats Lab empty')
    ok(J(pg,"document.querySelectorAll('#docSel option').length")==1,'B: only B documents in the list')
    J(pg,"setEditorHTML('<p>Study B text on sleep</p>');docSaveBody(getEditorHTML())")
    J(pg,"document.getElementById('statsPaste').value='x,y\\n1,2\\n3,4\\n5,7';statsParse()"); pg.wait_for_timeout(300)
    # back to A
    J(pg,"setActiveProject('%s')"%pidA); pg.wait_for_timeout(800)
    ok('Scratch draft' in J(pg,"getEditorHTML()"),'A again: A text back')
    ok(J(pg,"citGetLib().length")==1,'A again: A reference back')
    ok(J(pg,"document.getElementById('statsPaste').value").startswith('g,score'),'A again: A stats data back')
    # reload page: B data survives
    pidB=J(pg,"getProjects().find(p=>p.name==='Study B').id")
    J(pg,"setActiveProject('%s')"%pidB); pg.wait_for_timeout(500)
    pg.reload(); pg.wait_for_timeout(1800)
    ok('Study B text' in J(pg,"getEditorHTML()"),'reload: B text restored')
    ok(J(pg,"document.getElementById('statsPaste').value").startswith('x,y'),'reload: B stats data restored')
    ok(J(pg,"docsGet().length")==2,'no document lost: %d'%J(pg,"docsGet().length"))
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()

    # legacy user: two projects, three old documents, no migration yet
    errors=[]
    b,pg=new_page(p,errors)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(300)
    J(pg,"""(()=>{window._bkRestoring=true;localStorage.removeItem('appu_scope_v1');
      localStorage.setItem('appu_projects',JSON.stringify([{id:'p1',name:'Old one',stage:'idea',status:'active',createdAt:1,updatedAt:1},{id:'p2',name:'Old two',stage:'idea',status:'active',createdAt:2,updatedAt:2}]));
      localStorage.setItem('appu_active_project','p1');
      localStorage.setItem('appu_docs',JSON.stringify([{id:'d1',title:'Thesis',body:'<p>thesis</p>',updated:1},{id:'d2',title:'Notes',body:'<p>notes</p>',updated:1},{id:'d3',title:'Essay',body:'<p>essay</p>',updated:1}]));
      localStorage.setItem('appu_doc_current','d1');
      localStorage.setItem('appu_citations',JSON.stringify([{author:'Old, A.',year:'2000',title:'Old ref'}]));
      ['appu_citations__p1','appu_citations__p2'].forEach(k=>localStorage.removeItem(k));})()""")
    pg.reload(); pg.wait_for_timeout(1800)
    J(pg,"window.confirm=()=>true")
    ok('thesis' in J(pg,"getEditorHTML()"),'legacy: open thesis still open')
    ok(J(pg,"docsGet().find(d=>d.id==='d1').pid")=='p1','legacy: open doc joined the open study')
    ok(J(pg,"document.querySelectorAll('#docSel optgroup option').length")==2,'legacy: two old documents offered under "not in any study"')
    ok(J(pg,"citGetLib().length")==1,'legacy: old references copied into old study p1')
    J(pg,"docSwitch('d2')"); pg.wait_for_timeout(200)
    ok(J(pg,"docsGet().find(d=>d.id==='d2').pid")=='p1' and 'notes' in J(pg,"getEditorHTML()"),'legacy: choosing a loose doc moves it into the study')
    J(pg,"setActiveProject('p2')"); pg.wait_for_timeout(500)
    ok(J(pg,"citGetLib().length")==1,'legacy: old study p2 also gets the old references')
    ok(J(pg,"document.querySelectorAll('#docSel optgroup option').length")==1,'legacy: p2 sees the one remaining loose doc')
    ok(J(pg,"docsGet().length")==4,'legacy: nothing lost (3 old + new p2 paper)')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'legacy: no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
