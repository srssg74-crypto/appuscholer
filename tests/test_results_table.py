"""Insert as table: a results table in the draft that remembers its analysis and refreshes when the data changes."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
D1="group,score\\nA,10\\nA,12\\nA,11\\nA,13\\nB,15\\nB,17\\nB,16\\nB,18\\n"
D2="group,score\\nA,10\\nA,12\\nA,11\\nA,13\\nB,22\\nB,25\\nB,24\\nB,27\\n"
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true;true")
    J("openSaveAsProject();document.getElementById('sapName').value='Q';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("document.getElementById('statsDsName').value='Trial';rtNameChanged();document.getElementById('statsPaste').value='%s';statsParse();true"%D1)
    J("document.getElementById('statsTest').value='ttestInd';statsFieldsRender();true")
    J("(()=>{const d=window._statsData;const sd=document.getElementById('sf_dv'),si=document.getElementById('sf_iv');sd.value=String(d.cols.findIndex(c=>c.name==='score'));si.value=String(d.cols.findIndex(c=>c.name==='group'));statsRunNow()})()")
    ok(len(J("window._statsTables"))>=1,'the run captured its results tables: %d'%len(J("window._statsTables")))
    ok('Insert as table' in J("document.getElementById('statsResults').innerHTML"),'the Insert as table button is offered')
    J("document.getElementById('editor').innerHTML='<p>Results</p>'")
    J("(()=>{const ed=document.getElementById('editor');ed.focus();const r=document.createRange();r.selectNodeContents(ed);r.collapse(false);const s=getSelection();s.removeAllRanges();s.addRange(r);savedRange=null;try{document.getElementById('statsDlg').showModal()}catch(e){}})()")
    J("statsInsertTable()"); pg.wait_for_timeout(300)
    n=J("document.querySelectorAll('#editor table[data-run]').length")
    ok(n>=1,'table(s) in the draft carry the run id: %d'%n)
    ok('stats-table' not in J("getEditorHTML()") and 'data-newtbl' not in J("getEditorHTML()"),'no app classes or markers left in the document')
    ok(J("document.getElementById('capDlg').open"),'the caption dialog opens for the table')
    J("document.getElementById('capDlg').close()")
    before=J("document.querySelector('#editor table').textContent")
    items=J("rtScan().map(i=>i.status)"); ok(items==['cur'],'scan: the table is current: %s'%items)
    # data changes
    J("document.getElementById('statsPaste').value='%s';statsParse();true"%D2)
    items=J("rtScan().map(i=>i.status)"); ok(items==['stale'],'after the data changes the table is out of date: %s'%items)
    ok(J("document.querySelector('#editor table').classList.contains('stat-stale')")is False,'no stale class is written onto the table')
    r=J("(()=>{window._rtItems=rtScan();const it=window._rtItems[0];const x=rtRerunOne(it);return x.ok})()")
    after=J("document.querySelector('#editor table').textContent")
    ok(r is True and after!=before,'refresh replaces the numbers')
    ok(J("rtScan().map(i=>i.status)")==['cur'],'after refresh the table is current')
    # compare to a fresh run on D2
    J("window._statsRun=null;statsRunNow();true")
    fresh=J("(()=>{const d=document.createElement('div');d.innerHTML=window._statsTables[0];return d.textContent})()")
    ok(fresh==after,'the refreshed table equals a fresh run on the new data')
    # edited table warns
    J("document.querySelector('#editor table').rows[1].cells[0].textContent='EDITED'")
    ok(J("rtIsEdited(rtScan()[0])") is True,'a hand-edited table is detected before refresh')
    # table bar button
    J("(()=>{const c=document.querySelector('#editor table').rows[1].cells[1];const r=document.createRange();r.selectNodeContents(c);r.collapse(true);const s=getSelection();s.removeAllRanges();s.addRange(r)})()")
    J("tblOp('fromrun')"); ok(J("document.getElementById('rtDlg').open"),'From analysis opens the results list')
    ok('Results table' in J("document.getElementById('rtList').textContent"),'the list names it as a results table')
    J("document.getElementById('rtDlg').close()")
    # a test with several tables (multiple regression): all are inserted, all refresh together
    rows1=[(2,5,10),(3,4,11),(4,7,15),(5,3,14),(6,8,19),(7,2,17),(8,9,24),(9,5,22),(10,7,27),(11,1,23),(12,6,30),(13,4,29)]
    rows2=[(a,b,y+ (i%3)*4+ i) for i,(a,b,y) in enumerate(rows1)]
    mk=lambda rs: "x1,x2,y\\n"+"\\n".join("%d,%d,%d"%r for r in rs)+"\\n"
    J("document.getElementById('statsDsName').value='Multi';rtNameChanged();document.getElementById('statsPaste').value='%s';statsParse();true"%mk(rows1))
    J("document.getElementById('statsTest').value='mregress';statsFieldsRender();true")
    J("(()=>{const d=window._statsData;document.getElementById('sf_dv').value=String(d.cols.findIndex(c=>c.name==='y'));document.querySelectorAll('.sfm_preds').forEach(c=>{c.checked=true});statsRunNow()})()")
    k=len(J("window._statsTables"))
    ok(k>=2,'multiple regression gives several tables (%d)'%k)
    J("document.getElementById('editor').innerHTML='<p>R</p>'")
    J("(()=>{const ed=document.getElementById('editor');ed.focus();const r=document.createRange();r.selectNodeContents(ed);r.collapse(false);const s=getSelection();s.removeAllRanges();s.addRange(r);savedRange=null})()")
    J("statsInsertTable()"); pg.wait_for_timeout(300); J("try{document.getElementById('capDlg').close()}catch(e){}")
    ok(J("document.querySelectorAll('#editor table[data-run]').length")==k,'every table of the analysis is inserted (%d)'%k)
    ok(J("rtScan().length")==1,'they count as one tracked result')
    J("document.getElementById('statsPaste').value='%s';statsParse();true"%mk(rows2))
    ok(J("rtScan().map(i=>i.status)")==['stale'],'stale after the data changes')
    ok(J("(()=>{window._rtItems=rtScan();return rtRerunOne(window._rtItems[0]).ok})()") is True,'all refresh together')
    J("window._statsRun=null;statsRunNow();true")
    ok(J("Array.from(document.querySelectorAll('#editor table[data-run]')).map(t=>t.textContent).join('|')")==J("window._statsTables.map(h=>{const d=document.createElement('div');d.innerHTML=h;return d.textContent}).join('|')"),'each refreshed table equals the fresh run')
    # a plain table
    J("document.getElementById('editor').innerHTML='<table><tr><th>a</th></tr><tr><td>1</td></tr></table>'")
    J("(()=>{const c=document.querySelector('#editor th');const r=document.createRange();r.selectNodeContents(c);r.collapse(true);const s=getSelection();s.removeAllRanges();s.addRange(r)})()")
    J("tblOp('fromrun')"); ok(not J("document.getElementById('rtDlg').open"),'a plain table says it is not tied to an analysis')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
