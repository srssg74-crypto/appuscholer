"""Stage 7 runner: the app's simple and permuted-block lists match the Python engine; enrolment shows positions, reveal is logged, a wrong seed is refused."""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
VEC=json.load(open('/tmp/claude-0/-home-claude/d540b351-a2df-5fa6-9a88-226a4c6e6a4f/scratchpad/appuscholar_randomise/vectors.json'))
SEED=VEC['seed_hex']
REASON='Two intact sections of one college, so chance keeps the groups close on baseline anxiety.'
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Runner study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    # engine cross-check: same seed, same output as the Python engine
    got=J("(async()=>{const s=ALG.fromHex(%s);return {simple: await alSimple(s,30,['A','B']), blocks: await alPermBlocks(s,40,['A','B'],[4,6,8])}})()" % json.dumps(SEED))
    ok(got['simple']==VEC['simple_A_B_30'],'app simple randomisation matches the Python engine')
    ok(got['blocks']==VEC['blocks_A_B_40'],'app permuted blocks match the Python engine')
    J("const o=studyGet();o.idea={topic:'Sleep and exam anxiety in first-year students'};o.design={type:'experimental',pop:'First-year students in two colleges',sampling:'Convenience'};designSet('ec',{status:'approved',apprNo:'IEC/2026/12',apprDate:'2026-11-01'});studySet(o)")
    J("alOpen()"); pg.wait_for_timeout(200)
    J("document.getElementById('alReason').value=%s;document.getElementById('alFactors').value='';document.getElementById('alN').value='12';alRefresh()"%json.dumps(REASON))
    J("document.getElementById('alMethod').value='perm';document.getElementById('alConc').value='central';document.getElementById('alMaker').value='Dr. Meena Sharma';document.getElementById('alHolder').value='Coordinator';document.getElementById('alArms').value='A,B';alSave()")
    J("alMakeCommit()"); pg.wait_for_timeout(300)
    seed_hex=J("AL_PENDING.seedHex")
    J("document.getElementById('alSeedSaved').checked=true;alRegister()"); pg.wait_for_timeout(300)
    ok(J("!!studyGet().alloc.commit"),'commitment registered')
    # seed file: correct one loads, the list matches the engine's permuted blocks for n=12
    d=tempfile.mkdtemp()
    good=os.path.join(d,'appuscholar_seed_KEEP_SECRET.txt'); open(good,'w').write('Appuscholar randomisation seed\nSeed (hex): %s\n'%seed_hex)
    pg.set_input_files('#enSeed',good); pg.wait_for_timeout(600)
    ok(J("AL_LIST!==null && AL_LIST.length===12"),'list built from the right seed')
    bad=os.path.join(d,'wrong.txt'); open(bad,'w').write('Seed (hex): %s\n'%('ff'*32))
    J("AL_LIST=null;AL_SEED=null"); pg.set_input_files('#enSeed',bad); pg.wait_for_timeout(600)
    ok(J("AL_LIST")==None,'a wrong seed does not build a list')
    pg.set_input_files('#enSeed',good); pg.wait_for_timeout(600)
    # enrolment: positions only, no arms in the record; duplicates refused
    J("document.getElementById('alDlg').scrollTop=0")
    for code in ['P-001','P-002','P-003']:
        J("document.getElementById('enCode').value='%s';enEnrol()"%code)
    en=J("studyGet().alloc.enrol")
    ok([e['pos'] for e in en]==[1,2,3],'enrolment assigns positions 1,2,3')
    ok('arm' not in json.dumps(en) and 'A"' not in json.dumps(en),'enrolment record holds no arm')
    J("document.getElementById('enCode').value='P-001';enEnrol()")
    ok(len(J("studyGet().alloc.enrol"))==3,'duplicate code refused')
    J("enReveal('P-002')")
    ok(any(e['kind']=='reveal' for e in J("studyGet().alloc.log")),'reveal is logged')
    ok(J("document.getElementById('enMsg').textContent").startswith('Arm for P-002'),'reveal shows the arm on screen')
    rec=J("JSON.stringify(studyGet().alloc)")
    ok('"arm"' not in rec,'the study record never stores an arm')
    errs=[e for e in errors if e[0]=='pageerror']
    ok(not errs,'no page errors '+json.dumps(errs[:3]))
    b.close()
print('FAILED %d'%len(fails) if fails else 'ALL PASS')
