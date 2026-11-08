"""PDF page reading order with columns (build 2026.11.08d). Synthetic pages, no paper text in the repo."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
JS_ITEMS="""
(function(){
  function it(s,x,y,w,rot){return{str:s,transform:rot?[0,12,-12,0,x,y]:[12,0,0,12,x,y],width:w,height:12}}
  const left=[],right=[];
  for(let i=0;i<20;i++){left.push(it('L'+i+' alpha beta gamma delta',50,640-i*14,235));right.push(it('R'+i+' one two three four',325,640-i*14,235))}
  window.__two=left.concat(right).sort(()=>Math.random()-0.5);  /* order in the file does not matter */
  window.__full=[it('TITLE of the whole paper spans both columns right across the page now',50,740,500)].concat(window.__two);
  const one=[];for(let i=0;i<25;i++)one.push(it('S'+i+' single column line with enough words to fill the width of the page body',60,700-i*14,470));
  window.__one=one;
  window.__side=window.__two.concat([it('Downloaded from a journal site',590,400,150,true)]);
})()
"""
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J(JS_ITEMS)
    r=J("(function(){const o=apPageOrder(__two,[0,0,612,792]);return{t:o.text,c:o.cols}})()")
    L=r['t'].split('\n')
    ok(r['c']==2,'two columns found')
    ok(L[0].startswith('L0 ') and L[19].startswith('L19 ') and L[20].startswith('R0 ') and L[39].startswith('R19 '),'whole left column first, then whole right column')
    r=J("apPageOrder(__full,[0,0,612,792]).text").split('\n')
    ok(r[0].startswith('TITLE') and r[1].startswith('L0 ') and r[21].startswith('R0 '),'full-width title stays on top, then left, then right')
    r=J("(function(){const o=apPageOrder(__one,[0,0,612,792]);return{t:o.text,c:o.cols}})()")
    ok(r['c']==1 and r['t'].split('\n')[0].startswith('S0 ') and r['t'].split('\n')[24].startswith('S24 '),'single column page stays single column and in order')
    ok('Downloaded' not in J("apPageOrder(__side,[0,0,612,792]).text"),'vertical side note is left out')
    ok(J("apPageOrder([],[0,0,612,792]).scanned")==True and J("apPageOrder([{str:' ',transform:[12,0,0,12,1,1],width:3}],[0,0,612,792]).scanned")==True,'empty page is reported as no text')
    ok(J("apPageOrder(__two,[0,0,612,792]).text.split(/\\s+/).filter(Boolean).length")==J("__two.reduce((n,i)=>n+i.str.split(/\\s+/).length,0)"),'no word is lost')
    ok(not errors,'no page errors: %s'%errors)
    b.close()
print('failures:',len(fails))
