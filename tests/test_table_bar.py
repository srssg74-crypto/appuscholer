"""Table bar and paste from Excel."""
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
    ok(J("JSON.stringify(tblParse('a\\tb\\n1\\t2\\n'))")=='[["a","b"],["1","2"]]','parser reads tab and newline')
    ok(J("JSON.stringify(tblParse('\"x\\ty\"\\t2\\n3\\t4'))")=='[["x y","2"],["3","4"]]','parser keeps a quoted cell with a tab')
    ok(J("tblParse('just a sentence')")is None,'plain text is not taken as a table')
    ok(J("tblColLetter(0)+tblColLetter(25)+tblColLetter(26)")=='AZAA','column letters A, Z, AA')
    PASTE="""(txt)=>{const ed=document.getElementById('editor');const dt=new DataTransfer();dt.setData('text/plain',txt);const ev=new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true});ed.dispatchEvent(ev);return ev.defaultPrevented}"""
    # 1 paste outside a table makes a table
    J("(()=>{const ed=document.getElementById('editor');ed.innerHTML='<p>Start</p>';ed.focus();const r=document.createRange();r.selectNodeContents(ed);r.collapse(false);const s=getSelection();s.removeAllRanges();s.addRange(r)})()")
    r=pg.evaluate("(%s)('Group\\tM\\tSD\\nA\\t3.2\\t0.5\\nB\\t4.1\\t0.7')"%PASTE)
    ok(r is True and J("document.querySelectorAll('#editor table').length")==1,'pasting rows from Excel makes a table')
    ok(J("document.querySelectorAll('#editor table th').length")==3 and J("document.querySelectorAll('#editor table tr').length")==3,'first row is the header; 3 rows')
    ok(J("document.querySelector('#editor table').rows[2].cells[1].textContent")=='4.1','values land in the right cells')
    # 2 paste inside a cell fills from that cell and grows the table
    J("(()=>{const c=document.querySelector('#editor table').rows[2].cells[1];const r=document.createRange();r.selectNodeContents(c);r.collapse(true);const s=getSelection();s.removeAllRanges();s.addRange(r)})()")
    r=pg.evaluate("(%s)('9.9\\t8.8\\t7.7\\t6.6\\n5.5\\t4.4\\t3.3\\t2.2')"%PASTE)
    t=J("[...document.querySelectorAll('#editor table tr')].map(r=>[...r.cells].map(c=>c.textContent.trim()).join('|'))")
    ok(r is True and len(t)==4 and t[2].startswith('B|9.9|8.8|7.7|6.6') and t[3].split('|')[1]=='5.5','paste inside a cell fills from there; table grew: %s'%t)
    ok(len(set(len(x.split('|')) for x in t))==1,'every row has the same number of cells')
    # 3 ordinary text with no tabs still pastes normally
    r=pg.evaluate("(%s)('hello world')"%PASTE); ok(r is False,'text without tabs pastes as before')
    # 4 bar
    J("(()=>{const c=document.querySelector('#editor table').rows[1].cells[2];const r=document.createRange();r.selectNodeContents(c);r.collapse(true);const s=getSelection();s.removeAllRanges();s.addRange(r)})()")
    pg.click('#editor table td >> nth=0'); pg.wait_for_timeout(200)
    CUR=lambda r,c: J("(()=>{const c=document.querySelector('#editor table').rows[%d].cells[%d];const r=document.createRange();r.selectNodeContents(c);r.collapse(true);const s=getSelection();s.removeAllRanges();s.addRange(r)})()"%(r,c))
    ok('Column A, row 2' in J("document.getElementById('tblPos').textContent"),'a click on a cell moves the position label to it')
    CUR(1,2)
    ok(J("document.getElementById('tblBar').style.display")=='flex','bar shows in a table')
    ok('Column' in J("document.getElementById('tblPos').textContent"),'bar says which cell: '+J("document.getElementById('tblPos').textContent"))
    n0=J("document.querySelectorAll('#editor table tr').length")
    J("tblOp('addrow')"); ok(J("document.querySelectorAll('#editor table tr').length")==n0+1,'add row')
    J("tblOp('delrow')"); ok(J("document.querySelectorAll('#editor table tr').length")==n0,'delete row')
    w0=J("document.querySelector('#editor table').rows[0].cells.length")
    CUR(1,1); J("tblOp('addcol')"); ok(J("document.querySelector('#editor table').rows[0].cells.length")==w0+1 and J("document.querySelector('#editor table').rows[0].cells[1].tagName")=='TH','add column; the header cell is a header')
    CUR(1,2); J("tblOp('delcol')"); ok(J("document.querySelector('#editor table').rows[0].cells.length")==w0,'delete column')
    CUR(1,1); J("tblOp('align')"); ok(J("document.querySelector('#editor table').rows[2].cells[1].style.textAlign")=='center','align column centre')
    CUR(1,1); J("tblOp('apa')")
    ok(J("document.querySelector('#editor table').getAttribute('data-apa')")=='1' and J("document.querySelector('#editor table').rows[1].cells[0].style.borderBottomStyle")=='none','APA look: no inner lines')
    ok(J("document.querySelector('#editor table').rows[0].cells[0].style.borderBottom")!='none' and J("document.querySelector('#editor table').style.borderTop")!='','APA look: rule under the header and at the top')
    CUR(1,1); J("tblOp('apa')"); ok(J("document.querySelector('#editor table').getAttribute('data-apa')")is None,'APA look toggles off')
    # one-row table refuses delete
    J("document.getElementById('editor').innerHTML='<table><tr><th>a</th></tr></table>'")
    J("(()=>{const c=document.querySelector('#editor th');const r=document.createRange();r.selectNodeContents(c);r.collapse(true);const s=getSelection();s.removeAllRanges();s.addRange(r)})()")
    J("tblOp('delrow');tblOp('delcol')"); ok(J("document.querySelectorAll('#editor th').length")==1,'the last row and column cannot be deleted')
    # Word export keeps the APA look and the column alignment
    import base64, zipfile, io, re
    J("document.getElementById('editor').innerHTML='<table><tr><th>Group</th><th>M</th></tr><tr><td>A</td><td>3.2</td></tr></table>'")
    CUR(1,1); J("tblOp('align')"); J("tblOp('align')"); J("tblOp('apa')")
    b64=pg.evaluate("""(async()=>{const h=document.createElement('div');h.innerHTML=getEditorHTML();const bl=await dxBuild(h,'T');const ab=new Uint8Array(await bl.arrayBuffer());let s='';for(const x of ab)s+=String.fromCharCode(x);return btoa(s)})()""")
    xml=zipfile.ZipFile(io.BytesIO(base64.b64decode(b64))).read('word/document.xml').decode()
    tb=re.search(r'<w:tbl>.*?</w:tbl>',xml,re.S).group(0)
    ok('<w:left w:val="nil"/>' in tb and '<w:insideV w:val="nil"/>' in tb and '<w:insideH w:val="nil"/>' in tb,'Word: no side or inner lines in APA look')
    ok('<w:top w:val="single"' in tb and '<w:bottom w:val="single"' in tb,'Word: rules at top and bottom')
    ok('<w:tcBorders><w:bottom' in tb,'Word: rule under the header row')
    ok('<w:jc w:val="right"/>' in tb,'Word: right-aligned column kept')
    J("tblOp('apa')")
    b64=pg.evaluate("""(async()=>{const h=document.createElement('div');h.innerHTML=getEditorHTML();const bl=await dxBuild(h,'T');const ab=new Uint8Array(await bl.arrayBuffer());let s='';for(const x of ab)s+=String.fromCharCode(x);return btoa(s)})()""")
    tb=re.search(r'<w:tbl>.*?</w:tbl>',zipfile.ZipFile(io.BytesIO(base64.b64decode(b64))).read('word/document.xml').decode(),re.S).group(0)
    ok('<w:left w:val="single"' in tb,'Word: plain grid table is unchanged')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
