"""Version 142: the outline beside the page can fold chapters, rename, add, move and delete headings, with Undo,
and shows one soft colour per chapter on screen only (never in saved or printed text)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import harness
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

DOC = ("<h1>Introduction</h1><p>Intro text one two three.</p><h2>Background</h2><p>Back text four five.</p>"
       "<h1>Literature Review</h1><p>Review words here now.</p><h2>Theory</h2><p>Theory words.</p><h2>Gaps</h2><p>Gap words go here.</p>"
       "<h1>Method</h1><p>Method text.</p>")
HEADS = "[...editor.querySelectorAll('h1,h2,h3')].map(h=>h.textContent)"

with sync_playwright() as p:
    errs = []
    b, pg = harness.new_page(p, errs, {'width': 1366, 'height': 900})
    pg.goto(harness.BASE); pg.wait_for_timeout(1500)
    pg.evaluate("apGoTool('style')"); pg.wait_for_timeout(400)
    pg.evaluate("editor.innerHTML=%r;LS.set('appu_bb_out','1');try{bbOutlineToggle();bbOutlineToggle()}catch(e){};bbOutlineRender()" % DOC)
    pg.wait_for_timeout(400)
    if not pg.evaluate("!!document.getElementById('bbOutline')&&document.getElementById('bbOutline').style.display!=='none'"):
        pg.evaluate("try{bbOutlineToggle()}catch(e){};bbOutlineRender()"); pg.wait_for_timeout(300)
    ok(pg.evaluate("document.querySelectorAll('#bbOutline .bb-rw').length") == 6, 'every heading becomes an outline row')
    ok(pg.evaluate("document.querySelectorAll('#bbOutline .ol-more').length") == 6, 'every row has an options button')
    # chapter colours on screen
    ok(pg.evaluate("[...editor.querySelectorAll('h1')].map(h=>h.getAttribute('data-tint')).join(',')") == '0,1,2', 'each chapter gets its own colour')
    ok(pg.evaluate("editor.querySelectorAll('h2')[1].getAttribute('data-tint')") == '1', 'sub-headings take their chapter colour')
    ok('data-tint' not in pg.evaluate("getEditorHTML()"), 'colour marks never reach saved or exported text')
    pg.emulate_media(media='print')
    ok(pg.evaluate("getComputedStyle(editor.querySelector('h1')).backgroundColor") in ('rgba(0, 0, 0, 0)', 'transparent'), 'no colour when printed')
    pg.emulate_media(media='screen')
    # fold
    pg.evaluate("olFoldAll(true)"); pg.wait_for_timeout(200)
    ok(pg.evaluate("[...document.querySelectorAll('#bbOutline .bb-rw')].filter(w=>!w.hidden).length") == 3, 'Collapse all leaves only the chapters')
    pg.evaluate("olFoldAll(false)"); pg.wait_for_timeout(200)
    ok(pg.evaluate("[...document.querySelectorAll('#bbOutline .bb-rw')].filter(w=>!w.hidden).length") == 6, 'Expand all shows every heading')
    # move a chapter up, with its sub-headings and text
    pg.evaluate("olMove(2,-1)"); pg.wait_for_timeout(200)
    ok(pg.evaluate(HEADS) == ['Literature Review', 'Theory', 'Gaps', 'Introduction', 'Background', 'Method'], 'Move up carries the chapter with its sub-headings')
    ok('Gap words go here.' in pg.evaluate("editor.querySelectorAll('p')[2].textContent"), 'the text moves with its heading')
    pg.evaluate("olUndo()"); pg.wait_for_timeout(200)
    ok(pg.evaluate(HEADS)[0] == 'Introduction', 'Undo puts it back')
    # move a sub-heading down within its chapter only
    pg.evaluate("olMove(3,1)"); pg.wait_for_timeout(200)
    ok(pg.evaluate(HEADS) == ['Introduction', 'Background', 'Literature Review', 'Gaps', 'Theory', 'Method'], 'Move down swaps sub-headings inside a chapter')
    pg.evaluate("olUndo()"); pg.wait_for_timeout(200)
    # rename through the inline box
    pg.evaluate("olRename(1)"); pg.wait_for_timeout(100)
    pg.fill('#bbOutline .ol-ren', 'Background and context'); pg.keyboard.press('Enter'); pg.wait_for_timeout(200)
    ok(pg.evaluate("editor.querySelectorAll('h2')[0].textContent") == 'Background and context', 'Rename changes the heading in the document')
    # add a sub-heading
    pg.evaluate("olAdd(5,1)"); pg.wait_for_timeout(300); pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    ok(pg.evaluate(HEADS)[-1] in ('New heading', 'नया शीर्षक') and pg.evaluate("editor.querySelectorAll('h1,h2,h3')[6].tagName") == 'H2', 'Add sub-heading puts a level-2 heading inside the chapter')
    # delete: heading only keeps the words, whole section removes them
    pg.evaluate("olDel(4,'head')"); pg.wait_for_timeout(200)
    ok('Gap words go here.' in pg.evaluate("editor.textContent") and 'Gaps' not in pg.evaluate(HEADS), 'Delete heading only keeps its text')
    pg.evaluate("olUndo()"); pg.wait_for_timeout(200)
    pg.evaluate("olDel(4,'all')"); pg.wait_for_timeout(200)
    ok('Gap words go here.' not in pg.evaluate("editor.textContent"), 'Delete whole section removes its words')
    pg.evaluate("olMenu(0,document.querySelector('#bbOutline .ol-more'));olDelAsk(0)"); pg.wait_for_timeout(100)
    ok('words' in pg.inner_text('#olMenu'), 'the delete choice says how many words would go')
    # colours can be switched off
    pg.evaluate("LS.set('appu_ol_tint','0');bbOutlineRender()"); pg.wait_for_timeout(200)
    ok(pg.evaluate("editor.querySelectorAll('[data-tint]').length") == 0, 'Chapter colours can be switched off')
    ok(not [e for e in errs if e[0] == 'pageerror'], 'no page errors %s' % [e for e in errs if e[0] == 'pageerror'][:2])
    b.close()
sys.exit(1 if fails else 0)
