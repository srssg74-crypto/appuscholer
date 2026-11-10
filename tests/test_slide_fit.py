"""A long slide never loses its last lines, in a short window as well as full screen (build 2026.11.10y)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import new_page
from playwright.sync_api import sync_playwright
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    errors=[]; b,pg=new_page(p,errors,viewport={'width':1366,'height':650}); J=lambda js: pg.evaluate(js)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    J("""_pptxSlideModel=[{title:'Made up slide',bullets:['Made up first point that runs on for a long line of words so that it wraps onto a second line here.','Second point that also runs on for a long line of words so that it wraps onto a second line here.','Third made up point with another long line of words so that it wraps onto a second line of text.','Fourth made up point with another long line of words so that it wraps onto a second line of text.','Fifth made up point with another long line of words so that it wraps onto a second line of text.','Sixth made up point which also runs long enough to wrap onto a second line of the slide.','Seventh made up point which also runs long enough to wrap onto a second line of the slide.']}];ssOpen()""")
    pg.wait_for_timeout(400)
    r=J("(()=>{const s=document.getElementById('ssSlide'),li=[...s.querySelectorAll('li')].pop().getBoundingClientRect(),sr=s.getBoundingClientRect();return {last:li.bottom,slide:sr.bottom,fs:parseFloat(getComputedStyle(s).fontSize)}})()")
    ok(r['last']<=r['slide']+1,'last line is inside the slide (%.0f <= %.0f), type %.1fpx'%(r['last'],r['slide'],r['fs']))
    ok(not [e for e in errors if 'Failed to load resource' not in str(e)],'no page errors %s'%errors)
    b.close()
print('failures:',len(fails)); sys.exit(1 if fails else 0)
