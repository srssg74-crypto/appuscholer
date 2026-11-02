"""Free AI in two minutes: the key wizard recognises, tests and saves a key (build 2026.11.02d)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
GOOD='AIza'+'x'*35
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    calls=[]
    def gem(route):
        calls.append(route.request.url)
        bad='key=AIzaBAD' in route.request.url or 'AIzaBAD' in (route.request.headers.get('x-goog-api-key') or '')
        if bad: return route.fulfill(status=400,content_type='application/json',body=json.dumps({'error':{'code':400,'message':'API key not valid. Please pass a valid API key.','status':'INVALID_ARGUMENT'}}))
        route.fulfill(status=200,content_type='application/json',body=json.dumps({'candidates':[{'content':{'parts':[{'text':'OK'}]},'finishReason':'STOP'}]}))
    pg.context.route('**/generativelanguage.googleapis.com/**',gem)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    ok(J("keyGuessProv('%s')"%GOOD)=='gemini' and J("keyGuessProv('gsk_abcdefghijklmnopqrstuvwxyz')")=='groq' and J("keyGuessProv('sk-or-v1-abc')")=='openrouter' and J("keyGuessProv('sk-ant-abc')")=='claude' and J("keyGuessProv('hello')")=='','keys are recognised by their first letters')
    J("LS.rm('appu_key_gemini');LS.set('appu_provider','gemini')")
    J("callAI('hi').catch(()=>{})"); pg.wait_for_timeout(400)
    ok(J("!!(document.getElementById('keyWizDlg')||{}).open"),'an AI button without a key opens the wizard')
    ok(J("document.getElementById('kwGo').disabled"),'Test and save waits for a key')
    pg.fill('#kwIn','AIzaBAD'+'y'*32); pg.wait_for_timeout(100)
    ok('Google Gemini' in J("document.getElementById('kwWho').textContent"),'pasted key is named')
    J("keyWizSave()"); pg.wait_for_timeout(1200)
    ok('✗' in J("document.getElementById('kwOut').textContent") and not J("LS.get('appu_key_gemini')"),'a bad key is reported and not saved: %s'%J("document.getElementById('kwOut').textContent")[:120])
    pg.fill('#kwIn',GOOD); pg.wait_for_timeout(100)
    J("keyWizSave()"); pg.wait_for_timeout(1200)
    ok(J("LS.get('appu_key_gemini')")==GOOD and J("getProv()")=='gemini','a good key is tested and saved')
    pg.wait_for_timeout(800)
    ok(not J("document.getElementById('keyWizDlg').open"),'the wizard closes itself')
    ok(len(calls)>=2,'the test request went to Google')
    J("document.getElementById('welcomeDlg').showModal()")
    ok('Turn on free AI' in J("document.getElementById('welcomeDlg').innerText"),'welcome points to the wizard')
    b.close()
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:2])
print('FAILED' if fails else 'ALL PASS', len(fails))
