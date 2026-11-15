"""Reading shelf: reported statistics checked against each other (t, F, chi-square with their p)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
root=os.path.join(os.path.dirname(__file__),'..')
html=open(os.path.join(root,'index.html'),encoding='utf-8').read()
for f in ('statsfind','consistency'):
    mod=open(os.path.join(root,'tools','stats',f+'.js'),encoding='utf-8').read().rstrip('\n')
    ok(mod in html,'index.html carries %s.js, identical to the file'%f)
GOOD="Anxiety fell, t(48) = 2.31, p = .025, and sleep rose, F(2, 87) = 4.10, p = .020."
BAD ="The groups differed, t(48) = 2.31, p = .005. A second test gave F(1, 130) = 6.14, p = .001 (R 2 Adjusted = 0.10). A third, t(48) = 1.50, p = .03."
ADJ ="After Bonferroni correction, t(64) = 2.10, p = .001 (adjusted)."
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Cs';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("shOpen()"); pg.wait_for_timeout(400)
    def paper(id,pages):
        J("(async()=>{await shPut({id:'%s',title:'%s',file:'a.pdf',size:9,added:'2026-11-15',pages:%s,total:%d,notes:[],cells:{},sections:[]});await shRefresh();shRead('%s',1)})()"%(id,id,json.dumps(pages),len(pages),id)); pg.wait_for_timeout(600)
        J("document.querySelectorAll('#shBody details').forEach(d=>d.open=true)")
        return J("document.getElementById('shBody').innerText")
    t=paper('good',[GOOD])
    ok('Do the numbers agree?' in t and '2 checked' in t,'a paper with two pairs shows the check: two checked')
    ok('agrees with that test statistic' in t,'consistent pairs say so')
    t=paper('bad',["Intro text. "*20,BAD])
    ok('3 to look at' in t or '2 to look at' in t,'flagged pairs are counted: %s'%[l for l in t.split('\n') if 'to look at' in l])
    ok('t(48) = 1.50, p = .03' in t and 'changes whether p is below .05' in t,'a decision error is marked')
    ok('The test statistic gives p about' in t,'the computed p is shown')
    J("Array.from(document.querySelectorAll('#shBody details button')).find(x=>x.title==='Go to page 2'&&x.closest('details').innerText.indexOf('Do the numbers agree?')===0).click()"); pg.wait_for_timeout(300)
    ok(J("SH.page")==2,'tapping a flagged line goes to its page')
    t=paper('adj',[ADJ])
    ok('1 checked' in t and 'adjusted, so a difference is expected' in t and '1 to look at' not in t,'an adjusted p is not flagged')
    t=paper('none',["No tests here, only prose about the sample. "*10])
    ok('Do the numbers agree?' not in t,'no tests, no check')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
