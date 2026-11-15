"""Reading shelf: Markdown import. Pages from markers, sections from headings, no page picture, honest note when the file has no page numbers."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
root=os.path.join(os.path.dirname(__file__),'..')
mod=open(os.path.join(root,'tools','markdown','mdpages.js'),encoding='utf-8').read().rstrip('\n')
html=open(os.path.join(root,'index.html'),encoding='utf-8').read()
ok(mod in html,'index.html carries the Markdown reader, identical to tools/markdown/mdpages.js')
W="Participants were students from three colleges and completed the scale twice, a week apart. "
MD1="# Sleep and Exam Anxiety\n\n<!-- page 1 -->\n## Abstract\n"+W*3+"\n\n<!-- page 2 -->\n## Methods\n### Participants\nN = 120. "+W*3+"\n\n<!-- page 3 -->\n## Results\nr = -.41, p < .001. "+W*3+"\n"
MD2="## Introduction\n"+(W*40+"\n\n")*3+"## Methods\n"+(W*40+"\n\n")*3
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Md';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("shOpen()"); pg.wait_for_timeout(400)
    J("(async()=>{const f=new File([%s],'ocr.md',{type:'text/markdown'});await shAddFiles({files:[f],value:''})})()"%json.dumps(MD1)); pg.wait_for_timeout(1200)
    rec=J("SH.papers[0]")
    ok(rec['md']=='markers' and len(rec['pages'])==3,'markers: 3 pages stored, md flag set')
    ok(rec['title']=='Sleep and Exam Anxiety','title from the single # heading')
    ok([s['kind'] for s in rec['sections']]==['abstract','methods','results'],'sections from headings: %s'%[s['kind'] for s in rec['sections']])
    ok(rec['sections'][1]['subs'][0]['title']=='Participants','subsection kept')
    J("shRead(SH.papers[0].id,2)"); pg.wait_for_timeout(500)
    t=J("document.getElementById('shBody').innerText")
    ok('Imported from a Markdown file' in t and 'check them against the printed paper' in t,'reader says where the page numbers come from')
    ok('Sections (3)' in t,'Sections list shown')
    J("document.querySelector('#shBody details').open=true")
    J("Array.from(document.querySelectorAll('#shBody details button')).find(x=>x.textContent.startsWith('Results')).click()"); pg.wait_for_timeout(300)
    ok(J("SH.page")==3,'tapping Results jumps to page 3')
    J("shImgToggle()"); pg.wait_for_timeout(400)
    ok('no page picture' in J("document.getElementById('shBody').innerText"),'no page picture is said plainly')
    ok('Statistics in this paper' in J("document.getElementById('shBody').innerText"),'statistics list works on imported text')
    # no markers
    J("(async()=>{const f=new File([%s],'plain.txt',{type:'text/plain'});await shAddFiles({files:[f],value:''})})()"%json.dumps(MD2)); pg.wait_for_timeout(1000)
    r2=J("SH.papers.find(x=>x.file==='plain.txt')")
    ok(r2 and r2['md']=='none' and len(r2['pages'])>=2,'no markers: cut into parts')
    J("shRead(SH.papers.find(x=>x.file==='plain.txt').id,1)"); pg.wait_for_timeout(500)
    ok('no page numbers' in J("document.getElementById('shBody').innerText") and 'Do not cite them' in J("document.getElementById('shBody').innerText"),'a file with no page numbers warns against citing them')
    # same file twice, tiny file, wrong type
    J("(async()=>{const f=new File([%s],'ocr.md',{type:'text/markdown'});await shAddFiles({files:[f],value:''})})()"%json.dumps(MD1)); pg.wait_for_timeout(600)
    ok('already on the shelf' in J("SH.status"),'the same file is not added twice')
    J("(async()=>{await shAddFiles({files:[new File(['hi'],'tiny.md')],value:''});})()"); pg.wait_for_timeout(500)
    ok('too little text' in J("SH.status"),'a tiny file is refused')
    J("(async()=>{await shAddFiles({files:[new File(['x'],'a.docx')],value:''});})()"); pg.wait_for_timeout(500)
    ok('not a PDF or a Markdown file' in J("SH.status"),'other types are refused with a clear message')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
