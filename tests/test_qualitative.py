"""D5 qualitative record: approach, phases, themes from codes, quote identifier check, Findings draft; COREQ and SRQR."""
import sys, os, json
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
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Qual';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.design={type:'qualitative'};studySet(o)")
    # codes and tagged passages in a transcript
    J("setEditorHTML('<p>P01: <span class=\"qual-tag\" data-qcode=\"c1\">I cannot sleep the night before an exam.</span></p><p>P02: <span class=\"qual-tag\" data-qcode=\"c2\">My parents call every evening to ask about marks.</span></p>');docSaveBody(getEditorHTML())")
    J("qualCodesSet([{id:'c0',name:'Body under strain',parentId:null,color:'#f59e0b'},{id:'c1',name:'Lost sleep',parentId:'c0',color:'#10b981'},{id:'cP',name:'Family pressure',parentId:null,color:'#3b82f6'},{id:'c2',name:'Calls about marks',parentId:'cP',color:'#ef4444'}])")
    J("subOpen('collect','D5')"); pg.wait_for_timeout(200)
    ok('2 tagged passages' in J("document.getElementById('subMain').innerText") or '2 चिह्नित' in J("document.getElementById('subMain').innerText"),'D5 shows codes and tagged passages from the coding tool')
    ok(J("subState('D5').s")=='ns','D5 not done at first')
    J("d5FromCodes()")
    rows=J("logRows(studyGet(),'themes')")
    ok(len(rows)==2 and rows[0]['codes']=='Lost sleep' and 'cannot sleep' in rows[0]['quote'],'themes started from top-level codes, with their sub-codes and a quote')
    J("wPick('D5','ap','rta')")
    for ph in ['fam','code','gen','rev','def','rep']: J("wNestRedraw('D5','ph','%s',true)"%ph)
    J("logCell('themes',0,'def','Students describe exam stress through the body: lost sleep, headaches, no appetite.');logCell('themes',0,'who','P01')")
    J("logCell('themes',1,'def','Pressure from home arrives as daily questions about marks.');logCell('themes',1,'quote','Mr Sharma my father calls every evening at 9876543210.')")
    iss=J("d5Issues(studyGet())")
    ok(any('phone' in x for x in iss) and any('title with a name' in x for x in iss),'quote with a phone number and a name is caught')
    J("logCell('themes',1,'quote','My parents call every evening to ask about marks.');logCell('themes',1,'who','P02')")
    J("wPick('D5','refl','I am a teacher in a similar college, so I may hear complaints about parents more readily than other themes.')")
    ok(J("subState('D5').s")=='ns','not done until the no-names box is ticked')
    J("wPick('D5','idok',true)")
    ok(J("subState('D5').s")=='dn','D5 done with approach, six phases, two defined themes with clean quotes, reflexive notes')
    J("setEditorHTML('<p>x</p>');d5Insert()"); ed=J("getEditorHTML()")
    ok('<h2>Findings</h2>' in ed and 'reflexive thematic analysis' in ed and '(P02)' in ed and '<blockquote>' in ed,'Findings draft with themes and coded quotes')
    J("subOpen('review','F2')")
    ok(J("f2Suggest(studyGet())")=='coreq' and len(J("F2_LISTS.coreq.items"))==32 and len(J("F2_LISTS.srqr.items"))==21,'COREQ 32 items suggested for a qualitative design; SRQR 21 items available')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
