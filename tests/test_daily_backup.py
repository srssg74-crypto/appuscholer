"""Daily backup (build 2026.11.02m): kiosk answers and shelf records travel in the backup file, a chosen folder
gets a locked file every day (fake folder handle here, since a headless browser has no folder picker), only the
newest 14 day-files stay, and the reminder comes after one day without a backup."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
FAKE_DIR = r"""
(()=>{const files={};window._fakeFiles=files;
 for(let i=1;i<=20;i++){files['appuscholar-auto-2026-09-'+String(i).padStart(2,'0')+'.json']='old';}
 files['my-notes.txt']='keep';
 const dir={kind:'directory',name:'Drive backup',
  queryPermission:async()=>'granted',requestPermission:async()=>'granted',
  getFileHandle:async(n,o)=>({kind:'file',name:n,createWritable:async()=>{let buf='';return{write:async d=>{buf+=d},close:async()=>{files[n]=buf}}}}),
  removeEntry:async n=>{delete files[n]},
  entries:async function*(){for(const n of Object.keys(files))yield [n,{kind:'file',name:n}]}};
 window.showDirectoryPicker=async()=>dir;})()
"""
with sync_playwright() as p:
    errors=[]
    b,pg=new_page(p,errors)
    J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Backup study';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("editor.innerHTML='<p>'+'Sleep and exam anxiety in hostel students. '.repeat(30)+'</p>';docSaveBody(getEditorHTML())")
    J("(async()=>{await sfPut({id:'k1',sid:'S1',pkg:'LOCKEDPKG',ts:1,src:'kiosk'});await shPut({id:'p1',title:'Gupta 2020',file:'g.pdf',size:9,added:'2026-11-01',pages:['page one text'],total:1,notes:[],cells:{}})})()")
    pg.wait_for_timeout(300)
    # 1. plain backup file carries the IndexedDB records
    with pg.expect_download() as d:
        J("backupExport()")
    path=d.value.path(); bundle=json.load(open(path))
    ok(len(bundle.get('idb',{}).get('forms',[]))==1 and bundle['idb']['forms'][0]['pkg']=='LOCKEDPKG','backup file holds the kiosk answer, still locked')
    ok(len(bundle['idb'].get('shelf',[]))==1,'backup file holds the shelf record')
    ok(not any(k.startswith('appu_key_') for k in bundle['data']),'no AI key in the file')
    # 2. restore puts them back
    J("(async()=>{await sfClear('S1');await shDel('p1')})()"); pg.wait_for_timeout(200)
    ok(J("(async()=>(await sfAll('S1')).length)()")==0,'(records removed before restore)')
    pg.set_input_files('#backupFile', path)
    pg.wait_for_timeout(3500)
    J("window.confirm=()=>true")
    ok(J("(async()=>(await sfAll('S1')).length)()")==1,'restore brings the kiosk answer back')
    ok(J("(async()=>(await shAll()).some(x=>x.id==='p1'))()"),'restore brings the shelf record back')
    # 3. folder backup
    J(FAKE_DIR)
    J("bkxSetup();0"); pg.wait_for_timeout(500)
    J("document.getElementById('bkPass1').value='correct horse 12';document.getElementById('bkPass2').value='correct horse 12';bkPassOk()")
    pg.wait_for_timeout(4000)
    files=J("Object.keys(window._fakeFiles)")
    today=J("backupStamp(Date.now())")
    name='appuscholar-auto-%s.json'%today
    ok(name in files,'today\'s file is written into the chosen folder')
    autos=[f for f in files if f.startswith('appuscholar-auto-')]
    ok(len(autos)==14,'only the newest 14 day-files are kept (%d)'%len(autos))
    ok('my-notes.txt' in files,'other files in the folder are never touched')
    raw=J("window._fakeFiles['%s']"%name); fj=json.loads(raw)
    ok(fj.get('locked') and 'Sleep and exam' not in raw,'the folder file is locked')
    inner=J("(async()=>bkDecrypt(JSON.parse(window._fakeFiles['%s']),'correct horse 12'))()"%name)
    ok('Sleep and exam' in inner and 'LOCKEDPKG' in inner,'the password opens it, with documents and kiosk answers inside')
    ok(J("(async()=>{try{await bkDecrypt(JSON.parse(window._fakeFiles['%s']),'wrong pass 123');return false}catch(e){return true}})()"%name),'a wrong password does not open it')
    # unchanged: no rewrite; changed: same-day file updated
    J("window._fakeFiles['%s']='MARK'"%name)
    J("bkxWrite(false,false)"); pg.wait_for_timeout(1500)
    ok(J("window._fakeFiles['%s']"%name)=='MARK','nothing is rewritten when the work did not change')
    J("editor.innerHTML+='<p>NEW LINE after lunch</p>';docSaveBody(getEditorHTML())"); pg.wait_for_timeout(300)
    J("bkxWrite(false,false)"); pg.wait_for_timeout(3000)
    inner2=J("(async()=>bkDecrypt(JSON.parse(window._fakeFiles['%s']),'correct horse 12'))()"%name)
    ok('NEW LINE after lunch' in inner2,'a change during the day updates today\'s file')
    # the restore path reads the auto file with the password
    ok(J("JSON.parse(window._fakeFiles['%s']).auto===true"%name),'(auto file marked)')
    # 4. settings shows the status
    J("openSettings();backupStatusRender()"); pg.wait_for_timeout(300)
    st=J("document.getElementById('bkxStatus').innerText")
    ok('Drive backup' in st and 'Daily backup on' in st,'settings shows the folder and the last file: %s'%st[:90])
    # 5. no folder API: daily reminder after one day
    J("bkxOff()"); pg.wait_for_timeout(300)
    J("LS.set('appu_last_backup',String(Date.now()-2*86400000));LS.set('appu_backup_snooze','0');backupNudgeCheck()")
    ok(J("document.getElementById('backupNudge').style.display")=='block','the reminder shows after a day without a backup')
    J("backupSnooze();backupNudgeCheck()")
    ok(J("document.getElementById('backupNudge').style.display")=='none','"Later" hides it until tomorrow')
    real=[e for e in errors if 'favicon' not in e[1]]
    ok(not real,'no page errors %s'%real[:3])
    b.close()
print('\n%d failures'%len(fails) if fails else '\nALL PASS')
sys.exit(1 if fails else 0)
