"""Select in the paper, paste in the draft: a quote with an amber bar and a live citation; the bar goes when the words change."""
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
    J("(async()=>{await shPut({id:'q1',title:'Sleep and exam anxiety in first-year students',file:'a.pdf',size:9,added:'2026-11-15',pages:[%s],total:1,notes:[],cells:{},sections:[],lib:'c1'});await shPut({id:'q2',title:'An unlinked paper with a long title',file:'b.pdf',size:9,added:'2026-11-15',pages:[%s],total:1,notes:[],cells:{},sections:[]});await shRefresh();shRead('q1',1)})()"%(json.dumps(PAGE),json.dumps(PAGE))); pg.wait_for_timeout(600)
    SELECT="""(()=>{const el=document.getElementById('shText');const tn=(function f(n){for(const c of n.childNodes){if(c.nodeType===3&&c.nodeValue.indexOf('slept less')>=0)return c;const r=f(c);if(r)return r}return null})(el);
      const a=tn.nodeValue.indexOf('Students who slept'),b=tn.nodeValue.indexOf('whole sample.')+'whole sample.'.length;const r=document.createRange();r.setStart(tn,a);r.setEnd(tn,b);const s=getSelection();s.removeAllRanges();s.addRange(r);return s.toString()})()"""
    sel=J(SELECT); ok(sel.startswith('Students who slept'),'a passage is selected in the paper')
    J("document.getElementById('editor').innerHTML='<p>My own sentence.</p>'")
    J("shQuoteToDraft()"); pg.wait_for_timeout(400)
    ed=J("document.getElementById('editor').innerHTML")
    ok('class="sq"' in ed and 'Students who slept less than six hours' in ed,'button: the quote is in the draft with the amber mark')
    ok('“Students who slept' in ed,'the quote is in quotation marks')
    ok('class="cit"' in ed and 'data-cid="c1"' in ed and 'data-pg="1"' in ed,'a live citation to the library paper with the page follows')
    # copy and paste across the panes
    J("document.getElementById('editor').innerHTML='<p>Start. </p>'")
    J(SELECT); J("document.dispatchEvent(new Event('copy'))")
    res=J("""(()=>{const ed=document.getElementById('editor');ed.focus();const r=document.createRange();r.selectNodeContents(ed);r.collapse(false);const s=getSelection();s.removeAllRanges();s.addRange(r);
      const dt=new DataTransfer();dt.setData('text/plain',SH.lastCopy.text);const ev=new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true});ed.dispatchEvent(ev);return ev.defaultPrevented})()""")
    ed=J("document.getElementById('editor').innerHTML")
    ok(res is True and 'class="sq"' in ed and 'data-cid="c1"' in ed,'copy in the paper, paste in the draft: quote and citation arrive')
    # a paste of other text is left alone
    res=J("""(()=>{const ed=document.getElementById('editor');const dt=new DataTransfer();dt.setData('text/plain','Something copied from a website');const ev=new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true});ed.dispatchEvent(ev);return ev.defaultPrevented})()""")
    ok(res is False,'text from elsewhere pastes as it always did')
    # editing the quote removes the mark
    J("(()=>{const s=document.querySelector('#editor span.sq');s.firstChild.nodeValue=s.firstChild.nodeValue.replace('highest','LOWEST');upd()})()")
    ok(J("document.querySelectorAll('#editor span.sq').length")==0,'changing the words takes the amber mark off')
    # saved and reloaded: the mark stays while the quote is unchanged
    J("document.getElementById('editor').innerHTML='<p>x</p>'")
    J(SELECT); J("shQuoteToDraft()"); pg.wait_for_timeout(300)
    J("setEditorHTML(getEditorHTML())")
    ok(J("document.querySelectorAll('#editor span.sq').length")==1,'the mark survives a save and reload of the document')
    # unlinked paper: quote but no citation, said plainly
    J("shRead('q2',1)"); pg.wait_for_timeout(400)
    J("document.getElementById('editor').innerHTML='<p>y</p>'")
    J(SELECT); J("shQuoteToDraft()"); pg.wait_for_timeout(300)
    ed=J("document.getElementById('editor').innerHTML")
    ok('class="sq"' in ed and 'class="cit"' not in ed,'a paper not linked to the library gives a quote and no citation')
    # nothing selected: a toast asks for a selection and the draft is left alone
    J("window.__toasts=[];const _st=showToast;window.showToast=function(m){window.__toasts.push(m);return _st(m)};true")
    before=J("document.getElementById('editor').innerHTML")
    J("getSelection().removeAllRanges()"); J("shQuoteToDraft()")
    ok(any('Select some text' in t for t in J("window.__toasts"))and J("document.getElementById('editor').innerHTML")==before,'nothing selected: asks for a selection and changes nothing')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
