from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import json

root = Path(__file__).resolve().parents[1]
out = root / '.review'
out.mkdir(exist_ok=True)
groups = []
for folder in sorted(root.iterdir()):
    files = sorted(folder.glob('*.jpg')) if folder.is_dir() else []
    videos = sorted(folder.glob('*.mp4')) if folder.is_dir() else []
    if not files and not videos:
        continue
    group = {'folder': folder.name, 'images': [p.name for p in files], 'videos': [p.name for p in videos]}
    groups.append(group)
    if not files:
        continue
    sheet = Image.new('RGB', (1000, ((len(files)+3)//4)*225), '#ededed')
    draw = ImageDraw.Draw(sheet)
    for i, file in enumerate(files):
        with Image.open(file) as im:
            im = ImageOps.exif_transpose(im)
            im.thumbnail((244,195))
            x,y = (i%4)*250,(i//4)*225
            sheet.paste(im,(x+(250-im.width)//2,y))
            draw.text((x+8,y+199), f'{len(groups):02d} / {i+1:02d}  {file.stem[-8:]}', fill='black')
    sheet.save(out / f'group-{len(groups):02d}.jpg')
(out/'inventory.json').write_text(json.dumps(groups,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(groups,ensure_ascii=True))
