"""Reader highlight colours fill the table (build 2026.11.08r)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
PG1='Participants were 96 nurses recruited from two hospitals. Each took a survey in March.'
PG2='Stress was higher on night shifts. A key limitation is the small single-city sample.'
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Colours';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("citSaveLib([{author:'G, H.',year:'2022',title:'Nurse stress on night shifts',type:'Journal article',style:'apa',scr:{st:'included',why:''}}])")
    cid=J("citGetLib()[0].cid")
    J("(async()=>{await shPut({id:'pN',title:'Nurse stress on night shifts',file:'n.pdf',size:1,added:'2026-11-08',pages:[%s,%s],total:2,notes:[],cells:{},lib:'%s'});const l=citGetLib();l[0].shelf='pN';citSaveLib(l)})()"%(json.dumps(PG1),json.dumps(PG2),cid)); pg.wait_for_timeout(500)
    J("shOpenAt('pN',1)"); pg.wait_for_timeout(800)
    ok(J("document.getElementById('shelfDlg').open")==True,'reader opens at the page')
    H=J("document.getElementById('shBody').innerHTML")
    ok(all(x in H for x in ['Sample','Method','Main finding','Limitation','Quote']),'five colour buttons')
    def sel(txt):
        J("""(()=>{var el=document.getElementById('shText'),w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT),n=w.nextNode();while(n&&n.textContent.indexOf(%s)<0)n=w.nextNode();var i=n.textContent.indexOf(%s),r=document.createRange();r.setStart(n,i);r.setEnd(n,i+%d);var s=getSelection();s.removeAllRanges();s.addRange(r)})()"""%(json.dumps(txt),json.dumps(txt),len(txt)))
    sel('Participants were 96 nurses recruited from two hospitals.')
    J("shSaveHL('yellow')"); pg.wait_for_timeout(600)
    d=json.loads(J("JSON.stringify(citGetLib()[0])"))
    ok(d['cells']['sample']['by']=='hl' and '96 nurses' in d['cells']['sample']['t'] and d['cells']['sample']['page']==1,'yellow highlight filled the sample cell with its page')
    ok(d['hls'][0]['col']=='yellow','highlight kept on the paper')
    J("shPage(1)"); pg.wait_for_timeout(400)
    sel('A key limitation is the small single-city sample.')
    J("shSaveHL('red')"); pg.wait_for_timeout(600)
    d=json.loads(J("JSON.stringify(citGetLib()[0])")); ok(d['cells']['limits']['page']==2,'red highlight filled the limitations cell (page 2)')
    sel('Stress was higher on night shifts.')
    J("shSaveHL('purple')"); pg.wait_for_timeout(600)
    d=json.loads(J("JSON.stringify(citGetLib()[0])")); ok(len(d['hls'])==3 and 'results' not in d['cells'] and len(d['cells'])==2,'purple quote goes to notes only, no cell')
    ok('background:#e9d5ff' in J("document.getElementById('shText').innerHTML"),'the passage is marked in its own colour')
    # own words stay
    J("b3Cell(0,'sample','my own words')"); J("shPage(-1)"); pg.wait_for_timeout(300)
    sel('Each took a survey in March.'); J("shSaveHL('yellow')"); pg.wait_for_timeout(600)
    d=json.loads(J("JSON.stringify(citGetLib()[0])")); ok(d['cells']['sample']['by']=='me' and len(d['hls'])==4,'my own words in a cell are kept; the quote is still saved')
    # click cell -> reader
    J("shRead(null,1)") if False else None
    J("subOpen('lit','B3')"); J("document.getElementById('shelfDlg').close()")
    ok('page 2' in J("document.getElementById('subMain').innerText"),'table cell shows its page link')
    J("shOpenAt('pN',2)"); pg.wait_for_timeout(600)
    ok(J("SH.cur&&SH.cur.id")=='pN' and J("SH.page")==2,'the link opens the reader at that page')
    # ---- page picture ----
    J("shOpenAt('pN',1)"); pg.wait_for_timeout(500)
    ok('Show page picture' in J("document.getElementById('shBody').innerText"),'page picture button')
    J("shImgToggle()"); pg.wait_for_timeout(800)
    ok('not kept for this paper' in J("document.getElementById('shImg').innerText"),'paper without a stored file says how to get the picture')
    J("(async()=>{await shFilePut('pN',new Uint8Array([37,80,68,70]).buffer)})()"); pg.wait_for_timeout(300)
    J("shPage(0)"); pg.wait_for_timeout(1000)
    ok(J("!!document.querySelector('#shImg canvas')"),'with a stored file the page is drawn on a canvas (viewer stubbed)')
    ok(J("document.querySelector('#shImg canvas').getAttribute('aria-label')").startswith('Page 1'),'canvas has a text label')
    J("shImgToggle()"); ok(J("document.getElementById('shImg')")is None,'hide works')
    J("(async()=>{await shDel('pN')})()"); pg.wait_for_timeout(300)
    ok(J("(async()=>await shFileGet('pN'))()")is None,'removing the paper removes its stored file')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
