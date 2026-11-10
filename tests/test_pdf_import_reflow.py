"""Writing-tool PDF import uses the Reader's reading order and rejoins paragraph lines (build 2026.11.10j).
pdf.js cannot load in the sandbox, so the extractor is replaced by made-up pages."""
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
    h=J("""pdfReflowHTML(['A Made-up Title About Anxiety\\nJ. Author and K. Writer\\nAbstract\\nAnxiety is an experience of everyday life. It typically functions as an alarm\\nthat warns of danger and, in mild degrees, is serviceable to the person.\\nIn disorders, however, the alarms may be intense.\\n','Second page line one of a paragraph that runs on for a good while and\\ncontinues here without a full stop yet and then ends here.\\n'])""")
    ok(h.startswith('<h1>A Made-up Title About Anxiety</h1>'),'title becomes a heading')
    ps=[x for x in h.replace('</h1>','<p>').split('<p>') if x and not x.startswith('<h1>')]
    ok(any('alarm that warns of danger' in x for x in ps),'wrapped lines rejoin with a space')
    ok(not any('<br>' in x for x in ps),'no stray line breaks')
    ok(any(x.startswith('Abstract') for x in ps),'short heading line stays separate')
    ok(any('continues here without a full stop' in x and 'Second page line one' in x for x in ps),'a paragraph runs on across lines')
    ok(J("pdfReflowHTML([])")=='<p></p>','empty input is safe')
    b2=J("pdfReflowHTML(['Likewise patients with anxiety often experi-\\nSleep disturbances are very common in these disorders and are discussed here at length.\\n'])")
    ok(b2.count('<p>')==2 and '<h1>' not in b2,'a hyphen-cut line is not merged with a capital-letter block')
    ok(J("pdfReflowHTML(['12 Journal of Made-up Things\\nBody text of the paragraph that is long enough to be a line of its own here and here.\\n'])").startswith('<p>'),'a running-head-like first line is not made a heading')
    d1=J("pdfReflowHTML(['A Made-up Title About Worry\\nBody paragraph one is long enough to stand as a line of its own in the text.\\nKeywords: worry; sleep\\nCopyright 2003 Example Press. All rights reserved\\nWe often experi-\\n','ence worry in daily life and this sentence goes on for a good while longer.\\nBody paragraph three is also long enough to stand as a line of its own here.\\nexperience is a word used twice in this made-up paper, experience.\\n'])")
    ok('<h2>Paper details</h2>' in d1 and d1.index('Keywords')>d1.index('<h2>Paper details</h2>') and d1.index('Copyright')>d1.index('<h2>Paper details</h2>'),'front matter and footer move to a Paper details block')
    ok('We often experience worry in daily life' in d1,'a word cut at the end of a page is joined to the next page')
    ok('Body paragraph one' in d1[:d1.index('<h2>')],'the body stays above the details block')
    J("window.__f=shExtractPdf;shExtractPdf=async()=>({pages:['Title Of The Paper Goes Here For Test\\nBody line one of the paragraph is long enough to be a full line here\\nand it ends now.\\n'],total:1})")
    J("window.confirm=()=>true")
    r=J("(async()=>{const f=new File([new Uint8Array([37,80,68,70])],'Paper.pdf',{type:'application/pdf'});await docImportOne(f,'');return getEditorHTML()})()")
    ok('Title Of The Paper' in r and 'and it ends now.' in r and 'is long enough to be a full line here and it ends now.' in r,'import puts the reflowed text in the editor')
    ok(not [e for e in errors if 'Failed to load resource' not in str(e)],'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
