"""Reading shelf: printed page numbers shown beside the PDF page and used for citations; can be switched off per paper."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mod=open(os.path.join(root,'tools','pagenums','pagenums.js'),encoding='utf-8').read().rstrip('\n')
html=open(os.path.join(root,'index.html'),encoding='utf-8').read()
ok(mod in html,'index.html carries pagenums.js, identical to the file')
def page(i,foot):
    return "Zervigon: Photography and the Arts\nBody sentence number %d about reproduction and photography in the nineteenth century, long enough to quote.\nSecond line of the page text.\n%s"%(i,foot)
PAGES=[page(i,str(147+i)) for i in range(1,8)]   # PDF page 1..7 -> printed 148..154
PAGES[1]=page(2,'M49')                            # misread footer on PDF page 2 (should be 149)
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true;true")
    J("openSaveAsProject();document.getElementById('sapName').value='Q';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("citSaveLib([{cid:'c1',author:'Zervigon, A.',title:'Photography and the Arts',year:'2023',journal:'NCAW',type:'journal'}])")
    J("shOpen()"); pg.wait_for_timeout(400)
    J("(async()=>{await shPut({id:'q1',title:'Photography and the Arts',file:'a.pdf',size:9,added:'2026-11-16',pages:%s,total:7,notes:[],cells:{},sections:[],lib:'c1'});await shRefresh();shRead('q1',2)})()"%json.dumps(PAGES)); pg.wait_for_timeout(600)
    head=J("document.getElementById('shelfDlg').innerText")
    ok('printed page' in head and '149' in head,'the reader shows printed page 149 beside PDF page 2 (footer was misread as M49)')
    ok('worked out' in head,'a page whose number was not read says it was worked out')
    J("shGo(3)"); pg.wait_for_timeout(200)
    import re
    ok(re.search(r'printed page\s*150',J("document.getElementById('shelfDlg').innerText")) is not None,'PDF page 3 shows printed page 150')
    SELECT="""(()=>{const el=document.getElementById('shText');const tn=(function f(n){for(const c of n.childNodes){if(c.nodeType===3&&c.nodeValue.indexOf('Body sentence')>=0)return c;const r=f(c);if(r)return r}return null})(el);
      const a=tn.nodeValue.indexOf('Body sentence'),b=tn.nodeValue.indexOf('to quote.')+9;const r=document.createRange();r.setStart(tn,a);r.setEnd(tn,b);const s=getSelection();s.removeAllRanges();s.addRange(r);return s.toString()})()"""
    J("document.getElementById('editor').innerHTML='<p>x</p>'")
    J(SELECT); J("shQuoteToDraft()"); pg.wait_for_timeout(300)
    ed=J("document.getElementById('editor').innerHTML")
    ok('data-pg="150"' in ed,'the citation uses the printed page 150, not PDF page 3')
    # switch off
    J("shPlToggle()"); pg.wait_for_timeout(300)
    ok(J("SH.papers.find(p=>p.id==='q1').plOff")is True,'the switch is saved on the paper')
    J("document.getElementById('editor').innerHTML='<p>x</p>'"); J(SELECT); J("shQuoteToDraft()"); pg.wait_for_timeout(300)
    ok('data-pg="3"' in J("document.getElementById('editor').innerHTML"),'switched off: the citation uses the PDF page')
    ok('cite the printed page' in J("document.getElementById('shelfDlg').innerText"),'the link now offers to go back')
    # a paper without numbers shows nothing extra
    J("(async()=>{await shPut({id:'q2',title:'Plain paper',file:'b.pdf',size:9,added:'2026-11-16',pages:['One page of text without numbers. '.repeat(5),'Another page. '.repeat(8)],total:2,notes:[],cells:{},sections:[]});await shRefresh();shRead('q2',1)})()"); pg.wait_for_timeout(500)
    ok('printed page' not in J("document.getElementById('shelfDlg').innerText"),'no numbers found: nothing is shown')
    # margin lines found by position (edges) are used when the record has them
    sc=["Line one\nbody a\nbody b\n%d\nbody c\nbody d\nbody e\nbody f"%(35+i) for i in range(3)]
    J("(async()=>{await shPut({id:'q3',title:'Scrambled order',file:'c.pdf',size:9,added:'2026-11-16',pages:%s,edges:[['35'],['36'],['87']],total:3,notes:[],cells:{},sections:[]});await shRefresh();shRead('q3',3)})()"%json.dumps(sc)); pg.wait_for_timeout(500)
    ok(re.search(r'printed page\s*37',J("document.getElementById('shelfDlg').innerText")) is not None,'record with edges: page 3 shows printed page 37 (87 misread, 35 and 36 agree)')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
