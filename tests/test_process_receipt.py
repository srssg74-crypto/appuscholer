"""Process receipt: built from the app's own records, with a fingerprint the downloaded file checks itself (build 2026.11.02i)."""
import sys, os, re, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true;LS.set('appu_me',JSON.stringify({name:'Asha Verma',pos:'',role:'student',course:'pg'}))")
    J("openNewProjectDirect();document.getElementById('sapName').value='Receipt';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("""const o=studyGet();o.idea={topic:'Sleep and exam anxiety',savedAt:Date.now()-20*864e5};o.design={type:'survey',hyp:'H1: Less sleep goes with more anxiety.',vars:[{name:'Exam anxiety',role:'outcome',type:'score',scale:'GAD7'}]};
      o.ethics={route:'app',cm:{name:'IEC',inst:'Uni',addr:'Jaipur',email:'iec@uni.ac.in'},lt:{no:'IEC/41',date:new Date(Date.now()-15*864e5).toISOString().slice(0,10)},risk:{}};studySet(o);
      logSaveRows('aplan',[{date:new Date(Date.now()-18*864e5).toISOString().slice(0,10),h:'H1: Less sleep goes with more anxiety.',dv:'GAD-7 total',test:'Pearson r',es:'r',miss:'Complete cases',kind:'Main'}]);
      logSaveRows('clean',[{date:new Date().toISOString().slice(0,10),step:'Duplicate',what:'rows 144',n:'1',why:'Exact copy of an earlier row'}])""")
    J("document.getElementById('statsPaste').value='sleep,anx\\n6,8\\n7,5\\n5,11\\n8,4\\n6,9';statsParse()")
    J("setEditorHTML('<p>'+'I wrote this myself about sleep and exams. '.repeat(10)+'</p><p><span class=\"ai-ins\" data-h=\"x\">An AI sentence that was later changed by the student here.</span></p>');docSaveBody(getEditorHTML())")
    J("prOpen()"); pg.wait_for_timeout(500)
    t=J("document.getElementById('prDlg').innerText")
    ok('was written before the data was first loaded' in t,'plan before data is confirmed')
    ok('ethics approval' in t.lower() and 'came before the data' in t,'approval before data is confirmed')
    ok('Exact copy of an earlier row' in t,'cleaning reasons are in the timeline')
    ok('were not inserted by AI' in t and 'rewritten' in t,'writing share is reported')
    h=J("window._pr.h")
    ok(bool(re.fullmatch(r'[0-9a-f]{64}',h or '')),'a SHA-256 fingerprint is shown')
    html=J("prFileHTML()")
    d=os.path.dirname(os.path.abspath(__file__));f1=os.path.join(d,'_tmp_receipt.html');open(f1,'w').write(html)
    pg2=b.contexts[0].new_page(); pg2.goto('http://localhost:8765/tests/_tmp_receipt.html'); pg2.wait_for_timeout(600)
    ok('has not been edited' in pg2.inner_text('#v'),'the downloaded receipt confirms its own fingerprint')
    f2=os.path.join(d,'_tmp_receipt2.html');open(f2,'w').write(html.replace('var T="PROCESS RECEIPT','var T="PROCESS RECEIPT EDITED'))
    pg2.goto('http://localhost:8765/tests/_tmp_receipt2.html'); pg2.wait_for_timeout(600)
    ok('was changed' in pg2.inner_text('#v'),'an edited receipt says so')
    os.remove(f1);os.remove(f2)
    J("document.getElementById('prDlg').close();subOpen('review','F1')"); pg.wait_for_timeout(200)
    ok('Make my process receipt' in J("document.getElementById('subMain').innerText"),'F1 offers the receipt')
    b.close()
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:2])
print('FAILED' if fails else 'ALL PASS', len(fails))
