"""B1 'Help me choose' (build 2026.11.08e): plain questions give a suggested review type with reasons, checklist and
protocol, by rules only. Use this suggestion fills type and reason but never overwrites the student's own reason."""
import sys, os
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
    J("window.confirm=()=>true;window.__ai=0;window.callAI=async function(){window.__ai++;return ''}")
    J("openSaveAsProject();document.getElementById('sapName').value='B1 help';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("subOpen('lit','B1')")
    ai0=J("window.__ai")
    T=lambda: J("document.getElementById('subMain').innerText")
    ok('Help me choose' in T() and J("document.getElementById('b1Help').open")==True,'helper shows, open while no type is chosen')
    ok('5. Do most studies' not in T(),'question 5 hidden until meta-analysis is the goal')
    S=lambda: J("JSON.stringify(b1Suggest((wGet(studyGet()).B1||{}).help,false))")
    import json
    sg=lambda: json.loads(S()) if S()!='null' else None
    ok(sg() is None and 'Suggestion, worked out' not in T(),'no suggestion before the first answer')
    a=lambda k,v: J("wNestRedraw('B1','help','%s','%s')"%(k,v))
    a('goal','answer'); a('focus','yes'); a('team','two'); a('time','gt6')
    ok(sg()['type']=='sys' and 'PRISMA 2020' in T() and 'Systematic review' in T(),'focused question, two screeners, time: systematic review, PRISMA 2020')
    a('team','solo')
    ok(any('two people to screen' in x for x in sg()['notes']),'screening alone: note about PRISMA asking for two screeners')
    a('focus','notyet')
    ok(sg()['type']=='scop' and any('sharpen the question' in x for x in sg()['notes']),'question not yet focused: scoping review, with the A3 note')
    a('focus','yes'); a('time','lt2')
    s=sg(); ok(s['type']=='narr' and any('under two months' in x for x in s['reasons']) and any('systematic review usually takes several months' in x for x in s['notes']),'under two months: narrative review, with the reason and the time note')
    ok(any('full search log in B2' in x for x in s['notes']),'narrative: full search log note (agreed 8 Nov)')
    a('time','gt6'); a('goal','number')
    ok('5. Do most studies' in T(),'question 5 shows for meta-analysis')
    a('combine','no')
    ok(sg()['type']=='sys' and any('without meta-analysis' in x for x in sg()['reasons']),'numbers cannot be combined: systematic review without meta-analysis')
    a('combine','dk')
    s=sg(); ok(s['type']=='meta' and any('open three likely papers' in x for x in s['notes']) and any('not in Stats Lab yet' in x for x in s['notes']),'meta-analysis: check three papers first, and pooling is honestly not in Stats Lab yet')
    a('goal','map')
    ok(sg()['type']=='scop' and 'OSF' in sg()['proto'] and 'PRISMA-ScR' in sg()['guide'],'map of the field: scoping review, OSF, PRISMA-ScR')
    # use the suggestion
    J("b1UseSug()")
    b1=json.loads(J("JSON.stringify(wGet(studyGet()).B1)"))
    ok(b1.get('type')=='scop' and 'scoping review fits' in b1.get('why',''),'Use this suggestion fills type and reason')
    ok(b1Ok:=J("b1Ok(studyGet())") is not None,'b1Ok still runs')
    J("wPatch('B1','why','My own words: I want to see what has been studied on exam stress in Indian colleges.');wRedraw()")
    a('goal','answer'); J("b1UseSug()")
    b1=json.loads(J("JSON.stringify(wGet(studyGet()).B1)"))
    ok(b1.get('type')=='sys' and b1.get('why','').startswith('My own words'),'a reason the student wrote is never overwritten')
    ok('suggestion differs' not in T(),'no mismatch note when choice equals suggestion')
    J("wPick('B1','type','narr')")
    ok('suggestion differs from your choice' in T() and J("document.getElementById('b1Help').open")==False,'student can overrule; helper closes and notes the difference')
    # clicking a chosen answer again clears it
    J("wNestRedraw('B1','help','goal','')")
    ok(sg() is None,'an answer can be cleared')
    # Hindi
    if J("getLang()")!='hi': J("toggleLang()")
    J("subOpen('lit','B1')")
    if J("studyHi()"):
        a('goal','map'); t=J("document.getElementById('b1Help').textContent")
        ok('चुनने में मदद' in t and 'scoping review ठीक है' in t and 'PROSPERO scoping review नहीं लेता' in t,'Hindi: helper, reasons and protocol in Hindi')
    else:
        print('SKIP Hindi (no setLang in this build)')
    ok(J("window.__ai")==ai0,'no AI call anywhere in the helper')
    real=[e for e in errors if 'favicon' not in e[1]]
    ok(not real,'no page errors %s'%real[:3])
    b.close()
print('failures:',len(fails))
