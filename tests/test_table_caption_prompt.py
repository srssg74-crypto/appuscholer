"""Insert table opens the caption dialog for that table; closing it skips the caption."""
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
    J("window.confirm=()=>true;window.prompt=()=>'3x3';true")
    J("openSaveAsProject();document.getElementById('sapName').value='Q';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("document.getElementById('editor').innerHTML='<p>Intro</p>'")
    J("insertTable()"); pg.wait_for_timeout(300)
    ok(J("document.getElementById('capDlg').open"),'caption dialog opens after the table is inserted')
    ok(J("document.getElementById('capKind').value")=='table','kind is already Table')
    ok(J("document.querySelectorAll('#editor table').length")==1 and 'data-newtbl' not in J("getEditorHTML()"),'one table, no marker left in the document')
    J("document.getElementById('capTitle').value='Group means';document.getElementById('capNote').value='N = 40.';capInsert()"); pg.wait_for_timeout(200)
    h=J("getEditorHTML()")
    ok('Table 1' in h and 'Group means' in h and 'N = 40.' in h,'caption, title and note are placed')
    ok(h.index('Table 1')<h.index('<table'),'caption sits above the table')
    # skipping
    J("document.getElementById('editor').innerHTML='<p>x</p>'")
    J("insertTable()"); pg.wait_for_timeout(200); J("document.getElementById('capDlg').close()")
    ok(J("document.querySelectorAll('#editor table').length")==1 and 'data-cap' not in J("getEditorHTML()"),'closing the dialog leaves a table with no caption')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
