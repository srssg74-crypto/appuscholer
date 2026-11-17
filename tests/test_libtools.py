"""Library duplicates and merge, My prompts in Ask, shared links (Android share target), accessibility in Help."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright

fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

LIB = [
 {'cid':'cAAA1','author':'Sharma, R.; Gaur, S.','year':'2021','title':'Exam anxiety in Indian college students','source':'Indian J Psychol','doi':'10.1234/ijp.2021.5','type':'Journal article'},
 {'cid':'cBBB2','author':'Sharma, R.','year':'2021','title':'Exam Anxiety in Indian College Students.','source':'','volume':'12','pages':'4-9','doi':'https://doi.org/10.1234/IJP.2021.5','type':'Journal article','notes':'Read twice'},
 {'cid':'cCCC3','author':'Lee, K.','year':'2019','title':'Sleep and memory in adolescents: a cohort study','doi':'10.5555/pre.1','type':'Journal article'},
 {'cid':'cDDD4','author':'Lee, K.','year':'2019','title':'Sleep and memory in adolescents: a cohort study','doi':'10.5555/pub.9','type':'Journal article'},
 {'cid':'cEEE5','author':'Rao, P.','year':'2018','title':'Mindfulness training for nursing students in Jaipur hospitals','type':'Journal article'},
 {'cid':'cFFF6','author':'Rao, P.','year':'2018','title':'Mindfulness training for nursing students in Jaipur hospital','type':'Journal article'},
 {'cid':'cGGG7','author':'Kumar, A.','year':'2020','title':'Social media use and loneliness','type':'Journal article'},
]

with sync_playwright() as p:
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 1366, 'height': 900})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    pg.evaluate("l=>citSaveLib(l)", LIB)
    pairs = pg.evaluate("dupScan(citGetLib(),true).map(x=>[citGetLib()[x[0]].cid,citGetLib()[x[1]].cid,x[2],x[3]])")
    keys = {tuple(sorted(x[:2])): (x[2], x[3]) for x in pairs}
    ok(('cAAA1','cBBB2') in keys and keys[('cAAA1','cBBB2')][0] == 'doi', 'DOI written two ways is found: %s' % pairs)
    ok(keys.get(('cCCC3','cDDD4'), ('',''))[1] == 'twodoi', 'same title with two DOIs carries the preprint warning')
    ok(('cEEE5','cFFF6') in keys, 'near-identical title with same author and year is found')
    ok(not any('cGGG7' in k for k in keys), 'an unrelated paper is not paired')
    cheap = pg.evaluate("dupScan(citGetLib(),false).length")
    ok(cheap == 2, 'quick check on render finds the exact ones only (%s)' % cheap)
    pg.evaluate("showTool('cite')"); pg.wait_for_timeout(300)
    ok('look like the same paper' in pg.inner_text('#citDupSummary'), 'library shows a duplicates line')

    # import of the same DOI in another spelling is skipped
    added = pg.evaluate("citLibPush([{author:'Sharma, R.',year:'2021',title:'Different words',doi:'doi:10.1234/ijp.2021.5'}])")
    ok(added == 0, 'import skips a DOI already in the library (doi: prefix)')

    # a document cites the copy that will be dropped; the shelf links it too
    pg.evaluate("""async()=>{setEditorHTML('<p>Text '+citSpanHTML('cBBB2')+' and '+'<span class="cit" contenteditable="false" data-cid="cAAA1,cBBB2">…</span></p>');
       localStorage.setItem('appu_test_study',JSON.stringify({papers:['cBBB2','cGGG7']}));
       await shPut({id:'shX',title:'Exam anxiety',lib:'cBBB2'})}""")
    pg.wait_for_timeout(300)
    pg.evaluate("dupOpen()"); pg.wait_for_timeout(200)
    ok(pg.is_visible('#dupDlg'), 'duplicates window opens')
    txt = pg.inner_text('#dupDlg')
    ok('preprint' in txt and 'Not the same' in txt, 'window shows the preprint warning and the Not the same choice')
    ok('Volume' in txt and 'Pages' in txt, 'keep button lists the fields it will fill')
    pg.evaluate("dupMerge('cAAA1','cBBB2')"); pg.wait_for_timeout(500)
    lib = pg.evaluate("citGetLib()")
    a = [d for d in lib if d['cid'] == 'cAAA1']
    ok(len(lib) == 6 and not any(d['cid'] == 'cBBB2' for d in lib), 'merge leaves one copy')
    ok(a and a[0].get('volume') == '12' and a[0].get('pages') == '4-9' and a[0].get('source') == 'Indian J Psychol', 'kept copy keeps its fields and gains the missing ones')
    ok(a and a[0].get('notes') == 'Read twice', 'notes move to the kept copy')
    cids = pg.evaluate("[...editor.querySelectorAll('span.cit')].map(s=>s.getAttribute('data-cid'))")
    ok(cids == ['cAAA1', 'cAAA1'], 'citations in the open document point to the kept copy, no doubled id: %s' % cids)
    st = pg.evaluate("JSON.parse(localStorage.getItem('appu_test_study'))")
    ok(st['papers'] == ['cAAA1', 'cGGG7'], 'stored study records move to the kept copy')
    sh = pg.evaluate("async()=>(await shAll()).find(p=>p.id==='shX').lib")
    ok(sh == 'cAAA1', 'reading shelf paper moves to the kept copy')
    pg.evaluate("dupNotSame('cCCC3','cDDD4')"); pg.wait_for_timeout(200)
    left = pg.evaluate("dupScan(citGetLib(),true).map(x=>[citGetLib()[x[0]].cid,citGetLib()[x[1]].cid])")
    ok(not any(set(x) == {'cCCC3','cDDD4'} for x in left), 'Not the same is remembered')
    pg.evaluate("document.getElementById('dupDlg').close()")

    # My prompts
    pg.evaluate("showTool('chat')"); pg.wait_for_timeout(200)
    ok(pg.is_visible('#mpRow'), 'Ask panel shows the prompt buttons')
    pg.fill('#chatIn', '')
    pg.type('#chatIn', '/vari'); pg.wait_for_timeout(150)
    ok(pg.is_visible('#mpMenu') and 'Find my variables' in pg.inner_text('#mpMenu'), 'typing / filters saved prompts')
    pg.press('#chatIn', 'Enter'); pg.wait_for_timeout(150)
    v = pg.input_value('#chatIn')
    ok(v.startswith('In this study idea'), 'Enter puts the prompt in the box instead of sending')
    ok(pg.evaluate("document.querySelectorAll('#chatLog .msg').length") == 0, 'nothing was sent')
    pg.fill('#chatIn', 'Compare these two scales for me: ')
    pg.evaluate("window.prompt=()=>'Compare scales'")
    pg.evaluate("mpSaveCurrent()"); pg.wait_for_timeout(150)
    saved = pg.evaluate("JSON.parse(localStorage.getItem('appu_myprompts'))")
    ok(saved and saved[0]['name'] == 'Compare scales' and len(saved) == 5, 'Save this question keeps it first, starters kept')
    pg.evaluate("mpManage()"); pg.wait_for_timeout(150)
    ok(pg.is_visible('#mpDlg') and pg.evaluate("document.querySelectorAll('#mpDlg .mp-t').length") == 5, 'My prompts window lists them')
    pg.evaluate("mpDel(0)"); pg.wait_for_timeout(100)
    ok(len(pg.evaluate("JSON.parse(localStorage.getItem('appu_myprompts'))")) == 4, 'delete works')
    pg.evaluate("document.getElementById('mpDlg').close()")
    # chat export
    pg.evaluate("""()=>{const l=document.getElementById('chatLog');l.innerHTML='<div class="msg user">What is a p-value?</div>';
      const a=document.createElement('div');a.className='msg ai';a.dataset.reply='The chance of data this extreme if nothing is going on.';l.appendChild(a)}""")
    with pg.expect_download() as dl:
        pg.evaluate("chatSaveMd()")
    path = dl.value.path(); md = open(path, encoding='utf-8').read()
    ok('## What is a p-value?' in md and 'nothing is going on' in md and 'Check them against a real source' in md, 'chat saves as Markdown with a caution line')

    # Help: accessibility
    pg.evaluate("openHelp()"); pg.wait_for_timeout(200)
    ok(pg.is_visible('#a11yBox'), 'Help has the accessibility section')
    pg.click('#a11yBox summary'); pg.wait_for_timeout(100)
    t = pg.inner_text('#a11yBox')
    ok('NVDA' in t and 'TalkBack' in t and 'VoiceOver' in t and 'not yet been tested' in t, 'it names free readers and the honest status')
    pg.evaluate("document.getElementById('helpDlg').close()")
    b.close()

    # Shared link (share target)
    errs2 = []
    b, pg = harness.new_page(p, errs2, {'width': 412, 'height': 880})
    pg.add_init_script("window.__looked=0;")
    pg.goto(harness.BASE + '?sh_title=Exam%20stress&sh_text=see%20https%3A%2F%2Fdoi.org%2F10.1037%2Fabc0000123&sh_url=')
    pg.wait_for_timeout(1200)
    pg.evaluate("citLookup=function(){window.__looked++}")
    pg.wait_for_timeout(500)
    ok(pg.evaluate("location.search") == '', 'share parameters are removed from the address')
    ok(pg.input_value('#citDOI') == '10.1037/abc0000123', 'DOI from shared text lands in the DOI box')
    ok(pg.evaluate("document.querySelector('.tool-panel.active').dataset.panel") == 'cite', 'Citation Manager is open')
    man = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'manifest.webmanifest')))
    ok(man.get('share_target', {}).get('params', {}).get('url') == 'sh_url', 'manifest offers the app in the Share menu')
    b.close()
    bad = [e for e in errs + errs2 if e[0] == 'pageerror']
    ok(not bad, 'no page errors %s' % bad[:3])
sys.exit(1 if fails else 0)
