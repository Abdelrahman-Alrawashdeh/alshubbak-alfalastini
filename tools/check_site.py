from pathlib import Path
import sys, threading, json, functools
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
root=Path(__file__).resolve().parents[1]
site_root=(root/sys.argv[1]).resolve() if len(sys.argv)>1 else root
sys.path.insert(0,str(root/'.tools/python'))
from playwright.sync_api import sync_playwright
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
    def copyfile(self,source,outputfile):
        try: super().copyfile(source,outputfile)
        except (ConnectionResetError,ConnectionAbortedError,BrokenPipeError): pass
server=ThreadingHTTPServer(('127.0.0.1',8765),functools.partial(QuietHandler,directory=str(site_root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
errors=[]; results={}
manifest=json.loads((root/'assets/media-manifest.json').read_text(encoding='utf-8'))
for item in manifest['items']:
    for key in ['src','thumbnail','original']:
        if key in item:
            base=root if key=='original' else site_root
            assert (base/item[key]).is_file(), f'Missing {item[key]}'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8765',wait_until='networkidle')
    page.screenshot(path=str(root/'.review/desktop-home.png'))
    assert page.locator('.media-card:visible').count()==9
    assert page.locator('video').count()==0
    results['noInitialVideoDownload']=page.evaluate("performance.getEntriesByType('resource').filter(e=>e.name.includes('.mp4')).length === 0")
    page.locator('#gallery').evaluate('(el)=>window.scrollTo({top:el.offsetTop-90,behavior:"instant"})')
    page.locator('.media-card:visible img').evaluate_all('(imgs)=>Promise.all(imgs.map(img=>{img.loading="eager";return img.decode()}))')
    page.wait_for_timeout(500)
    page.screenshot(path=str(root/'.review/desktop-gallery.png'))
    for section in ['products','kitchens','craft']:
        page.locator(f'#{section}').evaluate('(el)=>window.scrollTo({top:el.offsetTop-90,behavior:"instant"})')
        page.locator(f'#{section} img').evaluate_all('(imgs)=>Promise.all(imgs.map(img=>{img.loading="eager";return img.decode()}))')
        page.wait_for_timeout(900)
        page.screenshot(path=str(root/f'.review/desktop-{section}.png'))
    counts={}
    for category in ['windows-7000c','windows-9000c','kitchens','aluminium-fabrication','window-testing','about']:
        page.locator(f'button[data-category="{category}"]').click()
        counts[category]=page.locator('#mediaCount').inner_text()
        assert page.locator('.media-card:visible').count()>0
    results['categories']=counts
    page.locator('button[data-category="kitchens"]').click()
    page.locator('button[data-type="video"]').click()
    assert page.locator('#mediaEmpty').is_visible()
    page.locator('button[data-type="image"]').click()
    page.locator('.media-card:visible a').first.click()
    assert page.locator('#mediaDialog').is_visible()
    assert page.locator('#viewerStage img').evaluate('(img)=>img.complete && img.naturalWidth>0')
    first_title=page.locator('#viewerTitle').inner_text()
    page.locator('#nextMedia').click()
    assert page.locator('#viewerTitle').inner_text()!=first_title
    page.keyboard.press('Escape'); assert not page.locator('#mediaDialog').is_visible()
    page.locator('button[data-category="all"]').click(); page.locator('button[data-type="all"]').click()
    page.locator('#loadMore').click(); assert page.locator('.media-card:visible').count()==18
    page.locator('button[data-type="video"]').click()
    page.locator('.media-card:visible a').first.click()
    page.wait_for_function("document.querySelector('#viewerStage video').readyState>=2",timeout=30000)
    results['videoDuration']=page.locator('#viewerStage video').evaluate('(v)=>v.duration')
    page.locator('#viewerStage video').evaluate('(v)=>{v.pause();v.currentTime=12;}')
    page.wait_for_timeout(500)
    page.screenshot(path=str(root/'.review/desktop-video.png'))
    page.locator('.viewer-close').click(); assert page.locator('video').count()==0
    video_results=[]
    for item in json.loads((root/'assets/media-manifest.json').read_text(encoding='utf-8'))['items']:
        if item['type']!='video': continue
        result=page.evaluate('''async (item) => {
          const video=document.createElement('video'); video.preload='metadata'; video.muted=true;
          document.body.append(video);
          try {
            await new Promise((resolve,reject)=>{
              const timer=setTimeout(()=>reject(new Error('metadata timeout: '+item.id)),20000);
              video.onloadedmetadata=()=>{clearTimeout(timer);resolve()};
              video.onerror=()=>{clearTimeout(timer);reject(new Error('video error: '+item.id))};
              video.src=item.src;
            });
            return {id:item.id,duration:video.duration,width:video.videoWidth,height:video.videoHeight};
          } finally {video.pause();video.removeAttribute('src');video.load();video.remove()}
        }''',item)
        assert abs(result['duration']-item['duration'])<1
        assert result['width']>0
        video_results.append(result)
    results['allVideoMetadata']=video_results
    page.locator('.window-control').scroll_into_view_if_needed(); page.locator('.window-control').click()
    assert page.locator('.window-control').get_attribute('aria-pressed')=='true'
    for width in [390,768,1440]:
        page.set_viewport_size({'width':width,'height':844})
        page.goto('http://127.0.0.1:8765',wait_until='networkidle')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), f'Overflow at {width}'
        if width==390:
            page.screenshot(path=str(root/'.review/mobile-home.png'))
            page.locator('#navToggle').click(); assert page.locator('#mobileMenu').is_visible()
            page.locator('#mobileMenu a[href="#gallery"]').click(); assert not page.locator('#mobileMenu').is_visible()
            page.locator('#gallery').scroll_into_view_if_needed(); page.wait_for_timeout(300)
            page.screenshot(path=str(root/'.review/mobile-gallery.png'))
    page.emulate_media(reduced_motion='reduce')
    page.goto('http://127.0.0.1:8765',wait_until='networkidle')
    results['reducedMotion']=page.locator('.window-object').evaluate('(el)=>getComputedStyle(el).transitionDuration')
    page.locator('button[data-category="all"]').click(); page.locator('button[data-type="all"]').click()
    while page.locator('#loadMore').is_visible(): page.locator('#loadMore').click()
    assert page.locator('.media-card:visible').count()==47
    page.locator('img').evaluate_all('(imgs)=>Promise.all(imgs.map(img=>{img.loading="eager";return img.decode()}))')
    results['decodedImages']=page.locator('img').count()
    results['brokenImages']=page.evaluate('[...document.images].filter(i=>i.complete && i.naturalWidth===0).map(i=>i.src)')
    assert not results['brokenImages']
    assert not errors, errors
    browser.close()
server.shutdown()
results['pageErrors']=errors
(root/'.review/verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=True,indent=2))
