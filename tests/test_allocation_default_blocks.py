"""Second review, finding 5: a three-arm permuted-block plan with the block-size field left blank
used to save and register with a silent [4,6,8] default, then fail at seed load with
"block size 4 is not a positive multiple of 3". Blank must now record the arm-count default
(6,9,12 for three arms) on the plan, and the list must build. The parser must also refuse any
token that is not a whole positive number, instead of dropping it and saving the rest."""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
REASON='Three teaching methods compared in one college, so chance keeps the three groups close on baseline score.'
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Default blocks study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Three-arm teaching trial'};o.design={type:'experimental',pop:'Students',sampling:'Convenience'};designSet('ec',{status:'approved',apprNo:'IEC/2026/14',apprDate:'2026-11-01'});studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alN').value='30';alRefresh()"%json.dumps(REASON))
    base="document.getElementById('alMethod').value='perm';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Rao';document.getElementById('alHolder').value='Coordinator';document.getElementById('alArms').value='A,B,C';document.getElementById('alBlind').value='both';"

    # the parser table from the review: each of these used to save something other than what was typed
    for typed,why in [('six','a word'),('4,x,8','a bad token among good ones'),('4.9,6','a decimal'),('6,,9','an empty token'),('-6,9','a negative')]:
        J(base+"document.getElementById('alBlocks').value=%s;alSave()"%json.dumps(typed))
        ok(not J("!!(studyGet().alloc&&studyGet().alloc.plan)"),'block sizes %r (%s) are refused, not partly saved'%(typed,why))
    msg=J("document.getElementById('alMsg').textContent")
    ok('whole positive multiple' in msg,'the refusal says what a valid block size is: '+msg)

    # the reviewer's repro: blank block sizes on a three-arm plan
    J(base+"document.getElementById('alBlocks').value='';alSave()")
    plan=J("studyGet().alloc.plan")
    ok(bool(plan) and plan.get('blockSizes')==[6,9,12],'blank block sizes on a 3-arm plan record the arm-count default [6,9,12] on the plan, not a silent [4,6,8]: '+json.dumps(plan.get('blockSizes') if plan else None))
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    seed_hex=J("AL_PENDING.seedHex")
    J("document.getElementById('alSeedSaved').checked=true;document.getElementById('alPubNote').value='Emailed the commitment hash to Dr. Gaur on registration day.';alRegister()"); pg.wait_for_timeout(300)
    ok(J("!!studyGet().alloc.commit"),'the plan registers')
    d=tempfile.mkdtemp(); seedf=os.path.join(d,'seed.txt'); open(seedf,'w').write('Seed (hex): %s\n'%seed_hex)
    J("document.getElementById('enRoleAck').checked=true")
    pg.set_input_files('#enSeed',seedf); pg.wait_for_timeout(800)
    ok(J("AL_SEED!==null && AL_BUILT_N===30"),'the seed loads and the 30-position list builds (this used to fail with "block size 4 is not a positive multiple of 3")')
    enmsg=J("document.getElementById('enMsg').textContent")
    ok('not a positive' not in enmsg and 'multiple of' not in enmsg,'no block-size error on seed load: '+enmsg)
    # the built list is the engine's three-arm list for the default blocks, balanced across arms
    lst=J("(async()=>await alBuildList(ALG.fromHex(%s),'perm',30,['A','B','C'],{sizes:studyGet().alloc.plan.blockSizes}))()"%json.dumps(seed_hex))
    ok(len(lst)==30 and lst.count('A')==lst.count('B')==lst.count('C')==10 and None not in lst,'the list is balanced 10/10/10 with no undefined positions')
    # a two-arm plan with blank blocks still gets [4,6,8], so existing two-arm studies are unchanged
    J("const o=studyGet();o.alloc=null;studySet(o);alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alN').value='30';alRefresh()"%json.dumps(REASON))
    J(base+"document.getElementById('alArms').value='A,B';document.getElementById('alBlocks').value='';alSave()")
    ok(J("studyGet().alloc.plan.blockSizes")==[4,6,8],'a two-arm plan with blank blocks still records [4,6,8]')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
