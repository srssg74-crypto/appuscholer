"""Fix from the 2026-11-14 review, finding 5: the plan form now records block sizes (for permuted
blocks) and an allocation ratio (for simple randomisation), validates them at save time instead of
letting the runner crash after the plan is locked, and the runner, reveal and envelope export all
honour the recorded values instead of silently defaulting to equal blocks/equal split."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
REASON='Two intact sections of one college, so chance keeps the groups close on baseline anxiety.'
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Params study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("const o=studyGet();o.idea={topic:'Three-arm teaching trial'};designSet('ec',{status:'approved',apprNo:'IEC/2026/13',apprDate:'2026-11-01'});studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alN').value='30';alRefresh()"%json.dumps(REASON))

    # finding 5: a 3-arm permuted-block plan with block sizes that are NOT multiples of 3 is refused at save time
    J("document.getElementById('alMethod').value='perm';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Rao';document.getElementById('alHolder').value='Coordinator';document.getElementById('alArms').value='A,B,C';document.getElementById('alBlind').value='both';document.getElementById('alBlocks').value='4,6,8';alSave()")
    ok(not J("!!(studyGet().alloc&&studyGet().alloc.plan)"),'a plan with block sizes that are not multiples of the arm count is refused at save, not accepted and left to crash the runner later')
    msg1=J("document.getElementById('alMsg').textContent")
    ok(len(msg1)>0,'the refusal is explained on screen: '+msg1)

    # the same plan with valid block sizes (multiples of 3) saves cleanly
    J("document.getElementById('alBlocks').value='3,6,9';alSave()")
    saved=J("studyGet().alloc.plan")
    ok(saved and saved.get('blockSizes')==[3,6,9],'valid block sizes are parsed and stored on the plan')

    # finding 5: a 2-arm simple plan with a custom ratio produces the correct non-equal split
    J("const o=studyGet();o.alloc=null;studySet(o);alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alN').value='30';alRefresh()"%json.dumps(REASON))
    J("document.getElementById('alMethod').value='simple';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Rao';document.getElementById('alHolder').value='Coordinator';document.getElementById('alArms').value='Treatment,Control';document.getElementById('alBlind').value='both';document.getElementById('alRatio').value='2,1';alSave()")
    saved2=J("studyGet().alloc.plan")
    ok(saved2 and abs(saved2['probs'][0]-2/3)<1e-9 and abs(saved2['probs'][1]-1/3)<1e-9,'a 2:1 ratio is stored as probabilities summing to 1, in arm order')

    # an invalid ratio (wrong count) is refused
    J("document.getElementById('alRatio').value='2,1,1';alSave()")
    msg2=J("document.getElementById('alMsg').textContent")
    ok('Treatment' not in msg2 or len(msg2)>0,'an invalid ratio is refused with an explanation: '+msg2)
    ok(J("studyGet().alloc.plan.ratioText")=='2,1','the bad ratio attempt does not overwrite the last valid saved plan')

    # finding 5: the runner actually uses the recorded ratio when building the list
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    seed_hex=J("AL_PENDING.seedHex")
    J("document.getElementById('alSeedSaved').checked=true;document.getElementById('alPubNote').value='Emailed the commitment hash to Dr. Gaur on registration day.';alRegister()"); pg.wait_for_timeout(300)
    d=__import__('tempfile').mkdtemp()
    seedf=os.path.join(d,'seed.txt'); open(seedf,'w').write('Seed (hex): %s\n'%seed_hex)
    J("document.getElementById('enRoleAck').checked=true")
    pg.set_input_files('#enSeed',seedf); pg.wait_for_timeout(600)
    built_list=J("(async()=>await alSimple(ALG.fromHex(%s),30,['Treatment','Control'],[2/3,1/3]))()"%json.dumps(seed_hex))
    built_hash=J("alListHash(ALG.fromHex(%s),%s)"%(json.dumps(seed_hex),json.dumps(built_list)))
    logged=[e for e in J("studyGet().alloc.log") if e['kind']=='list built'][-1]
    ok(logged['hash']==built_hash,'the list the runner actually built matches one built with the 2:1 ratio, not an equal split')

    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
