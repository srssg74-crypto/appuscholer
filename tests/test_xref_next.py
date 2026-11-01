"""Live cross-references to tables and figures, and "Next for you" from the steps and the book."""
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
    J("openSaveAsProject();document.getElementById('sapName').value='XRef';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.design=Object.assign(o.design||{},{type:'survey'});studySet(o)")
    J("bpInsertOutline()")
    # two tables in Results, one figure
    J("""const h=editor.querySelector('[data-sec="results.main"]');const t=document.createElement('div');
      t.innerHTML=capBlocksHTML('table','Anxiety scores by group')+'<table><tr><td>a</td></tr></table>'+capBlocksHTML('table','Sleep hours by group')+'<table><tr><td>b</td></tr></table>'+capBlocksHTML('figure','Anxiety across exam weeks')+'<p>fig</p><p id="tx">Scores were higher in hostel students. </p>';
      let after=h;[...t.childNodes].forEach(n=>{after.after(n);after=n});renumberCaptions();docSaveBody(getEditorHTML())""")
    caps=J("xrCaps().map(c=>xrLabel(c)+'|'+!!c.getAttribute('data-capid'))")
    ok(caps==['Table 1|true','Table 2|true','Figure 1|true'],'captions get fixed ids and numbers %s'%caps)
    J("bbOutlineToggle()")
    t=J("document.getElementById('bbOutline').innerText")
    ok('Refer to a table or figure at the cursor' in t and 'Table 2' in t,'outline offers cross-references at the cursor')
    # insert a live reference to Table 2
    J("const p=document.getElementById('tx');const r=document.createRange();r.selectNodeContents(p);r.collapse(false);const s=getSelection();s.removeAllRanges();s.addRange(r);savedRange=r.cloneRange()")
    J("xrInsert(xrCaps()[1].getAttribute('data-capid'))")
    ok(J("document.getElementById('tx').querySelector('span.xr').textContent")=='Table 2','a live reference is inserted at the cursor')
    # move Table 2 above Table 1: the reference follows
    J("""const cs=xrCaps();const c2=cs[1],t2title=c2.nextElementSibling,t2=t2title.nextElementSibling;cs[0].before(c2,t2title,t2);renumberCaptions()""")
    ok(J("document.getElementById('tx').querySelector('span.xr').textContent")=='Table 1','after moving the table the reference reads Table 1')
    # delete it: reference shows Table ?
    J("const c=xrCaps()[0];c.nextElementSibling.nextElementSibling.remove();c.nextElementSibling.remove();c.remove();renumberCaptions();docSaveBody(getEditorHTML())")
    sp=J("(()=>{const s=document.getElementById('tx').querySelector('span.xr');return s.textContent+'|'+s.classList.contains('xr-broken')})()")
    ok(sp=='Table ?|true','a reference to a deleted table shows Table ? %s'%sp)
    msgs=J("bbCheck().map(x=>x.msg)")
    ok(any('cross-reference points to a table or figure that was deleted' in m for m in msgs),'book check lists the broken reference')
    ok(any('Table 1 (Anxiety scores by group) is never mentioned' in m for m in msgs),'book check lists a table never mentioned in the text')
    # plain text mention becomes a live link
    J("document.getElementById('tx').querySelector('span.xr').remove();document.getElementById('tx').append('See Table 1 and Figure 1.');docSaveBody(getEditorHTML())")
    is_=J("bbCheck().filter(x=>x.act).map(x=>x.msg)")
    ok(is_ and 'plain text' in is_[0],'book check offers to turn plain mentions into live links')
    n=J("xrLinkPlain()")
    ok(n==2 and J("document.querySelectorAll('#tx span.xr').length")==2,'plain mentions turned into live links (%s)'%n)
    ok(not any('never mentioned' in m for m in J("bbCheck().map(x=>x.msg)")),'no "never mentioned" once both are referred to')
    # click goes to the caption
    J("document.querySelector('#tx span.xr').click()"); pg.wait_for_timeout(200)
    ok(J("!!editor.querySelector('p[data-cap].xr-flash')"),'clicking a reference goes to its caption')
    ok(J("(()=>{const h=document.createElement('div');h.innerHTML=getEditorHTML();return h.querySelector('span.xr').getAttribute('contenteditable')})()")=='false','reference is one unit in the editor')
    # Next for you
    r=J("(()=>{const x=nfyPick();return x.kind+'|'+x.step[0]})()")
    ok(r.split('|')[0] in ('step','fill'),'next for you picks something to do on a new study (%s)'%r)
    first=r.split('|')[1]
    J("subSet('%s',{s:'dn'})"%first); J("try{document.getElementById('subDlg').close()}catch(e){}")
    r=J("(()=>{const x=nfyPick();return x.kind+'|'+x.step[0]+'|'+(x.sec?x.sec.id:'')})()")
    ok(r.startswith('fill|'+first+'|') or r.startswith('step|'),'a finished step whose section is empty is offered first: %s'%r)
    J("const o=studyGet();o.sub={};SUBSTAGES.forEach(x=>o.sub[x[0]]={s:'dn'});o.sub.C3={s:'ns'};o.ethics={route:'none'};studySet(o)")
    J("const h=editor.querySelector('[data-sec]');")
    # fill every section so no 'fill' remains
    J("editor.querySelectorAll('h1[data-sec],h2[data-sec],h3[data-sec]').forEach(h=>{const own=bbOwn(h);if(own.length)own[0].textContent='Some words written here.';else h.insertAdjacentHTML('afterend','<p>Some words written here.</p>')});docSaveBody(getEditorHTML())")
    r=J("(()=>{const x=nfyPick();return x.kind+'|'+x.step[0]+'|'+(x.sec?x.sec.id:'')})()")
    ok(r=='step|C3|method.size','next for you names the step and the book section it feeds: %s'%r)
    t=J("nfyHTML()")
    ok('Next: C3' in t and '3.3.3' in t and 'Open step C3' in t,'card text and buttons for the next step')
    J("bbOutlineRender()")
    ok('Next for you' in J("document.getElementById('bbOutline').innerText"),'next for you shows in the book outline')
    J("apHomeShow()"); pg.wait_for_timeout(300)
    ok('Next for you' in J("document.getElementById('apHome').innerText"),'next for you shows on the home page')
    J("const o=studyGet();o.sub.C3={s:'dn'};studySet(o)")
    ok(J("nfyPick().kind")=='done','everything done: the card points to the book check')
    J("const o=studyGet();o.sub.C3={s:'na'};o.sub.D1={s:'ar'};studySet(o)")
    ok(J("nfyPick().kind")=='wait','only waiting steps left: says so')
    J("apHomeHide&&apHomeHide()") if False else None
    J("docSwitch(studyGet().bookDoc)")
    sz=J("(async()=>{const h=document.createElement('div');h.innerHTML=getEditorHTML();const b=await dxBuild(h,'Book');return b.size})()")
    ok(sz>3000,'the book with live references exports to Word (%s bytes)'%sz)
    J("apLang=0") if False else None
    J("LS.set('appu_lang','hi')")
    ok('आपके लिए अगला' in J("nfyHTML()"),'Hindi card')
    real=[e for e in errors if 'favicon' not in e[1]]
    ok(not real,'no page errors %s'%real[:3])
    b.close()
print('\n%d failures'%len(fails) if fails else '\nALL PASS')
sys.exit(1 if fails else 0)
