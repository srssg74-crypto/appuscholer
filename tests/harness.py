"""Shared Playwright harness for Appuscholar.
Serves nothing itself: expects the repo on http://localhost:8765/.
CDN libraries are blocked in this sandbox, so they are replaced with small stubs."""
import json, sys
from playwright.sync_api import sync_playwright

import os
BASE = os.environ.get('APPU_URL','http://localhost:8765/index.html')

STUBS = {
 'mammoth': "window.mammoth={extractRawText:async()=>({value:'stub text'}),convertToHtml:async()=>({value:'<p>stub</p>'})};",
 'pdf.min': "window.pdfjsLib={GlobalWorkerOptions:{},getDocument:()=>({promise:Promise.resolve({numPages:1,getPage:async()=>({getTextContent:async()=>({items:[{str:'stub pdf text'}]}),getViewport:()=>({width:10,height:10}),render:()=>({promise:Promise.resolve()})})})})};",
 'pdf.worker': "",
 'chart': "window.Chart=function(ctx,cfg){this.cfg=cfg;this.destroy=function(){};this.update=function(){};this.toBase64Image=function(){return 'data:image/png;base64,'};};window.Chart.register=function(){};window.Chart.defaults={font:{},plugins:{legend:{},tooltip:{}},scale:{grid:{},ticks:{}},color:''};",
 'pptxgen': "window.PptxGenJS=function(){this.addSlide=()=>({addText(){},addImage(){},addShape(){},addTable(){},addChart(){},addNotes(){},background:null});this.writeFile=async()=>{};this.defineLayout=()=>{};this.defineSlideMaster=()=>{};this.ShapeType={rect:'rect',line:'line',roundRect:'roundRect',ellipse:'ellipse'};this.ChartType={bar:'bar',line:'line',pie:'pie'};};",
}

# Test-only: accept a dummy access code and skip first-use screens, so the probes reach the app.
GATE_BYPASS = r"""
(()=>{
  const v=crypto.subtle.verify.bind(crypto.subtle);
  crypto.subtle.verify=async(a,...r)=>(a&&a.name==='ECDSA')?true:v(a,...r);
  const p=btoa(JSON.stringify({exp:'2030-01-01',n:'Test',id:'t1'})).replace(/=+$/,'');
  try{
    if(!localStorage.getItem('appu_license'))localStorage.setItem('appu_license',JSON.stringify({payload:{exp:'2030-01-01',n:'Test',id:'t1'},raw:p+'.AAAA'}));
    if(!localStorage.getItem('appu_terms'))localStorage.setItem('appu_terms',JSON.stringify({v:999}));
    localStorage.setItem('appu_seen','1');
  }catch(e){}
})();
"""

def route_cdn(route):
    u = route.request.url
    for k, v in STUBS.items():
        if k in u:
            return route.fulfill(status=200, content_type='application/javascript', body=v)
    if 'fonts.g' in u:
        return route.fulfill(status=200, content_type='text/css', body='')
    # every other outside host: fail like an offline network
    return route.abort()

def new_page(p, errors, viewport=None):
    b = p.chromium.launch()
    ctx = b.new_context(viewport=viewport or {'width': 1366, 'height': 900}, service_workers='block')
    ctx.route(lambda url: not url.startswith('http://localhost'), route_cdn)
    ctx.add_init_script(GATE_BYPASS)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(('pageerror', str(e)[:400])))
    pg.on('console', lambda m: errors.append(('console.' + m.type, m.text[:400])) if m.type == 'error' else None)
    pg.on('dialog', lambda d: (errors.append(('dialog', d.message[:300])) if d.type=='alert' else None, d.dismiss()))
    return b, pg

def _ensure_server():
    import socket, subprocess, time
    s = socket.socket()
    try:
        s.connect(('127.0.0.1', 8765)); s.close(); return
    except OSError:
        pass
    subprocess.Popen(['python3', '-m', 'http.server', '8765'], cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    time.sleep(1)
_ensure_server()
