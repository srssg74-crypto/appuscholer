"""PDF to Word (build 2026.11.08u): paragraphs, real tables, headings, no false tables, docx file made."""
import sys, os, json, zipfile, io, base64
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
def it(s,x,y,w=None,h=10): return {"str":s,"transform":[h,0,0,h,x,y],"width":w if w is not None else 5*len(s),"height":h}
# a table: header + 3 numeric rows, 4 columns, page 612 wide
T=[]
for r,(y,row) in enumerate([(600,['Predictor','B','SE','p']),(585,['Age','0.12','0.03','.001']),(570,['Gender','-0.40','0.11','.020']),(555,['Income','0.05','0.02','.012'])]):
    for c,x in enumerate([60,250,350,450]): T.append(it(row[c],x,y))
# running text above and below
TXT_A=[it('Stress was higher on night shifts than on day shifts in this sample of nurses.',60,700,380),it('Sleep loss predicted burnout after the first year of work.',60,688,280)]
TXT_B=[it('The results are shown above and discussed in the next section.',60,500,300)]
# one spaced-out author line must not become a table
AUTH=[it('Rong Zhang',60,720),it('Ting Xu',260,720),it('Li Wei',460,720)]
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1200)
    bl=pg.evaluate("([i,v])=>shPageBlocks(i,v)",[TXT_A+T+TXT_B,[0,0,612,792]])
    kinds=[x['t'] for x in bl]
    ok(kinds.count('tbl')==1,'one table found %s'%kinds)
    tb=[x for x in bl if x['t']=='tbl'][0]['rows']
    ok(len(tb)==4 and tb[0]==['Predictor','B','SE','p'] and tb[2][1]=='-0.40','rows and cells right %s'%tb)
    ok(kinds.index('tbl')>0 and kinds[-1]=='p','table sits between the text above and below %s'%kinds)
    bl2=pg.evaluate("([i,v])=>shPageBlocks(i,v)",[AUTH+TXT_A,[0,0,612,792]])
    ok(not any(x['t']=='tbl' for x in bl2),'one spaced-out line is not a table')
    # sentence caught on top of a table goes back to the text
    PRE=[it('Given the sensitive nature of the topic, we asked all of them twice.',60,640)]
    T2=[]
    for r,(y,row) in enumerate([(626,['Predictor','B','SE','p']),(612,['Age','0.12','0.03','.001']),(598,['Gender','-0.40','0.11','.020']),(584,['Income','0.05','0.02','.012'])]):
        for c,x in enumerate([60,250,350,450]): T2.append(it(row[c],x,y))
    bl3=pg.evaluate("([i,v])=>shPageBlocks(i,v)",[T2+[it('Given the sensitive nature of the topic under study',60,640),it('B',300,640),it('-',380,640),it('-',460,640)],[0,0,612,792]])
    t3=[x for x in bl3 if x['t']=='tbl']
    ok(len(t3)==1 and t3[0]['rows'][0][0]=='Predictor' and any(x['t']=='p' and 'sensitive nature' in x['s'] for x in bl3),'a sentence on top of the table moves to the text %s'%bl3)
    # word-only table (no numbers) with aligned columns
    W=[]
    for r,(y,row) in enumerate([(600,['Layer','Baseline','Notes']),(585,['Charts','Plotly','Tie to data']),(570,['Stats','Python','Log the seed']),(555,['Export','Docx','Keep the original']),(540,['Store','Browser','Local only'])]):
        for c,x in enumerate([60,220,380]): W.append(it(row[c],x,y,w=40))
    bl4=pg.evaluate("([i,v])=>shPageBlocks(i,v)",[W,[0,0,612,792]])
    ok(any(x['t']=='tbl' and len(x['rows'])==5 for x in bl4),'a table of words only is found')
    # four spaced-out words lines that do not line up are not a table
    Z=[it('alpha beta',60,600),it('gamma',300,600),it('delta',500,600),it('one',60,585),it('two',200,585),it('three',420,585),it('x',100,570),it('y',350,570),it('z',480,570),it('p',60,555),it('q',260,555),it('r',470,555)]
    ok(not any(x['t']=='tbl' for x in pg.evaluate("([i,v])=>shPageBlocks(i,v)",[Z,[0,0,612,792]])),'scattered words are not a table')
    # paragraphs and headings
    ps=pg.evaluate("shParas(%s)"%json.dumps("Method\nParticipants were 96 nurses recruited from two hos-\npitals in Jaipur. They answered a short form.\nStress was higher on nights. The effect was small.\nResults\nSleep predicted burnout."))
    ok([x['t'] for x in ps][:2]==['h','p'] and 'hospitals' in ps[1]['s'],'heading, paragraph, hyphen mended %s'%ps)
    ok(any(x['t']=='h' and x['s']=='Results' for x in ps),'second heading found')
    h=pg.evaluate("shBlocksHTML([{t:'p',s:'a<b'},{t:'tbl',rows:[['x','y'],['1','2']]}])")
    ok('a&lt;b' in h and '<table>' in h and '<th>x</th>' in h,'html escapes and builds a table')
    # whole file, from stored text only (no PDF kept)
    PAGES=['Method\nParticipants were 96 nurses recruited from two hospitals.','Results\nStress was higher on night shifts.']
    J("window.confirm=()=>true")
    J("openSaveAsProject();document.getElementById('sapName').value='W';saveAsProject();try{document.getElementById('stageIntroDlg').close()}catch(e){}")
    J("(async()=>{await shPut({id:'pW',title:'Nurse stress',file:'n.pdf',size:1,added:'2026-11-08',pages:%s,total:2,notes:[],cells:{}})})()"%json.dumps(PAGES)); pg.wait_for_timeout(300)
    J("shOpenAt('pW',1)"); pg.wait_for_timeout(600)
    J("window.__b=null;shareBlob=async function(b,n,t){window.__n=n;window.__b=await new Promise(r=>{const f=new FileReader();f.onload=()=>r(f.result);f.readAsDataURL(b)});return true};0")
    J("shWord()"); pg.wait_for_timeout(600)
    ok(J("window.__b")is None and 'no PDF kept' in J("document.getElementById('toast')?document.getElementById('toast').innerText:document.body.innerText"),'first tap on a paper without a PDF asks to attach it, builds nothing')
    J("shWord()"); pg.wait_for_timeout(2500)
    d=J("window.__b")
    ok(bool(d) and J("window.__n")=='Nurse stress.docx','a .docx was made')
    if d:
        z=zipfile.ZipFile(io.BytesIO(base64.b64decode(d.split(',')[1]))); x=z.read('word/document.xml').decode()
        ok('96 nurses' in x and '[Page 2]' in x and 'Converted from the PDF' in x,'text and page marks are in the file')
    # a real table through the same builder
    J("window.__b=null");
    J("(async()=>{const h=document.createElement('div');h.innerHTML=shBlocksHTML([{t:'tbl',rows:[['a','b'],['1','2']]}]);window.__t=await new Promise(r=>{dxBuild(h,'t').then(b=>{const f=new FileReader();f.onload=()=>r(f.result);f.readAsDataURL(b)})})})()"); pg.wait_for_timeout(800)
    z=zipfile.ZipFile(io.BytesIO(base64.b64decode(J("window.__t").split(',')[1]))); ok('<w:tbl>' in z.read('word/document.xml').decode(),'the Word file holds a real table')
    ok(not errors,'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
