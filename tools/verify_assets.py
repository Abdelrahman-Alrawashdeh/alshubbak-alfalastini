from pathlib import Path
from html.parser import HTMLParser
import json, hashlib
root=Path(__file__).resolve().parents[1]
class References(HTMLParser):
    paths=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ('src','href') and value and value.startswith('assets/'):
                self.paths.append(value)
refs=References(); refs.feed((root/'index.html').read_text(encoding='utf-8'))
missing=[path for path in refs.paths if not (root/path).is_file()]
assert not missing, missing
manifest=json.loads((root/'assets/media-manifest.json').read_text(encoding='utf-8'))
for item in manifest['items']:
    assert hashlib.sha256((root/item['original']).read_bytes()).hexdigest()==item['sha256'],item['id']
    if 'duplicateOf' not in item:
        assert (root/item['src']).is_file(),item['id']
        assert (root/item['thumbnail']).is_file(),item['id']
original=sum((root/i['original']).stat().st_size for i in manifest['items'])
web=sum(p.stat().st_size for p in (root/'assets').rglob('*') if p.is_file() and 'originals' not in p.parts)
result={'verifiedOriginals':len(manifest['items']),'uniqueMedia':sum('duplicateOf' not in i for i in manifest['items']),'verifiedHtmlReferences':len(refs.paths),'originalMB':round(original/1e6,2),'webAssetsMB':round(web/1e6,2),'missing':missing}
(root/'.review/assets-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
