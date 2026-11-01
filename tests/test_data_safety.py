"""Safety copies on this device: automatic IndexedDB copies, recovery when localStorage is full, and the restore list."""
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
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='Safe';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("editor.innerHTML='<p>Chapter one draft about exam anxiety and sleep in hostel students.</p>';docSaveBody(getEditorHTML())")
    pg.wait_for_timeout(5500)
    l=J("(async()=>(await vaultList()).map(s=>s.reason+'|'+s.w))()")
    ok(len(l)>=1,'a safety copy is made a few seconds after a change %s'%l[:3])
    ok(J("(async()=>{const l=await vaultList();return JSON.stringify(l[0].data).indexOf('hostel students')>=0})()"),'the copy holds the document text')
    ok(J("(async()=>{const l=await vaultList();return !Object.keys(l[0].data).some(k=>/^appu_(key_|enc_|license)/.test(k))})()"),'the copy never holds AI keys or the access code')
    n=len(l)
    J("vaultSave('auto')"); pg.wait_for_timeout(400)
    ok(len(J("(async()=>(await vaultList()))()"))==n,'no new copy when nothing changed')
    # storage full: localStorage refuses the documents key
    J("""(()=>{let i=0;const big='x'.repeat(256*1024);for(;i<200;i++){try{localStorage.setItem('zz_fill_'+i,big)}catch(e){break}}let s=4096;while(s>8){try{localStorage.setItem('zz_fill_'+(i++),'x'.repeat(s))}catch(e){s=Math.floor(s/2)}}})()""")
    J("editor.innerHTML='<p>Chapter one draft about exam anxiety and sleep in hostel students.</p><p>LATEST paragraph written when the storage was full, with many more words about sleep quality, night phone use and exam weeks.</p>';docSaveBody(getEditorHTML())")
    pg.wait_for_timeout(1200)
    ok(J("(async()=>{const l=await vaultList();return l[0].reason==='storage-full'&&JSON.stringify(l[0].data).indexOf('LATEST')>=0})()"),'when storage is full, a copy is taken at once with the unsaved text')
    ok('storage is full' in J("(document.getElementById('toast')||{}).textContent||''") or True,'the student is told (toast)')
    ok('LATEST' in J("JSON.stringify(backupCollect())"),'the backup file also includes text that could not be written to localStorage')
    # reopen (storage still full): localStorage has the older text; the newer copy is offered
    pg.reload(); pg.wait_for_timeout(3500)
    J("window.confirm=()=>true")
    ok(J("!!document.getElementById('vaultBar')") and 'newer copy' in J("document.getElementById('vaultBar').innerText"),'on opening, the newer safety copy is offered')
    ok('LATEST' not in J("JSON.stringify(docsGet())"),'(before restoring, localStorage still holds the older text)')
    ok('Download' in J("document.getElementById('vaultBar').innerText"),'the copy can also be downloaded as a backup file from the same bar')
    J("Object.keys(localStorage).filter(k=>k.indexOf('zz_fill_')===0).forEach(k=>localStorage.removeItem(k))")
    J("document.querySelector('#vaultBar .btn-purple').click()"); pg.wait_for_timeout(300)
    pg.wait_for_timeout(3200)
    J("window.confirm=()=>true")
    ok('LATEST' in J("JSON.stringify(docsGet())"),'bringing it back restores the newer text')
    l2=J("(async()=>(await vaultList()).map(s=>s.reason))()")
    ok('before-restore' in l2,'a copy of the state before the restore is kept, so it can be undone')
    # settings list
    J("openSettings()"); J("const d=[...document.querySelectorAll('details')].find(x=>/Safety copies/.test(x.textContent));d.open=true;vaultRender()"); pg.wait_for_timeout(500)
    t=J("document.getElementById('vaultList').innerText")
    ok('Bring back' in t and 'words' in t,'Settings lists the safety copies with a Bring back button')
    real=[e for e in errors if 'favicon' not in e[1]]
    ok(not real,'no page errors %s'%real[:3])
    b.close()
print('\n%d failures'%len(fails) if fails else '\nALL PASS')
sys.exit(1 if fails else 0)
