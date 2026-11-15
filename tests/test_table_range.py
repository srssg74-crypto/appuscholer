"""Range selection, merge along a row, split, clear, copy, Word export of merged cells."""
import sys, os, base64, zipfile, io, re
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
T="<table><tr><th>Group</th><th>Time 1</th><th>Time 2</th></tr><tr><td>A</td><td>3.2</td><td>3.9</td></tr><tr><td>B</td><td>4.1</td><td>4.4</td></tr></table><p>after</p>"
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Q';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    def reset(): J("document.getElementById('editor').innerHTML=%r"%T); J("tblRangeClear()")
    reset()
    cell=lambda r,c:"document.querySelector('#editor table').rows[%d].cells[%d]"%(r,c)
    # drag across with the real mouse
    bb1=pg.locator('#editor table tr:nth-child(2) td:nth-child(2)').bounding_box(); bb2=pg.locator('#editor table tr:nth-child(2) td:nth-child(3)').bounding_box()
    pg.mouse.move(bb1['x']+8,bb1['y']+8); pg.mouse.down(); pg.mouse.move(bb2['x']+8,bb2['y']+8,steps=4); pg.mouse.up(); pg.wait_for_timeout(200)
    ok(J("document.querySelectorAll('#editor [data-tsel]').length")==2,'dragging across two cells marks both')
    ok(J("document.getElementById('tblBar').style.display")=='flex','bar shows after the drag')
    ok('data-tsel' not in J("getEditorHTML()") and 'data-selecting' not in J("getEditorHTML()"),'the selection marks are never saved')
    # copy gives tab-separated text
    txt=J("(()=>{const dt=new DataTransfer();const ev=new ClipboardEvent('copy',{clipboardData:dt,bubbles:true,cancelable:true});document.querySelector('#editor table').rows[1].cells[1].dispatchEvent(ev);return dt.getData('text/plain')})()")
    ok(txt=='3.2\t3.9','copy of a range is tab-separated: %r'%txt)
    # shift+click extends
    reset(); J("TB.a=%s;TB.b=%s"%(cell(1,0),cell(1,0)))
    pg.click('#editor table tr:nth-child(3) td:nth-child(2)',modifiers=['Shift']); pg.wait_for_timeout(150)
    ok(J("document.querySelectorAll('#editor [data-tsel]').length")==4,'Shift+click selects the rectangle (4 cells)')
    J("tblOp('clear')"); ok(J("[...document.querySelectorAll('#editor table tr')].slice(1).map(r=>r.cells[0].textContent.trim()+r.cells[1].textContent.trim()+'/'+r.cells[2].textContent.trim()).join('|')")=='/3.9|/4.4','Clear empties the selected cells and leaves the rest')
    # merge along a row
    reset(); J("TB.a=%s;TB.b=%s"%(cell(0,1),cell(0,2))); J("tblMark();tblOp('merge')")
    ok(J("document.querySelector('#editor table').rows[0].cells.length")==2 and J(cell(0,1)+".colSpan")==2,'merge: header spans two columns')
    ok(J(cell(0,1)+".textContent")=='Time 1 Time 2','merged text joined')
    ok('colspan="2"' in J("getEditorHTML()"),'colspan saved in the document')
    # Word
    b64=pg.evaluate("""(async()=>{const h=document.createElement('div');h.innerHTML=getEditorHTML();const bl=await dxBuild(h,'T');const ab=new Uint8Array(await bl.arrayBuffer());let s='';for(const x of ab)s+=String.fromCharCode(x);return btoa(s)})()""")
    xml=zipfile.ZipFile(io.BytesIO(base64.b64decode(b64))).read('word/document.xml').decode()
    ok('<w:gridSpan w:val="2"/>' in xml,'Word export: merged header has gridSpan 2')
    # merged table guards
    J("document.getElementById('editor').focus()"); J("(()=>{const c=%s;const r=document.createRange();r.selectNodeContents(c);r.collapse(true);const s=getSelection();s.removeAllRanges();s.addRange(r)})()"%cell(1,1))
    n=J("document.querySelector('#editor table').rows[0].cells.length")
    J("tblOp('addcol')"); ok(J("document.querySelector('#editor table').rows[0].cells.length")==n,'add column refused while cells are merged')
    ok('Column B' in (J("(()=>{tblBarShow();return document.getElementById('tblPos').textContent})()")),'position label under a merged header is right')
    J("(()=>{const c=%s;const r=document.createRange();r.selectNodeContents(c);r.collapse(true);const s=getSelection();s.removeAllRanges();s.addRange(r)})()"%cell(0,1))
    J("tblOp('addrow')"); ok(J("document.querySelector('#editor table').rows[1].cells.length")==3,'add row under a merged header makes three cells')
    # split
    J("(()=>{const c=%s;const r=document.createRange();r.selectNodeContents(c);r.collapse(true);const s=getSelection();s.removeAllRanges();s.addRange(r)})()"%cell(0,1))
    J("tblOp('split')"); ok(J("document.querySelector('#editor table').rows[0].cells.length")==3 and 'colspan' not in J("getEditorHTML()"),'split puts the cells back')
    # merge across rows refused
    reset(); J("TB.a=%s;TB.b=%s"%(cell(0,1),cell(1,1))); J("tblOp('merge')")
    ok(J("document.querySelector('#editor table').rows[0].cells.length")==3,'merge across rows is refused')
    # tap-to-select for phones
    reset(); J("(()=>{const c=%s;const r=document.createRange();r.selectNodeContents(c);r.collapse(true);const s=getSelection();s.removeAllRanges();s.addRange(r)})()"%cell(1,0))
    J("tblOp('pick')"); pg.click('#editor table tr:nth-child(3) td:nth-child(3)'); pg.wait_for_timeout(150)
    ok(J("document.querySelectorAll('#editor [data-tsel]').length")==6,'Select cells, then tap the last cell: 2x3 range')
    # escape clears
    J("TB.a=%s;TB.b=%s;tblMark()"%(cell(1,0),cell(1,2))); pg.keyboard.press('Escape')
    ok(J("document.querySelectorAll('#editor [data-tsel]').length")==0,'Escape clears the selection')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
