"""The book, part 4: contents and page numbers in the Word file, step checks that read the book by section id,
more linked numbers, and the writing-mode balance line."""
import sys, os, io, base64, zipfile
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
B64="(async(o)=>{const h=document.createElement('div');h.innerHTML=getEditorHTML();const b=await dxBuild(h,'Book',o);const a=new Uint8Array(await b.arrayBuffer());let s='';for(let i=0;i<a.length;i+=8192)s+=String.fromCharCode.apply(null,a.subarray(i,i+8192));return btoa(s)})"
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js,*a: pg.evaluate(js,*a)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Book4';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.design=Object.assign(o.design||{},{type:'survey',n:'99',ss:{basis:'power',n:84,recruit:99,alpha:.05,power:.8,effect:0.62,drop:15,effSrc:'a pilot study of 32 students',at:1,sentence:'84 participants were needed.'}});studySet(o)")
    J("bpInsertOutline()")
    J("""const h=editor.querySelector('[data-sec="results.main"]');const t=document.createElement('div');
      t.innerHTML=capBlocksHTML('table','Anxiety scores by "group"')+'<table><tr><td>a</td></tr></table>'+capBlocksHTML('figure','Anxiety across exam weeks')+'<p>fig</p>';
      let after=h;[...t.childNodes].forEach(n=>{after.after(n);after=n});renumberCaptions();docSaveBody(getEditorHTML())""")
    # Word: contents and page numbers
    z=zipfile.ZipFile(io.BytesIO(base64.b64decode(J(B64,{'toc':True,'tocTitle':'Contents'}))))
    names=z.namelist(); doc=z.read('word/document.xml').decode(); ftr=z.read('word/footer1.xml').decode() if 'word/footer1.xml' in names else ''
    ok('TOC \\o "1-3"' in doc and '>Contents<' in doc and 'Chapter 3: Method' in doc,'the book exports with a contents field listing the chapters')
    ok('PAGE' in ftr and 'footerReference' in doc,'every page has a page number in the footer')
    ok('updateFields' in z.read('word/settings.xml').decode(),'Word is asked to fill in the contents page numbers on opening')
    ok('TOC \\f t' in doc and '>List of tables<' in doc and 'TC &quot;Table 1 Anxiety scores by \'group\'&quot; \\f t' in doc.replace('"','&quot;') or ('TC "Table 1 Anxiety scores by' in doc),'the book has a list of tables built from the captions')
    ok('TOC \\f f' in doc and '>List of figures<' in doc and '\\f f \\l 1' in doc,'the book has a list of figures')
    ok(doc.index('>Contents<')<doc.index('>List of tables<')<doc.index('>List of figures<')<doc.rfind('Chapter 1'),'the lists come after the contents, before chapter 1')
    ct=z.read('[Content_Types].xml').decode()
    ok('footer1.xml' in ct and 'settings.xml' in ct,'the package lists the new parts')
    z2=zipfile.ZipFile(io.BytesIO(base64.b64decode(J(B64,None))))
    ok('TOC' not in z2.read('word/document.xml').decode() and 'word/footer1.xml' in z2.namelist(),'an ordinary document gets page numbers but no contents page')
    ok(' TC ' in z2.read('word/document.xml').decode(),'caption entries are kept in an ordinary export too, so a later contents update finds them')
    # step checks read the book by section id
    J("const h=editor.querySelector('h1[data-sec=\"method\"]');h.textContent='Chapter 3: Procedure of the study';const p=editor.querySelector('[data-sec=\"method.design\"]').nextElementSibling;p.textContent='A cross-sectional survey design was used with second-year students in two colleges of Jaipur during the 2026 session.';docSaveBody(getEditorHTML())")
    r=J("({book:(lsSecFor('E4')||{}).words||0,old:!!lsSection(LS_SEC.E4)})")
    ok(r['book']>10,'E4 finds the Method chapter by its section id after the heading was renamed (%s words)'%r['book'])
    # more linked numbers
    ok(J("[bbFieldVal('alpha'),bbFieldVal('power'),bbFieldVal('effect')].join('|')")=='.05|80%|0.62','α, power and effect size are available as linked numbers')
    # writing-mode balance
    J("""const h=editor.querySelector('[data-sec="disc.interpret"]');const p=h.nextElementSibling;
      p.outerHTML='<p>The hostel group reported higher anxiety scores than the day scholars, with a mean of 46.8 against 41.2 on the scale.</p><p>Sleep duration was shorter in the hostel group, averaging 5.9 hours a night across the fourteen days of the study period.</p><p>Exam weeks raised anxiety scores in both groups by about four points on the twenty-item questionnaire used here.</p>'""")
    h=J("bbBalanceHTML('disc.interpret',bpNode('disc.interpret'))")
    ok('Report 3' in h and 'Mostly reporting' in h,'balance line flags a discussion that only reports')
    J("""const h=editor.querySelector('[data-sec="disc.interpret"]');const p=document.createElement('p');p.textContent='This suggests that living away from home may raise anxiety because students lose their usual evening routine and family support.';bbOwn(h).slice(-1)[0].after(p)""")
    h=J("bbBalanceHTML('disc.interpret',bpNode('disc.interpret'))")
    ok('Interpret 1' in h and 'Mostly reporting' not in h,'an interpreting paragraph clears the advice')
    ok(J("bbBalanceHTML('method.design',bpNode('method.design'))")=='','no balance line in Method')
    real=[e for e in errors if 'favicon' not in e[1]]
    ok(not real,'no page errors %s'%real[:3])
    b.close()
print('\n%d failures'%len(fails) if fails else '\nALL PASS')
sys.exit(1 if fails else 0)
