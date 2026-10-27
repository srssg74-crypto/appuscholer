"""Records inside the steps: search log, source matrix, recruitment and deviation logs, cleaning log, supervisor tracker."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
S='/tmp/claude-0/-home-claude/d540b351-a2df-5fa6-9a88-226a4c6e6a4f/scratchpad/'
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("openSaveAsProject();document.getElementById('sapName').value='Records study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("subOpen('lit','B6')"); pg.wait_for_timeout(200)
    ok('No search logged yet' in J("document.getElementById('subMain').innerText"),'B6 warns when no search is logged')
    J("SUB_CUR.id='B2';subRender()")
    ok(J("subState('B2').s")=='ns','B2 not done at start')
    J("logAdd('search')"); J("logCell('search',0,'db','PubMed');logCell('search',0,'q','sleep AND exam anxiety AND India');logCell('search',0,'hits','37')")
    ok(J("subState('B2').s")=='dn' and J("logRows(studyGet(),'search').length")==1,'one logged search completes B2')
    ok(J("document.querySelector('.sub-item.on').textContent").startswith('✅'),'list icon updates without a full redraw')
    J("SUB_CUR.id='B6';subRender()")
    ok('No search logged yet' not in J("document.getElementById('subMain').innerText"),'B6 warning gone after the search')
    # matrix from the library
    J("citSaveLib([{author:'Sharma, A.; Gupta, R.',year:'2021',title:'Sleep quality and exam anxiety in Indian undergraduates'},{author:'Rao, K.',year:'2019',title:'Sleep in college students'}])")
    J("SUB_CUR.id='B3';subRender();logFromLibrary('matrix')")
    ok(J("logRows(studyGet(),'matrix').length")==2,'two papers brought from the library')
    J("logFromLibrary('matrix')")
    ok(J("logRows(studyGet(),'matrix').length")==2,'no duplicates on a second import')
    ok('Sharma et al. (2021)' in J("logRows(studyGet(),'matrix')[0].paper"),'paper label: '+J("logRows(studyGet(),'matrix')[0].paper"))
    J("logCell('matrix',0,'finding','Poor sleep linked with higher anxiety, r = .32')")
    ok(J("logsDone('B3',studyGet())")==True,'matrix row with a finding counts')
    pg.screenshot(path=S+'records-b3.png')
    # recruitment and deviations
    J("subOpen('collect','D2');logAdd('recruit');logCell('recruit',0,'appr','120');logCell('recruit',0,'agreed','96');logCell('recruit',0,'done','90');logCell('recruit',0,'left','6')")
    J("logRefresh()")
    ok('120 approached, 96 agreed, 90 completed, 6 withdrew' in J("document.getElementById('subMain').innerText"),'recruitment totals shown')
    ok(J("subState('D2').s")=='dn','D2 done with completed participants')
    ok(J("document.querySelectorAll('#subMain .log-tbl').length")==2,'D2 has recruitment and deviation tables')
    # cleaning
    J("subOpen('collect','D3');logAdd('clean');logCell('clean',0,'step','Exclusion');logCell('clean',0,'why','Failed both attention checks');logCell('clean',0,'n','3')")
    ok(J("subState('D3').s")=='dn','D3 done with a reasoned cleaning step')
    # supervisor tracker
    J("subOpen('review','F3');logAdd('supervisor');logCell('supervisor',0,'c','Add the response rate to the abstract')")
    ok(J("subState('F3').s")!='dn','open supervisor comment keeps F3 open')
    J("logCell('supervisor',0,'st','Done')")
    ok(J("subState('F3').s")=='dn','all comments closed: F3 done')
    J("logDel('supervisor',0)")
    ok(J("logRows(studyGet(),'supervisor').length")==0,'row can be removed')
    # CSV
    with pg.expect_download() as dl:
        J("logCsv('recruit')")
    path=dl.value.path(); txt=open(path,encoding='utf-8-sig').read()
    ok(txt.startswith('"Date","Site or channel","Approached"') and '"120"' in txt,'recruitment CSV downloads')
    # per study: a new study starts empty
    J("document.getElementById('subDlg').close();openNewProjectDirect();document.getElementById('sapName').value='Other';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    pg.wait_for_timeout(300)
    ok(J("logRows(studyGet(),'search').length")==0,'logs belong to their own study')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
