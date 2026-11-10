"""A first page written body-first (title, drop cap and abstract come later in the file) is read in page order;
drop caps are joined; running heads are dropped (build 2026.11.10o). Made-up pages only."""
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
  function it(s,x,y,h,eol){return{str:s,transform:[h||10,0,0,h||10,x,y],width:s.length*5,height:h||10,hasEOL:!!eol}}
  const body=[];for(let i=0;i<14;i++)body.push(it(i==0?'nxiety is a state that many people know and describe daily in plain words':'line '+i+' of the body text with enough words to fill a line of the column',i==0?343:301,537-i*12,10,1));
  const title=[it('A Made-up Study of Worry',50,671,25,1),it('Jane Roe, MD',50,590,15,0)];
  const dropcap=[it('A',318,537,60,0)];
  const abs=[];for(let i=0;i<4;i++)abs.push(it('abstract line '+i+' with words that run across the whole width of the page here',53,273-i*12,10,1));
  window.__p1={view:[0,0,595,765],items:[it('2 4 9',285,31,12,0)].concat(body,title,dropcap,abs)};
  window.__p1ok={view:[0,0,595,765],items:title.concat(dropcap,body,abs)};
  const mk=(n,tail)=>({view:[0,0,595,765],items:[it('Running Journal Name',50,740,8,1),it('Made-up study - Roe',250,725,8,1),it('Para one anxiety is discussed here at length in this page',50,600,10,1),it('Para two anxiety again with more words',50,588,10,1),it(String(n),285,31,12,0)].concat(tail||[])});
  window.__pages=[mk(250),mk(251),mk(252),mk(253)];
})()
"""
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J(JS)
    ok(J("apOutOfOrder(__p1.items,__p1.view)")==True,'body-first page is detected')
    ok(J("apOutOfOrder(__p1ok.items,__p1ok.view)")==False,'a page already in order is left alone')
    t=J("apPageText(__p1.items,__p1.view).text")
    ok(t.index('A Made-up Study of Worry')<t.index('nxiety is a state'),'title comes before the body')
    ok(t.index('Jane Roe')<t.index('nxiety is a state'),'author comes before the body')
    # drop cap
    fixed=J("apFixDropCaps([apPageText(__p1.items,__p1.view).text,'anxiety is here and anxiety is there'])[0]")
    ok('Anxiety is a state' in fixed and 'A nxiety' not in fixed,'drop cap A is joined to nxiety')
    ok('A brief treatment' in J("apFixDropCaps(['A brief treatment of anxiety is given','brief is a word'])[0]"),'a real "A brief" is left alone')
    # running heads
    r=J("apDropRunningHeads(__pages.map(d=>apPageText(d.items,d.view).text))")
    ok(all('Running Journal Name' not in x and 'Made-up study - Roe' not in x for x in r),'repeating head lines are dropped')
    ok(all('Para one anxiety' in x for x in r),'body lines stay')
    ok(all(not x.strip().split('\n')[-1].strip().isdigit() for x in r),'a counting page number is dropped')
    one=J("apDropRunningHeads([__pages[0].items.map(i=>i.str).join('\\n')])")
    ok('Running Journal Name' in one[0],'a single page keeps its first line')
    ok(not [e for e in errors if 'Failed to load resource' not in str(e)],'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
