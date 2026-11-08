"""AI reply reading, with the kinds of replies models really send (build 2026.11.08za)."""
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
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1200)
    P=lambda s: pg.evaluate("s=>b3AiParse(s)",s)
    r=P('{"gap":"A.","sample":"B."}'); ok(r and r['gap']=='A.' and r['sample']=='B.' and r['stats']=='','plain JSON; missing stages become empty')
    r=P('Here is the JSON you asked for:\n```json\n{"gap":"A.","sample":"B."}\n```\nHope that helps.'); ok(r and r['sample']=='B.','prose and code fence around the JSON')
    r=P('{"gap":"A.","sample":"B.",}'); ok(r and r['gap']=='A.','trailing comma')
    r=P('{"gap":"A.","sample":"B. and more","stats":"Regres'); ok(r and r['sample']=='B. and more' and r['stats']=='','reply cut off: finished pairs kept, the cut one dropped')
    r=P('{"Gap":"A.","SAMPLE":"B."}'); ok(r and r['gap']=='A.' and r['sample']=='B.','keys in any case')
    r=P('{"gap":["First.","Second."],"sample":null,"stats":5}'); ok(r and r['gap']=='First. Second.' and r['sample']=='' and r['stats']=='','list joined, null and number become empty')
    r=P('{"gap":"He said \\"stop\\" and left."}'); ok(r and r['gap']=='He said "stop" and left.','escaped quotes inside a sentence')
    ok(P('I could not find anything.') is None and P('') is None and P(None) is None,'no JSON gives null')
    ok(P('[1,2,3]') is None,'an array is not an answer')
    # end to end: curly quotes and a line break in the paper do not stop a real sentence being kept
    J("window.confirm=()=>true;window.callAI=async function(){return window.__reply};0")
    J("openSaveAsProject();document.getElementById('sapName').value='P';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    AB='Method: We surveyed “412 students” at one hostel using the Pittsburgh Sleep\nQuality Index. Results: Poor sleep was common.'
    J("citSaveLib(%s)"%json.dumps([{"author":"A, B.","year":"2019","title":"Sleep","type":"Journal article","style":"apa","abs":AB,"scr":{"st":"included","why":""}}]))
    J("window.__reply=%s"%json.dumps('Sure!\n```json\n{"sample":"We surveyed \\"412 students\\" at one hostel using the Pittsburgh Sleep Quality Index.","design":"A randomised trial of 900 adults.",}\n```'))
    J("subOpen('lit','B3')"); pg.wait_for_timeout(500)
    J("b3AiAsk()"); pg.wait_for_timeout(500); J("b3AiRun()"); pg.wait_for_timeout(1500)
    c=json.loads(J("JSON.stringify(citGetLib()[0].cells||{})"))
    ok('sample' in c and c['sample']['by']=='ai','sentence that differs only in quotes and line break is kept')
    ok('design' not in c,'invented sentence thrown away')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
