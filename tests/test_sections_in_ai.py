"""The AI reads a paper by its sections: abstract, intro, methods, results, discussion; references and back matter are left out."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
F=lambda w,n=60:(w+' ')*n
pages=[ "Sleep Study\nAbstract\n"+F('ABSWORD')+"\n1. Introduction\n"+F('INTROWORD'),
        "2. Methods\n"+F('METHWORD',80),
        "3. Results\n"+F('RESWORD',80),
        "4. Discussion\n"+F('DISCWORD',50)+"\nReferences\n"+F('REFWORD',80),
        F('APPXWORD',60) ]
S=[{'kind':'abstract','title':'Abstract','page':1,'subs':[]},{'kind':'introduction','title':'1. Introduction','page':1,'subs':[]},
   {'kind':'methods','title':'2. Methods','page':2,'subs':[]},{'kind':'results','title':'3. Results','page':3,'subs':[]},
   {'kind':'discussion','title':'4. Discussion','page':4,'subs':[]},{'kind':'references','title':'References','page':4,'subs':[]},
   {'kind':'backmatter','title':'Appendix','page':5,'subs':[]}]
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    r=J("shPaperText({pages:%s,sections:%s},4000)"%(json.dumps(pages),json.dumps(S)))
    t=r['text']
    ok(r['how']=='sections','built from sections')
    ok('REFWORD' not in t and 'APPXWORD' not in t,'reference list and back matter are left out')
    ok(all(k in t for k in ['ABSWORD','INTROWORD','METHWORD','RESWORD','DISCWORD']),'every body section is present')
    ok(len(t)<=4000+8,'the limit is kept (%d)'%len(t))
    ok(t.index('METHWORD')<t.index('RESWORD')<t.index('DISCWORD'),'sections keep their order')
    ok(t.count('INTROWORD')>0 and t.count('METHWORD')>10,'a long section gets a share of the budget')
    ok(J("shPaperText({pages:%s,sections:[]},4000).how"%json.dumps(pages))=='plain','no sections: falls back (plain)')
    ok(J("shPaperText({pages:['short'],sections:%s},4000).how"%json.dumps(S))=='plain','too little text: falls back')
    # the AI source for a shelf paper uses it
    J("(async()=>{await shPut({id:'ai1',title:'AI paper',file:'a.pdf',size:9,added:'2026-11-15',pages:%s,total:5,notes:[],cells:{},sections:%s});})()"%(json.dumps(pages),json.dumps(S))); pg.wait_for_timeout(400)
    src=J("(async()=>{const r=await b3AiSource({shelf:'ai1'});return r})()")
    ok(src['kind']=='full' and 'REFWORD' not in src['txt'] and 'RESWORD' in src['txt'],'the library AI reading gets body text without references')
    old=J("(async()=>{await shPut({id:'ai2',title:'Old',file:'o.pdf',size:9,added:'2026-11-15',pages:%s,total:5,notes:[],cells:{}});return (await b3AiSource({shelf:'ai2'})).txt.indexOf('REFWORD')>=0})()"%json.dumps(pages))
    ok(old is True,'a paper without sections keeps the old behaviour')
    ok(not [e for e in errors if e[0]=='pageerror'],'no page errors %s'%errors[:3])
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
