"""Read in batches of ten (build 2026.11.08n)."""
import sys, os, json
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
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Queue';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("wPatch('A3','q','How does sleep quality affect exam stress in hostel students?')")
    lib=[]
    for i in range(12):
        t='Sleep quality and exam stress in hostel students %d'%i if i==7 else 'Unrelated topic number %d about gardening'%i
        lib.append({"author":"A, B.","year":"2020","title":t,"type":"Journal article","style":"apa","abs":"abstract %d"%i})
    J("citSaveLib(%s)"%json.dumps(lib))
    J("wPatch('B1','type','sys')"); J("subOpen('lit','B3')")
    T=lambda: J("document.getElementById('subMain').innerText")
    t=T()
    ok('Read in batches of ten' in t and '12 waiting' in t and 'showing 1–10' in t,'ten shown out of 12')
    first=J("document.querySelector('#subMain .sub-box div[style*=\"13.5px\"]').innerText")
    ok('Sleep quality and exam stress' in first,'the paper that fits the question is first: '+first[:50])
    cid=J("citGetLib()[7].cid")
    J("citScrSet(7,'st','included')"); J("subOpen('lit','B3')")
    ok('11 waiting' in T(),'a decided paper leaves the queue')
    J("b3QueueMore(10)")
    t=T(); ok('showing 11–11' in t and 'Next ten' not in t,'next ten shows the last one; no more button')
    ok('Back to the first ten' in t,'can go back')
    J("b3QueueMore(0)"); ok('showing 1–10' in T(),'back to the top')
    J("retrCacheSet('10.1234/x',true);var l=citGetLib();l[0].doi='10.1234/x';citSaveLib(l)"); J("subOpen('lit','B3')")
    ok('10 waiting' in T(),'a retracted paper is never offered')
    for i in range(12): J("citScrSet(%d,'st','included')"%i)
    J("subOpen('lit','B3')")
    ok('Nothing is waiting' in T(),'all decided: nothing waiting')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
