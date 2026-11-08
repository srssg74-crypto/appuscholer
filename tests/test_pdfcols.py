"""PDF text order and broken words (build 2026.11.08d). Made-up pages only, no paper text in the repo.
pdf.js order is kept unless a page runs across both columns line by line; then it is rebuilt from positions."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
JS="""
(function(){
  function it(s,x,y,w,rot,eol){return{str:s,transform:rot?[0,10,-10,0,x,y]:[10,0,0,10,x,y],width:w,height:10,hasEOL:!!eol}}
  const L=[],R=[];
  for(let i=0;i<20;i++){L.push(it('L'+i+' alpha beta gamma delta',50,640-i*14,235,0,1));R.push(it('R'+i+' one two three four',325,640-i*14,235,0,1))}
  const title=it('TITLE of the whole paper spans both columns right across the page now',50,740,500,0,1);
  window.__cols=[title].concat(L,R);                                   /* written column by column: fine as it is */
  const rows=[title];for(let i=0;i<20;i++){rows.push(L[i],R[i])};window.__rows=rows;  /* written line by line across both columns */
  window.__shuf=L.concat(R).sort(function(){return Math.random()-0.5});
  const tb=[];for(let i=0;i<20;i++){tb.push(it('Item '+i,50,700-i*14,40),it(String(20+i),250,700-i*14,15),it(String(3+i),400,700-i*14,10,0,1))};window.__table=tb;
  const one=[];for(let i=0;i<25;i++)one.push(it('S'+i+' single column line with enough words to fill the width of the page body',60,700-i*14,470,0,1));window.__one=one;
  window.__side=window.__shuf.concat([it('Downloaded from a journal site',590,400,150,true)]);
})()
"""
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J(JS)
    tags=lambda t:[x.split(' ')[0] for x in t.split('\n')]
    # layout order from positions (used only for pages that need it)
    r=J("(function(){const o=apPageOrder(__shuf,[0,0,612,792]);return{t:o.text,c:o.cols}})()")
    ok(r['c']==2 and tags(r['t'])[:20]==['L%d'%i for i in range(20)] and tags(r['t'])[20:]==['R%d'%i for i in range(20)],'positions: whole left column, then whole right column, whatever the file order')
    t=tags(J("apPageOrder(__cols,[0,0,612,792]).text"))
    ok(t[0]=='TITLE' and t[1]=='L0' and t[21]=='R0','positions: full-width title on top, then left, then right')
    r=J("(function(){const o=apPageOrder(__one,[0,0,612,792]);return{t:o.text,c:o.cols}})()")
    ok(r['c']==1 and tags(r['t'])==['S%d'%i for i in range(25)],'positions: single column stays single column')
    ok(tags(J("apPageOrder(__table,[0,0,612,792]).text"))[:2]==['Item','Item'] and 'Item 0 20 3' in J("apPageOrder(__table,[0,0,612,792]).text"),'positions: a table stays row by row')
    ok('Downloaded' not in J("apPageOrder(__side,[0,0,612,792]).text"),'positions: vertical side note is left out')
    ok(J("apPageOrder([],[0,0,612,792]).scanned")==True,'positions: empty page is reported as no text')
    # which pages get rebuilt
    ok(J("apPageText(__cols,[0,0,612,792]).mode")=='stream' and J("apPageText(__cols,[0,0,612,792]).text")==J("apStreamText(__cols)"),'a page written column by column keeps the pdf.js order untouched')
    r=J("apPageText(__rows,[0,0,612,792])")
    ok(r['mode']=='layout' and tags(r['text'])[1:21]==['L%d'%i for i in range(20)] and tags(r['text'])[21:]==['R%d'%i for i in range(20)],'a page written line by line across both columns is rebuilt: L0..L19 then R0..R19')
    ok('L0 alpha beta gamma delta R0' in J("apStreamText(__rows)").replace('\n',' '),'(the old order really did mix them)')
    ok(J("apPageText(__table,[0,0,612,792]).mode")=='stream','a table page is not rebuilt')
    ok(J("apPageText(__one,[0,0,612,792]).mode")=='stream','a single-column page is not rebuilt')
    # broken words at line ends, decided by the paper itself
    J("window.__jb=apJoinBreaks(['The scores were associ-\\nated with self-\\ncontrol and task-\\nrelated cues in high-\\nand low-reward trials. It was signi\\uFB01cant.','Scores were associated with self-control. A related item. One task only. Under-\\nstanding grew.'])")
    t=J("__jb[0]")
    ok('associated\nwith' in t,'soft break joined: associated (the joined word is used elsewhere)')
    ok('self-control' in t,'hyphen kept: self-control (the hyphenated word is used elsewhere)')
    ok('task-related' in t,'hyphen kept: task-related (both halves are words in the paper)')
    ok('high- and low-reward' in t,'"high- and low-" keeps its space')
    ok('significant' in t,'ligature fi becomes plain letters')
    ok('Understanding' in J("__jb[1]"),'no evidence and halves unknown: joined (Understanding)')
    ok(J("apJoinBreaks(['',null]).length")==2,'empty pages do not crash')
    ok(not errors,'no page errors: %s'%errors)
    b.close()
print('failures:',len(fails))
