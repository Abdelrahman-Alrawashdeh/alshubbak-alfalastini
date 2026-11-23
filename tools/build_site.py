"""One-time migration of the existing static site to the reviewed media library."""
from pathlib import Path
import re,json,html,shutil
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'assets/media-manifest.json').read_text(encoding='utf-8'))
items=[i for i in data['items'] if 'duplicateOf' not in i]
def find(fragment): return next(i for i in items if fragment in i['id'])
def esc(s): return html.escape(str(s),quote=True)
def duration(i):
    seconds=int(i.get('duration',0)); return f'{seconds//60}:{seconds%60:02d}'
def picture(i,cls='',thumb=True):
    src=i['thumbnail'] if thumb else i['src']
    return f'<img class="{cls}" src="{src}" alt="{esc(i["title"])}" width="{i["width"]}" height="{i["height"]}" loading="lazy" decoding="async">'
def trigger(i,cls='',label=None):
    return f'<a class="media-open {cls}" href="{i["src"]}" data-media="{i["id"]}" aria-label="{esc(label or i["title"])}">'
def play(i): return f'<span class="play-circle" aria-hidden="true">▶</span><span class="media-duration" dir="ltr">{duration(i)}</span>'
source=(root/'index.html').read_text(encoding='utf-8')
(root/'.review/index-before.html').write_text(source,encoding='utf-8')
for folder in ['css','js','brand']: (root/'assets'/folder).mkdir(parents=True,exist_ok=True)
base=re.search(r'<style>(.*?)</style>',source,re.S).group(1)
(root/'assets/css/base.css').write_text(base,encoding='utf-8')
source=re.sub(r'    <style>.*?</style>', '    <link rel="stylesheet" href="assets/css/base.css">',source,count=1,flags=re.S)
source=source.replace('href="design.css"','href="assets/css/design.css"')
source=source.replace('</head>','    <link rel="stylesheet" href="assets/css/media.css">\n    <meta name="theme-color" content="#151918">\n</head>')
source=source.replace('src="logo.svg"','src="assets/brand/logo.svg"').replace('href="logo.svg"','href="assets/brand/logo.svg"')
source=source.replace('<a href="#kitchens">المطابخ</a>','<a href="#gallery">الصور والفيديوهات</a>')
source=source.replace('اكتشف منتجاتنا</a>','اكتشف أقسامنا</a>')
intro=find('about-01-company-and')
source=source.replace('<div class="hero-assurance">',trigger(intro,'hero-film')+f'<span class="mini-play" aria-hidden="true">▶</span><span>حكايتنا في دقيقة<small>شاهد فيلم الشركة · {duration(intro)}</small></span><span aria-hidden="true">↗</span></a><div class="hero-assurance">')
source=source.replace('<section id="about">','<div class="chapter-nav"><div class="wrap"><span>اكتشف التفاصيل</span><a href="#products">01 / الشبابيك</a><a href="#kitchens">02 / المطابخ</a><a href="#craft">03 / من الورشة</a><a href="#gallery">04 / مكتبة الصور والأفلام</a></div></div>\n    <section id="about">')
about_feature=f'''<div class="company-feature">
 {trigger(intro,'company-film')}{picture(intro)}{play(intro)}<span class="film-caption">الشباك الفلسطيني <small>فيلم تعريفي بالشركة</small></span></a>
 <div class="company-note"><span class="eyebrow">من الفكرة إلى التفاصيل</span><h3>لكل مشروع حكاية.<br>ولكل تفصيلة اهتمام.</h3><p>تعرّف على عالم الشباك الفلسطيني، ثم اقترب من المنتجات ومراحل العمل في مكتبتنا المرئية.</p><a class="text-link" href="#gallery" data-category-link="about">اكتشف مواد الشركة <span aria-hidden="true">↖</span></a></div></div>'''
source=source.replace('<div class="pillars">',about_feature+'\n<div class="pillars">',1)
products=[]
for number,category,title,desc,fragment,value in [
 ('01','windows-7000c','شبابيك 7000C','تفاصيل القطاع، مكوّنات الشباك ومراحل التركيب. اكتشف النظام عن قرب في الصور والفيديوهات.','windows-7000c-02-system-introduction','7000C'),
 ('02','windows-9000c','شبابيك 9000C','تعرّف على قطاع السحاب ومسارات الحركة وخيارات الفتح، وشاهد تجربة تشغيل الشباك.','windows-9000c-03-sliding-window-operation','9000C'),
 ('03','kitchens','مطابخ حسب مساحتك','من توزيع الخزائن إلى الإكسسوارات. شاهد صور المطبخ المنفّذ وتفاصيل تصميم المطابخ.','installed-kitchen-wide-view','مطابخ حديثة')]:
    i=find(fragment)
    products.append(f'''<article class="product-card" data-product="{value}"><a class="product-visual" href="#gallery" data-category-link="{category}">{picture(i)}<span class="product-number">{number}</span><span class="visual-caption">{'استكشف الأفلام والتفاصيل' if i['type']=='video' else 'من أعمالنا'} ↗</span></a><div class="body"><h3>{title}</h3><p>{desc}</p><a class="text-link" href="#gallery" data-category-link="{category}">استكشف القسم <span aria-hidden="true">↖</span></a></div></article>''')
start=source.index('            <div class="product-grid">')
end=source.index('    <section class="kitchen-section"',start)
source=source[:start]+'<div class="product-grid">'+''.join(products)+'</div></div></section>\n\n'+source[end:]
kitchen=find('installed-kitchen-corner')
source=re.sub(r'<div class="kitchen-media">.*?</div>',f'<div class="kitchen-media">{trigger(kitchen)}{picture(kitchen,thumb=False)}<span class="image-expand">عرض الصورة كاملة ↗</span></a><span class="project-caption">من أعمالنا / مطبخ بخزائن فاتحة وتفاصيل خشبية</span></div>',source,count=1,flags=re.S)
source=source.replace('href="https://wa.me/962796563548" target="_blank" rel="noopener noreferrer" class="btn btn-primary">اطلب عرض سعر لمطبخك','href="#gallery" data-category-link="kitchens" class="btn btn-primary">استكشف صور المطابخ')
workshop=find('workshop-cutting'); testing=find('candle-and-airflow')
craft=f'''<section id="craft" class="craft-section"><div class="wrap"><div class="section-head"><span class="eyebrow">وراء كل تفصيلة</span><h2>من داخل الورشة،<br>إلى تجربة الشباك.</h2><p class="lede">شاهد مراحل العمل وتفاصيل التنفيذ في لقطات قريبة من المنتج.</p></div><div class="craft-grid">'''
for i,kicker,title,desc in [(workshop,'01 / التصنيع','دقّة تبدأ من أول قصّة.','جولة في قصّ وتجهيز قطاعات الألمنيوم، من القياس إلى العمل على الماكينة.'),(testing,'02 / تجربة توضيحية','تفاصيل الإغلاق، عن قرب.','شاهد تجربة الشمعة وتيار الهواء حول الشباك، كما تظهر في الفيديو.')]:
    craft+=f'<article class="craft-card">{trigger(i,"craft-visual")}{picture(i)}{play(i)}</a><div class="craft-copy"><span class="eyebrow">{kicker}</span><h3>{title}</h3><p>{desc}</p>{trigger(i,"text-link")}شاهد الفيديو <span aria-hidden="true">↖</span></a></div></article>'
craft+='</div><p class="craft-footnote">فيديو تجربة الشمعة عرض توضيحي للمنتج، وليس تقرير فحص مخبري معتمد.</p></div></section>'
source=source.replace('    <section class="on-dark " id="why-us">',craft+'\n    <section class="on-dark " id="why-us">')
# Curate first page: finished project, introductions, fabrication, testing, then technical material.
priority=['installed-kitchen-wide-view','windows-7000c-02-system-introduction','windows-9000c-03-sliding-window-operation','workshop-cutting','candle-and-airflow','about-01-company-and','windows-7000c-03-system-overview','windows-9000c-02-technical-profile','installed-kitchen-corner']
ordered=[find(f) for f in priority]
ordered+= [i for i in items if i not in ordered]
gallery='''<section id="gallery" class="media-library"><div class="wrap"><div class="library-heading"><div class="section-head"><span class="eyebrow">المكتبة المرئية</span><h2>شاهد التفاصيل.<br><em>واكتشف الفرق بنفسك.</em></h2><p class="lede">صور المشاريع، تفاصيل المنتجات، وأفلام من مراحل العمل. كل قسم في مكان واحد.</p></div><div class="library-index"><strong>06</strong><span>أقسام من عالمنا</span></div></div><div class="library-toolbar"><div class="category-filters" role="group" aria-label="تصفية حسب القسم"><button class="category-filter active" type="button" data-category="all" aria-pressed="true">كل الأقسام</button>'''
for c in data['categories']:
    gallery+=f'<button class="category-filter" type="button" data-category="{c["id"]}" aria-pressed="false">{c["label"]}</button>'
gallery+='''</div><div class="library-options"><div class="type-filters" role="group" aria-label="نوع الوسائط"><button type="button" data-type="all" aria-pressed="true" class="active">الكل</button><button type="button" data-type="image" aria-pressed="false">صور</button><button type="button" data-type="video" aria-pressed="false">فيديوهات</button></div><p id="mediaCount" role="status" aria-live="polite"></p></div></div><div class="media-grid" id="mediaGrid">'''
for i in ordered:
    tag='فيديو' if i['type']=='video' else ('من أعمالنا' if i['presentation']=='project' else 'تفاصيل ومعلومات')
    gallery+=f'<article class="media-card" data-category="{i["category"]}" data-type="{i["type"]}">{trigger(i,"media-card-link")}<div class="media-card-visual {i["presentation"]}">{picture(i)}<span class="media-tag">{tag}</span>{play(i) if i["type"]=="video" else "<span class=\"expand-icon\" aria-hidden=\"true\">↗</span>"}</div><div class="media-card-copy"><span>{i["categoryLabel"]}</span><h3>{esc(i["title"])}</h3></div></a></article>'
gallery+='''</div><p id="mediaEmpty" class="empty-state" hidden>لا توجد فيديوهات في هذا القسم حاليًا. اختر الصور لاستكشاف المحتوى.</p><div class="library-more"><button class="btn btn-outline" type="button" id="loadMore" hidden>عرض المزيد <span aria-hidden="true">↓</span></button></div></div></section>'''
source=re.sub(r'    <!--\s*<section id="gallery.*?-->',gallery,source,count=1,flags=re.S)
dialog='''<dialog class="media-dialog" id="mediaDialog" aria-labelledby="viewerTitle"><div class="viewer-top"><span id="viewerCategory"></span><button class="viewer-close" type="button" aria-label="إغلاق العرض">✕</button></div><div class="viewer-stage" id="viewerStage"></div><div class="viewer-bottom"><div><h2 id="viewerTitle"></h2><p id="viewerPosition" aria-live="polite"></p></div><div class="viewer-navigation"><button type="button" id="previousMedia" aria-label="الوسيط السابق">→</button><button type="button" id="nextMedia" aria-label="الوسيط التالي">←</button></div></div><a class="viewer-original" id="viewerOriginal" target="_blank" rel="noopener">افتح الملف في صفحة مستقلة ↗</a></dialog>'''
source=source.replace('    <script>','    '+dialog+'\n    <script>',1)
# Keep existing form/menu/reveal behavior, remove unused old gallery handlers.
source=re.sub(r"        const filterBtns = .*?        const revealEls",'        const revealEls',source,count=1,flags=re.S)
source=source.replace('src="effects.js"','src="assets/js/effects.js"')
source=source.replace('</body>','    <script src="assets/js/media-data.js"></script>\n    <script src="assets/js/media.js"></script>\n</body>')
(root/'index.html').write_text(source,encoding='utf-8')
shutil.copy2(root/'design.css',root/'assets/css/design.css')
shutil.copy2(root/'effects.js',root/'assets/js/effects.js')
shutil.copy2(root/'logo.svg',root/'assets/brand/logo.svg')
(root/'assets/js/media-data.js').write_text('window.COMPANY_MEDIA = '+json.dumps({'items':items},ensure_ascii=False)+';\n',encoding='utf-8')
print(f'Built static gallery with {len(ordered)} unique media items.')
