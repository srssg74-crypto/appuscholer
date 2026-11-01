"""The book, part 3: linked numbers that follow the study record, and the book check."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='Book3';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("""const o=studyGet();o.design=Object.assign(o.design||{},{type:'survey',n:'99',ss:{basis:'power',test:'ttest',n:84,recruit:99,alpha:.05,power:.8,drop:15,effSrc:'a pilot study of 32 students in Jaipur',at:111,
      sentence:'An a priori power analysis for an independent t-test (two-tailed α = .05, d = 0.62, power = 80%) showed that 84 participants were needed.'}});studySet(o)""")
    J("bpInsertOutline()")
    bid=J("studyGet().bookDoc")
    J("subOpen('design','C3')")
    ok('Put it in my book' in J("document.getElementById('subMain').innerText"),'C3 offers to put the sample size in the book')
    J("bbSampleToBook();bbPlaceGo()")
    r=J("[...editor.querySelectorAll('[data-slot=\"ss\"] span.bb-f')].map(s=>s.getAttribute('data-f')+'='+s.textContent)")
    ok('n.planned=84' in r and 'n.recruit=99' in r,'sample-size paragraph lands in 3.3.3 with 84 and 99 linked %s'%r)
    # a linked number in the abstract
    J("const h=editor.querySelector('[data-sec=\"front.abstract\"]');const p=h.nextElementSibling;p.textContent='We needed ';const r=document.createRange();r.selectNodeContents(p);r.collapse(false);const s=getSelection();s.removeAllRanges();s.addRange(r);savedRange=r.cloneRange();bbFieldInsert('n.planned')")
    ok(J("!!editor.querySelector('[data-sec=\"front.abstract\"]').nextElementSibling.querySelector('span.bb-f[data-f=\"n.planned\"]')"),'a linked number can be put in the abstract')
    ok('Linked number at the cursor' in J("(bbOutlineToggle(),document.getElementById('bbOutline').innerText)"),'outline offers linked numbers')
    # the record changes: every place follows
    J("const o=studyGet();o.design.ss=Object.assign({},o.design.ss,{n:90,recruit:106,at:222});o.design.n='106';studySet(o)")
    pg.wait_for_timeout(700)
    r=J("[...editor.querySelectorAll('span.bb-f')].map(s=>s.getAttribute('data-f')+'='+s.textContent)")
    ok(r.count('n.planned=90')==2 and 'n.recruit=106' in r,'all linked numbers follow the new calculation %s'%r)
    ok(J("editor.querySelectorAll('span.bb-f.bb-f-new').length")==3 and len(J("window._bbLastChanges"))==3,'changed places are marked and listed')
    ok(J("docsGet().find(d=>d.id===studyGet().bookDoc).body.indexOf('>90<')>=0"),'the book is saved with the new numbers')
    # keep the old value at one place
    J("bbFieldUnlink(editor.querySelector('[data-sec=\"front.abstract\"]').nextElementSibling.querySelector('span.bb-f'))")
    t=J("editor.querySelector('[data-sec=\"front.abstract\"]').nextElementSibling.textContent")
    ok('84' in t and not J("!!editor.querySelector('[data-sec=\"front.abstract\"]').nextElementSibling.querySelector('span.bb-f')"),'unlinking keeps the old value as plain text')
    # changes made while the book is closed show when it opens again
    J("docCreateWith('Notes','<p>n</p>')")
    J("const o=studyGet();o.design.ss=Object.assign({},o.design.ss,{n:95});studySet(o)"); pg.wait_for_timeout(500)
    J("docSwitch(studyGet().bookDoc)"); pg.wait_for_timeout(300)
    ok(J("editor.querySelector('[data-slot=\"ss\"] span.bb-f[data-f=\"n.planned\"]').textContent")=='95','opening the book brings changes made while it was closed')
    # book check
    J("const h=editor.querySelector('[data-sec=\"method.procedure\"]');h.nextElementSibling.textContent='Data will be collected in two colleges. As shown in Table 3, scores varied.'")
    J("const h=editor.querySelector('[data-sec=\"front.abstract\"]');h.nextElementSibling.textContent='Data from N = 70 students were analysed.'")
    J("logAdd('recruit');logCell('recruit',0,'appr','120');logCell('recruit',0,'agreed','95');logCell('recruit',0,'done','88')")
    J("docSaveBody(getEditorHTML())")
    msgs=J("bbCheck().map(x=>x.sev+': '+x.msg)")
    has=lambda s: any(s in m for m in msgs)
    ok(has('earlier calculation'),'check: sample-size paragraph from an older calculation')
    ok(has('"Table 3" is mentioned'),'check: a table that does not exist')
    ok(has('The abstract says 70 participants'),'check: abstract number differs from the D2 log')
    ok(has('future tense'),'check: Method still in future tense after data collection')
    ok(has('Still empty: 1.1 Background'),'check: empty sections listed')
    J("packUse('ugc-phd-2022')")
    ok(any("UGC 2022 needs this page: Candidate's declaration" in m for m in J("bbCheck().map(x=>x.msg)")),'check: UGC 2022 front pages')
    J("const h=editor.querySelector('[data-sec=\"method.vars\"]');bbRange(h).forEach(x=>x.remove());h.remove();docSaveBody(getEditorHTML())")
    ok(any('Missing from the book: 3.4 Variables' in m for m in J("bbCheck().map(x=>x.msg)")),'check: plan section missing from the book')
    J("bbCheckOpen()")
    t=J("document.getElementById('bbCheckDlg').innerText")
    ok('to fix' in t and 'Go' in t,'check dialog lists issues with Go links')
    J("document.getElementById('bbCheckDlg').close()")
    sz=J("(async()=>{const h=document.createElement('div');h.innerHTML=getEditorHTML();const b=await dxBuild(h,'Book');return b.size})()")
    ok(sz>3000,'the book with linked numbers exports to Word (%s bytes)'%sz)
    real=[e for e in errors if 'favicon' not in e[1]]
    ok(not real,'no page errors %s'%real[:3])
    b.close()
print('\n%d failures'%len(fails) if fails else '\nALL PASS')
sys.exit(1 if fails else 0)
