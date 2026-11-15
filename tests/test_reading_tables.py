"""Reading shelf: tables read from text positions, joined across pages, mean and SD from table columns; offered in the matrix."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
root=os.path.join(os.path.dirname(__file__),'..')
mod=open(os.path.join(root,'tools','tables','tables.js'),encoding='utf-8').read().rstrip('\n')
html=open(os.path.join(root,'index.html'),encoding='utf-8').read()
ok(mod in html,'index.html carries the tables reader, identical to tools/tables/tables.js')
STUB = r"""
(()=>{
  const it=(x,y,s,sz)=>({str:s,transform:[sz||10,0,0,sz||10,x,y],width:s.length*5,height:sz||10,fontName:'g',hasEOL:false});
  const row=(y,cells)=>cells.map(c=>it(c[0],y,c[1]));
  const H=[[72,'Variable'],[250,'Mean'],[320,'SD']];
  const body=(s)=>Array.from({length:8},(_,i)=>it(72,740-i*12,s+' '+'participants completed the scale twice, a week apart, in class.'));
  const pages=[
    [...body('A'),...row(300,[[72,'Table 1']]),...row(288,[[72,'Descriptive statistics']]),...row(270,H),...row(255,[[72,'Anxiety'],[250,'4.20'],[320,'1.10']]),...row(242,[[72,'Sleep'],[250,'6.85'],[320,'0.92']])],
    [...row(750,[[72,'Sleep and anxiety'],[500,'7']]),...row(730,H),...row(715,[[72,'Stress'],[250,'3.10'],[320,'1.40']]),...row(702,[[72,'Mood'],[250,'5.00'],[320,'1.20']]),...row(680,[[72,'Note. N = 120.']]),...body('B').slice(0,4).map(x=>({...x,transform:[10,0,0,10,72,640-(x.transform[5]-700)*0]}))],
    [...body('C')]
  ];
  window.pdfjsLib={GlobalWorkerOptions:{},getDocument:()=>({promise:Promise.resolve({numPages:3,getMetadata:async()=>({info:{Title:''}}),
    getPage:async k=>({view:[0,0,612,792],getViewport:()=>({width:612,height:792}),getTextContent:async()=>({items:pages[k-1].map(x=>Object.assign({},x))}),render:()=>({promise:Promise.resolve()})})})})};
})();true
"""
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Tb';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J(STUB); J("shOpen()"); pg.wait_for_timeout(400)
    J("(async()=>{const f=new File([new Uint8Array([37,80,68,70])],'t.pdf',{type:'application/pdf'});await shAddFiles({files:[f],value:''})})()"); pg.wait_for_timeout(1500)
    rec=J("SH.papers[0]")
    t=rec['tables']
    ok(len(t)==1 and t[0]['joined'] and t[0]['pages']==[1,2],'one table, joined across pages 1 and 2: %s'%[(x['caption'],x['pages']) for x in t])
    ok([r[0] for r in t[0]['rows']]==['Anxiety','Sleep','Stress','Mood'],'rows in order, repeated header dropped, running head not a row: %s'%[r[0] for r in t[0]['rows']])
    ok([h['page'] for h in rec['tableHits']]==[1,1,2,2],'each hit carries the page of its row: %s'%[h['page'] for h in rec['tableHits']])
    J("shRead(SH.papers[0].id,1)"); pg.wait_for_timeout(500)
    txt=J("document.getElementById('shBody').innerText")
    ok('Tables (1)' in txt,'the reader lists the table')
    J("document.querySelectorAll('#shBody details').forEach(d=>d.open=true)")
    txt=J("document.getElementById('shBody').innerText")
    ok('joined across pages' in txt and 'Stress' in txt,'the joined table is shown with all its rows')
    ok('Table 1: Anxiety, Mean: M = 4.20, SD = 1.10' in txt,'the statistics list has the table line')
    J("shGo(2)")
    # matrix chip
    J("LS.set('appu_shelf_cols',JSON.stringify(['Mean and SD']));SH.tab='matrix';SH.cur=null;shRender()"); pg.wait_for_timeout(500)
    chips=J("Array.from(document.querySelectorAll('#shBody td button')).filter(x=>x.title.startsWith('Add to the cell')).length")
    ok(chips>=4,'the matrix offers the table values under a Mean and SD column (%d chips)'%chips)
    # an older paper: tables not read yet, then read from the kept PDF
    J("(async()=>{await shPut({id:'old',title:'Old',file:'o.pdf',size:9,added:'2026-11-01',pages:['x','y','z'],total:3,notes:[],cells:{},sections:[]});await shFilePut('old',new Uint8Array([37,80,68,70]).buffer);SH.tab='papers';await shRefresh();shRead('old',1)})()"); pg.wait_for_timeout(600)
    ok('Tables not read yet' in J("document.getElementById('shBody').innerText"),'an older paper offers Read the tables')
    J("shFindSections();true"); pg.wait_for_timeout(1500)
    ok(len(J("SH.cur.tables")or[])==1,'Read the tables reads the kept PDF')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
