"""Reading shelf: sections found from the PDF's type sizes, kept with the paper, shown as chips that jump to a page.
Also: the copy of the detector inside index.html is identical to tools/sections/sections.js."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
root=os.path.join(os.path.dirname(__file__),'..')
mod=open(os.path.join(root,'tools','sections','sections.js'),encoding='utf-8').read().rstrip('\n')
html=open(os.path.join(root,'index.html'),encoding='utf-8').read()
ok(mod in html,'index.html carries the section detector, identical to tools/sections/sections.js')

STUB = r"""
(()=>{
  const BODY='Participants were students from three colleges and completed the scale twice, a week apart, in class.';
  const L=(s,y,o)=>{o=o||{};const sz=o.size||10;return{str:s,transform:[sz,0,0,sz,72,y],width:s.length*sz*0.5,height:sz,fontName:o.font||'body',hasEOL:true}};
  const fill=(y0,n)=>Array.from({length:n},(_,i)=>L(BODY,y0-i*12));
  const H={size:13,font:'head'};
  const pages=[
    [L('Sleep and Exam Anxiety in First-Year Students',740,{size:18,font:'head'}),L('Abstract',700,H),...fill(680,6),L('1. Introduction',560,H),...fill(540,8)],
    [...fill(740,6),L('2. Methods',650,H),L('2.1. Participants',630,{font:'head'}),...fill(610,8)],
    [L('3. Results',740,H),...fill(720,8),L('4. Discussion',600,H),...fill(580,6),L('References',480,H),L('Smith, J. (2020). Sleep and learning. Journal of Sleep, 4, 1-9.',460,{size:9,font:'head'})]
  ];
  window.pdfjsLib={GlobalWorkerOptions:{},getDocument:()=>({promise:Promise.resolve({numPages:3,getMetadata:async()=>({info:{Title:''}}),
    getPage:async k=>({view:[0,0,612,792],getViewport:()=>({width:612,height:792}),getTextContent:async()=>({items:pages[k-1].map(x=>Object.assign({},x))}),render:()=>({promise:Promise.resolve()})})})})};
})();true
"""
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Sections';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J(STUB)
    J("shOpen()"); pg.wait_for_timeout(500)
    # a new PDF: sections are found while it is read and stored with the paper
    J("(async()=>{const f=new File([new Uint8Array([37,80,68,70])],'trial.pdf',{type:'application/pdf'});await shAddFiles({files:[f],value:''})})()"); pg.wait_for_timeout(1500)
    rec=J("SH.papers[0]")
    kinds=[s['kind'] for s in (rec.get('sections') or [])]
    ok(kinds==['abstract','introduction','methods','results','discussion','references'],'sections stored with the new paper: %s'%kinds)
    ok([x['title'] for x in rec['sections'][2]['subs']]==['Participants'],'numbered subheading kept under Methods')
    ok(rec['sections'][2]['page']==2,'Methods is on page 2')
    J("shRead(SH.papers[0].id,1)"); pg.wait_for_timeout(400)
    ok('Sections (6)' in J("document.getElementById('shBody').innerText"),'the reader shows the Sections list')
    J("document.querySelector('#shBody details').open=true")
    J("Array.from(document.querySelectorAll('#shBody details button')).find(x=>x.textContent.startsWith('Results')).click()"); pg.wait_for_timeout(300)
    ok(J("SH.page")==3,'tapping Results jumps to its page')
    # an older paper with no section list: Find sections reads the kept PDF again
    J("(async()=>{const r={id:'old1',title:'Old paper',file:'o.pdf',size:9,added:'2026-11-01',pages:['x','y','z'],total:3,notes:[],cells:{}};await shPut(r);await shFilePut('old1',new Uint8Array([37,80,68,70]).buffer);await shRefresh();shRead('old1',1)})()"); pg.wait_for_timeout(600)
    ok('Find sections' in J("document.getElementById('shBody').innerText"),'a paper with no list offers Find sections')
    J("shFindSections();true"); pg.wait_for_timeout(1500)
    ok(len(J("SH.cur.sections")or[])==6,'Find sections reads the kept PDF and stores the list')
    # a paper whose headings cannot be found says so and does not offer a wrong list
    J("(async()=>{const r={id:'old2',title:'Flat',file:'f.pdf',size:9,added:'2026-11-02',pages:['x'],total:1,notes:[],cells:{},sections:[]};await shPut(r);await shRefresh();shRead('old2',1)})()"); pg.wait_for_timeout(500)
    ok('No headings could be found' in J("document.getElementById('shBody').innerText"),'an empty list says no headings were found')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
