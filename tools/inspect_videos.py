from pathlib import Path
import sys, json, subprocess, re
from PIL import Image, ImageDraw, ImageOps
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / '.tools/python'))
import imageio_ffmpeg
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
groups=json.loads((root/'.review/inventory.json').read_text(encoding='utf-8'))
records=[]
for gi,g in enumerate(groups,1):
    for vi,name in enumerate(g['videos'],1):
        path=root/g['folder']/name
        info=subprocess.run([ffmpeg,'-i',str(path)],capture_output=True).stderr.decode('utf-8',errors='replace')
        match=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',info)
        duration=sum(float(v)*m for v,m in zip(match.groups(),[3600,60,1]))
        record={'group':gi,'index':vi,'duration':duration,'audio':'Audio:' in info,'file':str(path.relative_to(root))}
        records.append(record)
        sheet=Image.new('RGB',(1200,340),'#eee')
        draw=ImageDraw.Draw(sheet)
        for j,fraction in enumerate([.08,.3,.55,.8]):
            frame=root/'.review'/f'video-{gi:02d}-{vi:02d}-{j}.jpg'
            subprocess.run([ffmpeg,'-y','-ss',str(duration*fraction),'-i',str(path),'-frames:v','1','-vf','scale=500:-1',str(frame)],capture_output=True,check=True)
            im=Image.open(frame); im.thumbnail((296,305))
            sheet.paste(im,(j*300+(300-im.width)//2,0))
            draw.text((j*300+8,315),f'{gi:02d}/{vi:02d} @ {duration*fraction:.1f}s / {duration:.1f}s',fill='black')
        sheet.save(root/'.review'/f'video-{gi:02d}-{vi:02d}.jpg')
(root/'.review/videos.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print(json.dumps(records))
