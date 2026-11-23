"""Create a self-contained direct-upload folder; never modify the source library."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import sys, json, shutil, subprocess, hashlib

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / '.tools/python'))
import imageio_ffmpeg
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
destination = root / 'cloudflare-upload'
destination.mkdir(exist_ok=True)
review = root / '.review/cloudflare'
review.mkdir(parents=True, exist_ok=True)
limit = 24_000_000  # Conservative margin below both 25 MB and 25 MiB.
target_bytes = 23_000_000
manifest = json.loads((root / 'assets/media-manifest.json').read_text(encoding='utf-8'))
items = [i for i in manifest['items'] if 'duplicateOf' not in i]
allowed = {'index.html'}
for folder in ['css', 'js', 'brand']:
    allowed.update(p.relative_to(root).as_posix() for p in (root/'assets'/folder).rglob('*') if p.is_file())
for item in items:
    allowed.update([item['src'], item['thumbnail']])
existing = {p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file()}
if existing - allowed:
    raise RuntimeError(f'Unexpected files in upload folder: {sorted(existing-allowed)}')
jobs = []
for name in sorted(allowed):
    source, target = root/name, destination/name
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.stat().st_size >= limit:
        item = next(i for i in items if i['src'] == name)
        assert item['type'] == 'video', name
        jobs.append((item, target))
    else:
        shutil.copy2(source, target)

def encode(job):
    item, target = job
    source = root / item['original']
    bitrate = int(target_bytes * 8 / item['duration'] * .97 - 64000)
    log = review / item['id']
    common = [ffmpeg, '-y', '-i', str(source), '-map', '0:v:0',
              '-c:v', 'libx264', '-preset', 'medium', '-b:v', str(bitrate),
              '-pix_fmt', 'yuv420p', '-threads', '2', '-passlogfile', str(log)]
    print(f"Encoding full video: {item['id']}", flush=True)
    for args in [common + ['-pass', '1', '-an', '-f', 'null', 'NUL'],
                 common + ['-map', '0:a:0?', '-pass', '2', '-c:a', 'aac', '-b:a', '64k',
                           '-movflags', '+faststart', str(target)]]:
        result = subprocess.run(args, capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stderr.decode(errors='replace')[-3000:])
    assert target.stat().st_size < limit, (target, target.stat().st_size)
    check = subprocess.run([ffmpeg, '-v', 'error', '-i', str(target), '-f', 'null', 'NUL'], capture_output=True)
    assert check.returncode == 0 and not check.stderr, check.stderr.decode(errors='replace')
    info = subprocess.run([ffmpeg, '-i', str(target)], capture_output=True).stderr.decode(errors='replace')
    assert 'Audio:' in info, 'Audio stream missing'
    print(f"Verified video + audio: {target.name} ({target.stat().st_size/1e6:.2f} MB)", flush=True)
    return {'file':item['src'], 'beforeBytes':(root/item['src']).stat().st_size,'afterBytes':target.stat().st_size}

with ThreadPoolExecutor(max_workers=2) as pool:
    compressed = list(pool.map(encode, jobs))

class References(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ['src','href'] and value and value.startswith('assets/'):
                assert (destination/value).is_file(), value
References().feed((destination/'index.html').read_text(encoding='utf-8'))
for item in items:
    assert (destination/item['src']).is_file()
    assert (destination/item['thumbnail']).is_file()
for name in allowed:
    output = destination/name
    assert output.stat().st_size < limit, name
    if name not in {i['file'] for i in compressed}:
        assert hashlib.sha256(output.read_bytes()).digest() == hashlib.sha256((root/name).read_bytes()).digest(), name
for item in manifest['items']:
    assert hashlib.sha256((root/item['original']).read_bytes()).hexdigest() == item['sha256']
report = {'folder':destination.name,'files':len(allowed),'photos':sum(i['type']=='image' for i in items),
          'videos':sum(i['type']=='video' for i in items),'largestFileBytes':max((destination/name).stat().st_size for name in allowed),
          'compressed':compressed,'unchangedOriginals':len(manifest['items']),
          'identicalDesign':True,'totalBytes':sum((destination/name).stat().st_size for name in allowed)}
(review/'package-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2),flush=True)
