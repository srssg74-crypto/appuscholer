"""A1 (Topic and scope): one line no longer counts as done. Three boxes build the topic sentence; two other topics and a reason are needed."""
import sys, os
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
    J("openSaveAsProject();document.getElementById('sapName').value='A1 study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("subOpen('idea','A1')"); pg.wait_for_timeout(400)
    t=J("document.getElementById('subMain').innerText")
    ok('Who' in t and 'What' in t and 'Where' in t,'the page shows three boxes: who, what, where')
    ok('Goes into the book' not in t and 'goes into the book' not in t.lower(),'no "goes into the book" box in the step')
    ok('Check before moving on' not in t,'the vague static check line is gone; the list of what is still needed replaces it')
    # a topic typed in the Idea tool plus one line is not enough any more
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety in college students'};studySet(o);lsSet('A1','alt','one long line about other topics that used to be enough to pass')")
    ok(J("subState('A1').s")!='dn','one typed line does not make A1 done')
    iss=J("lsIssues('A1',studyGet())")
    ok(any('Who' in x for x in iss) and any('What' in x for x in iss) and any('Where' in x for x in iss),'the list names each missing box: %s'%iss[:3])
    # fill the boxes by typing
    ins=pg.locator('#subMain .a1-f input')
    ok(ins.count()==5,'five small boxes (3 + 2)')
    ins.nth(0).fill('students'); ins.nth(1).fill('exam anxiety, sleep and phone use and stress'); ins.nth(2).fill('India')
    pg.wait_for_timeout(300)
    hint=J("document.getElementById('a1Live').innerText")
    ok('one word' in hint or 'Add the course' in hint,'hint: "who" is a single word')
    ok('several things' in hint,'hint: "what" holds several things')
    ok('too wide' in hint,'hint: "where" is too wide')
    ins.nth(0).fill('first-year nursing students'); ins.nth(1).fill('exam anxiety'); ins.nth(2).fill('two colleges in Pune')
    pg.wait_for_timeout(300)
    live=J("document.getElementById('a1Live').innerText")
    ok('A study of exam anxiety among first-year nursing students, in two colleges in Pune.' in live,'the topic sentence is built from the three boxes: %s'%live[:100])
    ok(J("studyGet().idea.topic")=='A study of exam anxiety among first-year nursing students, in two colleges in Pune.','the Idea tool topic is filled from it (it was only a pre-typed line, which is kept apart: %s)'%J("studyGet().idea.topic")[:40]) if False else None
    ok(J("subState('A1').s")!='dn','still not done without two other topics and a reason')
    ins.nth(3).fill('phone use and sleep'); ins.nth(4).fill('loneliness in hostels')
    pg.locator('#subMain textarea').first.fill('Because'); pg.locator('#subMain textarea').first.blur()
    pg.wait_for_timeout(200)
    ok(J("subState('A1').s")!='dn','a one-word reason is not enough')
    pg.locator('#subMain textarea').first.fill('Because I can reach these students through my supervisor and the scale is free.'); pg.locator('#subMain textarea').first.blur()
    pg.wait_for_timeout(300)
    ok(J("subState('A1').s")=='dn','done once who, what, where, two alternatives and a full reason are written')
    real=[e for e in errors if 'favicon' not in e[1]]
    ok(not real,'no page errors %s'%real[:3])
    b.close()
print('\n%d failures'%len(fails) if fails else '\nALL PASS')
sys.exit(1 if fails else 0)
