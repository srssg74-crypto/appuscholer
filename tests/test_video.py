"""Explain-as-a-video: selection → AI scene (stubbed) → checks → lecture theatre."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
S='/tmp/claude-0/-home-claude/d540b351-a2df-5fa6-9a88-226a4c6e6a4f/scratchpad/'
SRC='A p-value of .03 means that if the null hypothesis were true, data this extreme would appear about 3 times in 100 studies. It does not give the chance that the hypothesis is true.'
def scene(extra_num=False):
    sl=[{"who":"raj","board":["What a p-value says","p = .03"],"boardH":["p-value क्या बताती है","p = .03"],"say":"Today we read one sentence slowly. It says p equals .03.","sayH":"आज हम एक वाक्य धीरे-धीरे पढ़ेंगे। इसमें लिखा है p = .03।"},
        {"who":"tara","board":["Is it a 3% chance?",""],"boardH":["क्या यह 3% chance है?",""],"say":"Sir, does that mean a 3 percent chance that I am wrong?","sayH":"Sir, क्या इसका मतलब है कि मेरे ग़लत होने का 3 प्रतिशत chance है?"},
        {"who":"raj","board":["Null hypothesis =","nothing is happening"],"boardH":["Null hypothesis =","कुछ नहीं हो रहा"],"say":"First, the null hypothesis is the story that nothing is happening. In simple words, no real difference.","sayH":"पहले, null hypothesis वह कहानी है कि कुछ नहीं हो रहा। सरल शब्दों में, कोई असली फ़र्क़ नहीं।"},
        {"who":"raj","board":["3 times in 100 studies",""],"boardH":["100 में से 3 studies",""],"say":"If nothing were happening, data this extreme would appear about 3 times in 100 studies."+(" In 1990 this was shown by 45 labs." if extra_num else ""),"sayH":"अगर कुछ न हो रहा होता, तो इतना extreme data 100 में से लगभग 3 studies में आता।"},
        {"who":"dev","board":["So not the chance it is true?",""],"boardH":["तो सच होने का chance नहीं?",""],"say":"So it is not the chance that the hypothesis is true?","sayH":"तो यह hypothesis के सच होने का chance नहीं है?"},
        {"who":"raj","board":["Recap: p is about the data","not about the hypothesis"],"boardH":["सार: p data के बारे में","hypothesis के बारे में नहीं"],"say":"Exactly. The p-value is about the data, given the null hypothesis.","sayH":"बिल्कुल। p-value null hypothesis मानकर data के बारे में बताती है।"}]
    return json.dumps({"title":"Reading p = .03","titleH":"p = .03 को पढ़ना","slides":sl})
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    ok(J("!!document.querySelector('#selBubble button[onclick=\"vidMake()\"]')"),'video button in the selection bubble')
    J("window._calls=[];window._ans=[%s,%s];window.callAI=async(p,o)=>{window._calls.push(p);return window._ans.shift()};0"%(json.dumps(scene(True)),json.dumps(scene(False))))
    J("setEditorHTML('<p>%s</p>');const r=document.createRange();r.selectNodeContents(editor.querySelector('p'));const s=getSelection();s.removeAllRanges();s.addRange(r);savedRange=r.cloneRange()"%SRC)
    J("vidMake()"); pg.wait_for_timeout(1500)
    calls=J("window._calls")
    ok(len(calls)==2 and 'Use only numbers from the passage' in calls[1] and '1990' in calls[1],'number not in the selection (1990, 45) caught; AI asked again')
    ok(SRC in calls[0] and 'Use ONLY what the passage says' in calls[0],'only the selected lines go to the AI, with the lecture rules')
    v=J("vidList()[0]")
    ok(v and len(v['slides'])==7 and v['slides'][-1]['t']=='Check it' and not v['flags'],"scene saved with the app's own closing check slide")
    ok(J("AP.les.lib")=='lib_'+v['id'] and J("document.getElementById('libDlg').open"),'opens in the lecture theatre')
    ok(J("AP_LIBGROUPS[0].g")=='mine' and J("AP_LECT['lib_'+vidList()[0].id].length")==7,'listed under My explanations')
    pg.wait_for_timeout(800); pg.screenshot(path=S+'video.png')
    J("apLibClose()")
    # cannot / too short
    J("window._ans=[JSON.stringify({cannot:'The passage is a heading only.'})];setEditorHTML('<p>Results of the second study were mixed overall.</p>');const r=document.createRange();r.selectNodeContents(editor.querySelector('p'));const s=getSelection();s.removeAllRanges();s.addRange(r);savedRange=r.cloneRange();window._t='';const st=showToast;window.showToast=m=>{window._t=m;st(m)};0")
    J("vidMake()"); pg.wait_for_timeout(600)
    ok('heading only' in J("window._t"),'AI saying it cannot explain is passed on, nothing made')
    ok(J("aiuClassify(window._calls[0])&&aiuClassify(window._calls[0]).k").startswith('a classroom'),'AI use logged for the E8 statement')
    # reload: kept
    pg.reload(); pg.wait_for_timeout(1500)
    ok(J("!!AP_LIBMAP['lib_'+vidList()[0].id]"),'explanation still there after reload')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
