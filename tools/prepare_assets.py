"""Build web assets without modifying source media; retain a complete source map."""
from pathlib import Path
from PIL import Image, ImageOps
import sys, json, hashlib, subprocess, shutil
from concurrent.futures import ThreadPoolExecutor
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'.tools/python'))
import imageio_ffmpeg
ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
groups=json.loads((root/'.review/inventory.json').read_text(encoding='utf-8'))
video_info=json.loads((root/'.review/videos.json').read_text(encoding='utf-8'))
categories=[('windows-7000c','شبابيك 7000C'),('windows-9000c','شبابيك 9000C'),('window-testing','تجربة العزل'),('aluminium-fabrication','قصّ الألمنيوم'),('kitchens','المطابخ'),('about','عن الشركة')]
image_names=[
 [('white-window-overview','شباك أبيض 7000C — نظرة عامة'),('engineered-profile','تفاصيل تصميم قطاع 7000C'),('system-overview','منظومة شباك 7000C'),('winter-sealing','تفاصيل الإغلاق في الشتاء'),('acoustic-thermal-design','تصميم العزل والصوت'),('profile-strength','بنية قطاع الألمنيوم'),('insulation-components','مكوّنات منظومة العزل'),('installation-steps','مراحل تركيب الشباك'),('leakage-prevention','تفاصيل الحد من التسريب'),('candle-demonstration','عرض تجربة الشمعة'),('specifications-details','المواصفات وتفاصيل التنفيذ'),('small-components','الإكسسوارات والتفاصيل الصغيرة'),('sealed-profile-design','تصميم القطاع والإغلاق'),('material-selection','اختيار مكوّنات الشباك'),('design-to-installation','من التصميم إلى التركيب')],
 [('integrated-system','منظومة 9000C المتكاملة'),('technical-profile','تفاصيل قطاع 9000C'),('sliding-track','قاعدة ومسار الشباك السحاب'),('weather-sealing','تفاصيل الإغلاق ومقاومة العوامل الجوية'),('opening-options','خيارات الفتح والتصميم'),('large-panel-base','قاعدة الدرف الكبيرة'),('glazing-details','الزجاج وتفاصيل العزل'),('profile-comparison','مقارنة توضيحية للقطاعات'),('shutter-integration','الأباجور وتكامل الشباك')],[],[],
 [('daily-function','مطبخ مصمّم للاستخدام اليومي'),('space-planning','توزيع مساحة المطبخ'),('craftsmanship','خبرة وتفاصيل صناعة المطابخ'),('craftsmanship-duplicate','خبرة وتفاصيل صناعة المطابخ — نسخة مكررة'),('durable-materials','خامات وتفاصيل خزائن المطبخ'),('custom-layout','تقسيم المطبخ حسب المساحة'),('installed-kitchen-corner','مطبخ منفّذ — الخزائن الركنية'),('installed-kitchen-tall-cabinet','مطبخ منفّذ — الخزانة الطويلة'),('hardware-details','الإكسسوارات وتفاصيل المطبخ'),('installed-kitchen-wide-view','مطبخ منفّذ — المشهد الكامل'),('planning-checklist','تفاصيل تخطيط المطبخ')],
 [('quality-from-first-cut','الجودة من أول مرحلة'),('project-stages','مراحل تنفيذ المشروع'),('company-experience','نبذة عن خبرة الشركة'),('aluminium-expertise','التخصص في صناعة الألمنيوم')]
]
video_names={1:[('profile-components-walkthrough','شرح قطاع 7000C ومكوّناته',.3),('system-introduction','تعرّف على منظومة 7000C',.3),('installation-and-shutters','تفاصيل التركيب والأباجور',.55)],2:[('profile-and-assembly-details','تفاصيل قطاع 9000C وتجميعه',.3),('sliding-system-introduction','شرح منظومة السحاب 9000C',.55),('sliding-window-operation','تجربة فتح وإغلاق الشباك السحاب',.08)],3:[('candle-and-airflow-demonstration','تجربة الشمعة وتيار الهواء',.3)],4:[('workshop-cutting-and-machining','من الورشة: قصّ وتجهيز الألمنيوم',.3)],6:[('company-and-manufacturing-introduction','الشباك الفلسطيني — تعرّف علينا',.3)]}
items=[]; moves=[]; seen={}; jobs=[]
for gi,(group,(category,label)) in enumerate(zip(groups,categories),1):
    for kind,files in [('image',group['images']),('video',group['videos'])]:
        for i,filename in enumerate(files):
            source=root/group['folder']/filename
            slug,title=(image_names[gi-1][i] if kind=='image' else video_names[gi][i][:2])
            stem=f'{category}-{i+1:02d}-{slug}'
            original=f'assets/{category}/originals/{stem}{source.suffix}'
            digest=hashlib.sha256(source.read_bytes()).hexdigest()
            moves.append({'source':str(source.relative_to(root)),'target':original,'sha256':digest})
            item={'id':stem,'category':category,'categoryLabel':label,'type':kind,'title':title,'original':original,'sha256':digest}
            if digest in seen:
                item['duplicateOf']=seen[digest]; items.append(item); continue
            seen[digest]=stem
            if kind=='image':
                folder=root/'assets'/category/'images'; folder.mkdir(parents=True,exist_ok=True)
                im=ImageOps.exif_transpose(Image.open(source)).convert('RGB')
                item.update({'width':im.width,'height':im.height,'presentation':'project' if 'installed-kitchen' in slug else 'editorial'})
                im.save(folder/f'{stem}.webp','WEBP',quality=88,method=6)
                item['src']=f'assets/{category}/images/{stem}.webp'
                im.thumbnail((520,700)); im.save(folder/f'{stem}-thumb.webp','WEBP',quality=82,method=6)
                item['thumbnail']=f'assets/{category}/images/{stem}-thumb.webp'
            else:
                info=next(v for v in video_info if v['group']==gi and v['index']==i+1)
                item.update({'duration':round(info['duration'],2),'hasAudio':info['audio'],'src':f'assets/{category}/videos/{stem}.mp4','thumbnail':f'assets/{category}/posters/{stem}.webp','presentation':'video'})
                (root/item['src']).parent.mkdir(parents=True,exist_ok=True)
                (root/item['thumbnail']).parent.mkdir(parents=True,exist_ok=True)
                frame=root/'.review'/f'poster-{stem}.png'
                subprocess.run([ffmpeg,'-y','-ss',str(info['duration']*video_names[gi][i][2]),'-i',str(source),'-frames:v','1','-vf','scale=720:-2',str(frame)],capture_output=True,check=True)
                im=Image.open(frame); item.update({'width':im.width,'height':im.height})
                im.save(root/item['thumbnail'],'WEBP',quality=85)
                jobs.append((source,root/item['src']))
            items.append(item)
assets=root/'assets'; assets.mkdir(exist_ok=True)
(assets/'media-manifest.json').write_text(json.dumps({'categories':[{'id':c,'label':l} for c,l in categories],'items':items},ensure_ascii=False,indent=2),encoding='utf-8')
(root/'.review/move-map.json').write_text(json.dumps(moves,ensure_ascii=False,indent=2),encoding='utf-8')
def encode(job):
    source,target=job
    if target.exists(): return
    result=subprocess.run([ffmpeg,'-y','-i',str(source),'-map','0:v:0','-map','0:a:0?','-vf',"scale='min(720,iw)':-2",'-c:v','libx264','-preset','fast','-crf','25','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-movflags','+faststart','-threads','2',str(target)],capture_output=True)
    if result.returncode: raise RuntimeError(result.stderr.decode(errors='replace')[-1500:])
    if target.stat().st_size > source.stat().st_size:
        subprocess.run([ffmpeg,'-y','-i',str(source),'-c','copy','-movflags','+faststart',str(target)],capture_output=True,check=True)
    print(f'Prepared {target.name}: {target.stat().st_size}',flush=True)
with ThreadPoolExecutor(max_workers=2) as pool: list(pool.map(encode,jobs))
print(f'Catalogued {len(items)} source files',flush=True)
