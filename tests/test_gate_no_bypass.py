"""No-bypass test for the instruction gate (AppuGate). Reads index.html as text and fails if a door
for outside text skips the gate. Exemptions are explicit markers, each with a reason:
  /*gate:data ...*/   the app's own files (backups, keys, exported JSON)
  /*gate:viewer ...*/ a PDF read used only to draw highlights or a selection layer
  /*gate:tts ...*/    speech made from the app's own lecture script (only inside apTtsMake)
  /*gate:net ...*/    a network read that is not outside prose (error text, a script, a zip part) or is gated later
  /*gate:doi ...*/    a paste from which only a DOI or PMID is taken
  /*gate:key ...*/    a clipboard read that takes only an API key
A comment that merely mentions AppuGate does not count; the gate must be called."""
import os, re, sys
src=open(os.path.join(os.path.dirname(__file__),'..','index.html'),encoding='utf-8').read()
L=src.split('\n'); fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
CALL=r'AppuGate\.(inbound|paste|pdfPage|pdfVisible|hidden|docx|html|outbound|reply)\('
def mark(kind): return r'/\*gate:'+kind+r' [^*]{3,}\*/'
def code(l): return re.sub(r'/\*(?!gate:)[\s\S]*?\*/','',l)   # drop ordinary comments, keep gate markers
CL=[code(l) for l in L]
ok('const AppuGate=(function(){' in src,'AppuGate module present')
# 1 every PDF text read is gated or marked viewer-only (any arguments, marker within the same statement)
bad=[i+1 for i,l in enumerate(CL) if re.search(r'\.getTextContent\(',l) and not re.search(CALL+r'|ijPdfHidden\(|'+mark('viewer'),'\n'.join(CL[i:i+2]))]
ok(not bad,'every PDF text read goes through the gate or is marked viewer-only '+str(bad))
# 2 every Word read checks hidden text first
bad=[i+1 for i,l in enumerate(CL) if re.search(r'mammoth\.(convertToHtml|extractRawText|convertToMarkdown)\(',l) and not re.search(r'ijDocxHidden\(|AppuGate\.docx\(','\n'.join(CL[max(0,i-3):i+1]))]
ok(not bad,'every Word read checks hidden text '+str(bad))
# 3 every .text() / readAsText is gated, or marked
GATED=CALL+r'|ijCleanImportHTML\(|'+mark('data')+'|'+mark('net')
def text_read_ok(i):
    l=CL[i]
    if re.search(GATED,l): return True
    if 'readAsText(' in l:
        for j in range(i,max(-1,i-12),-1):
            if 'onload' in CL[j]: return re.search(GATED,CL[j]) is not None
    return False
bad=[i+1 for i,l in enumerate(CL) if re.search(r'readAsText\(|\.text\(\)',l) and not text_read_ok(i)]
ok(not bad,'every text read is gated or marked '+str(bad))
# 4 search abstracts and Crossref
bad=[i+1 for i,l in enumerate(CL) if re.search(r'rsReconstructAbstract\(\w',l) and 'function rsReconstructAbstract' not in l and 'AppuGate.inbound(rsReconstructAbstract' not in l]
ok(not bad,'OpenAlex abstracts pass the gate '+str(bad))
m=re.search(r'async function rsPubmedAbstracts[\s\S]{0,1500}?\n}',src)
ok(m and 'AppuGate.inbound(' in m.group(0),'PubMed abstracts pass the gate')
ok(re.search(r'function citCrPlain\(x\)\{[^\n]*AppuGate\.inbound\(',src) is not None,'Crossref text passes the gate')
# 5 capture, share link, paste, AI in and out
m=re.search(r'function citCheckCaptureHash\(\)\{[\s\S]{0,2500}?\n}',src)
ok(m and 'AppuGate.inbound(' in m.group(0),'citation capture passes the gate')
ok("title=AppuGate.inbound((q.get('sh_title')" in src and "text=AppuGate.inbound((q.get('sh_text')" in src,'shared links pass the gate')
bad=[i+1 for i,l in enumerate(CL) if re.search(r"addEventListener\(\s*'paste'|onpaste=",l) and 'onpaste="return false"' not in l and not re.search(r'AppuGate\.paste\(|'+mark('doi'),'\n'.join(CL[i:i+2]))]
ok(not bad,'every paste listener is checked or marked '+str(bad))
ok(re.search(r'async function callAI\(prompt,opts\)\{\s*prompt=ijGuardPrompt\(prompt\)',src) is not None,'every AI call quotes suspicious material')
ok(re.search(r'const r=ijCheckReply\(ijTakeWatch\(await callAIRaw\(',src) is not None,'every AI reply is checked')
# 6 AI providers are reached only from callAIRaw (and speech from apTtsMake), by fetch, XHR or beacon
hosts=['generativelanguage.googleapis.com','api.anthropic.com','api.openai.com','api.groq.com','openrouter.ai/api','api.deepseek.com']
def body(name):
    m=re.search(r'async function '+name+r'\([\s\S]*?\n}\n',src); return m.group(0) if m else ''
rest=src
for nm in ['callAIRaw','apTtsMake']: rest=rest.replace(body(nm),'')
# the content security policy names the providers it allows; that is a permission, not a call
rest=re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>','',rest)
found=[h for h in hosts if h in rest and re.search(re.escape(h),'\n'.join(l for l in rest.split('\n') if re.search(r'fetch\(|XMLHttpRequest|sendBeacon|url\s*=|https://',l)))]
ok(not found,'AI provider addresses appear only inside callAIRaw and the speech maker '+str(found))
ok(all(src.count(m)==len(re.findall(re.escape(m)+r' [^*]{3,}\*/',src)) for m in ['/*gate:data','/*gate:viewer','/*gate:tts','/*gate:net','/*gate:doi','/*gate:key']),'every exemption marker gives a reason')
unknown=set(re.findall(r'/\*gate:(\w+)',src))-{'data','viewer','tts','net','doi','key'}
ok(not unknown,'no unknown exemption kinds '+str(unknown))
net_bad=[i+1 for i,l in enumerate(L) if '/*gate:net' in l and not re.search(r'fetch\(|\br\.text\(\)|r\.clone\(\)\.text\(\)|DecompressionStream',l)]
ok(not net_bad,'network exemptions sit only on network or zip reads '+str(net_bad))
drop_bad=[i+1 for i,l in enumerate(CL) if re.search(r"addEventListener\(\s*'drop'|\.ondrop\s*=",l) and not re.search(r'docImportFiles\(|'+CALL,'\n'.join(CL[i:i+5]))]
ok(not drop_bad,'every drop handler imports through the gated importer '+str(drop_bad))
clip_bad=[i+1 for i,l in enumerate(CL) if re.search(r'clipboard\.read(Text)?\(',l) and not re.search(CALL+'|'+mark('key'),l)]
ok(not clip_bad,'every clipboard read is gated or marked '+str(clip_bad))
other_bad=[i+1 for i,l in enumerate(CL) if re.search(r"\.onpaste\s*=|addEventListener\(\s*'beforeinput'",l) and not re.search(CALL,'\n'.join(CL[i:i+3]))]
ok(not other_bad,'no other paste routes skip the gate '+str(other_bad))
tts_out=[i+1 for i,l in enumerate(L) if '/*gate:tts' in l and l not in body('apTtsMake')]
ok(not tts_out,'speech exemptions sit only inside apTtsMake '+str(tts_out))
print('FAILED',len(fails)); sys.exit(1 if fails else 0)
