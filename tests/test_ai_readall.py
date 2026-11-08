"""AI reading of all included papers (build 2026.11.08q): count first, agree, quotes checked, own words kept."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
AB='Background: Sleep affects learning. Few studies have examined hostel students. Methods: A cross-sectional survey of 412 students (58% women) used the Pittsburgh Sleep Quality Index. Data were analysed with SPSS using regression. Results: Each hour less sleep was linked to lower GPA (r = .32, p < .001). Limitations include self-report.'
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true;window.__ai=0;window.__prompts=[];window.callAI=async function(pr){window.__ai++;window.__prompts.push(pr);return window.__reply};0")
    J("openSaveAsProject();document.getElementById('sapName').value='AI';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    lib=[{"author":"A, B.","year":"2019","title":"Sleep and grades","type":"Journal article","style":"apa","abs":AB,"scr":{"st":"included","why":""}},
         {"author":"C, D.","year":"2020","title":"Included no text","type":"Journal article","style":"apa","scr":{"st":"included","why":""}},
         {"author":"E, F.","year":"2021","title":"Excluded one","type":"Journal article","style":"apa","abs":AB,"scr":{"st":"excluded","why":"x","rd":"1"}},
         {"author":"G, H.","year":"2022","title":"Shelf paper","type":"Journal article","style":"apa","scr":{"st":"included","why":""}}]
    J("citSaveLib(%s)"%json.dumps(lib))
    # shelf paper with full text
    J("(async()=>{await shPut({id:'pS',title:'Shelf paper',file:'s.pdf',size:1,added:'2026-11-08',pages:['Introduction. Wide gap in the field.','Participants were 96 nurses recruited from two hospitals.'],total:2,notes:[],cells:{}});const l=citGetLib();l[3].shelf='pS';citSaveLib(l)})()"); pg.wait_for_timeout(500)
    reply=json.dumps({"gap":"Few studies have examined hostel students.","sample":"A cross-sectional survey of 412 students (58% women) used the Pittsburgh Sleep Quality Index.","stats":"Regression was done in SPSS version 99 on Mars.","results":"Each hour less sleep was linked to lower GPA (r = .32, p < .001).","limits":""})
    J("window.__reply=%s"%json.dumps(reply))
    J("subOpen('lit','B3')")
    ok('Read all included papers (AI)' in J("document.getElementById('subMain').innerText"),'button shown')
    J("b3AiAsk()"); pg.wait_for_timeout(800)
    t=J("document.getElementById('subMain').innerText")
    ok('2 included papers will be read (1 from the full text on your shelf, 1 from the abstract only)' in t and '2 AI calls' in t,'count shown first')
    ok('1 included paper(s) have no text' in t,'paper without text named as skipped')
    ok(J("window.__ai")==0,'no AI call before the student agrees')
    J("b3AiRun()"); pg.wait_for_timeout(1500)
    ok(J("window.__ai")==2,'two calls, one per paper with text')
    L=json.loads(J("JSON.stringify(citGetLib())")); c=L[0]['cells']
    ok(c['sample']['by']=='ai' and '412' in c['sample']['t'],'real quote kept, labelled AI')
    ok('stats' not in c,'sentence not found in the paper is dropped')
    ok('cells' not in L[2] and 'cells' not in L[1],'excluded and no-text papers untouched')
    ok(J("window.__prompts[1]").count('Participants were 96 nurses')==1,'shelf paper read from its full text')
    t=J("document.getElementById('subMain').innerText")
    ok('dropped because they were not in the paper' in t,'summary reports what was dropped')
    # own words survive
    J("b3Cell(0,'gap','my own gap words')"); J("b3AiAsk()"); pg.wait_for_timeout(600); J("b3AiRun()"); pg.wait_for_timeout(1500)
    L=json.loads(J("JSON.stringify(citGetLib())")); ok(L[0]['cells']['gap']=={'t':'my own gap words','by':'me'},'my words never overwritten')
    # error stops
    J("window.callAI=async function(){throw new Error('limit')};0"); J("b3AiAsk()"); pg.wait_for_timeout(600); J("b3AiRun()"); pg.wait_for_timeout(1200)
    ok('Stopped' in J("document.getElementById('subMain').innerText"),'an AI error stops the run with a message')
    J("b3AiAsk()"); pg.wait_for_timeout(500); J("b3AiCancel()")
    ok('Before this runs' not in J("document.getElementById('subMain').innerText"),'cancel closes the box')
    errs=[e for e in errors if 'limit' not in str(e)]
    ok(not errs,'no page errors %s'%errs)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
