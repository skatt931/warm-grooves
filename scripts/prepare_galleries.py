"""Bundle up to six photographs from each exact Discogs release, with provenance."""
import json,time,concurrent.futures
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
records=json.loads((ROOT/'public/collection.json').read_text())
out=ROOT/'public/gallery.json'
galleries=json.loads(out.read_text()) if out.exists() else {}
folder=ROOT/'public/gallery';folder.mkdir(exist_ok=True)
cache=ROOT/'scripts/.discogs-cache';cache.mkdir(exist_ok=True)
def get(url):return urlopen(Request(url,headers={'User-Agent':'WarmGroovesPersonalCollection/1.0'}),timeout=25).read()
for r in records:
    if str(r['id']) in galleries:continue
    cachefile=cache/f"{r['id']}.json"
    try:
        if cachefile.exists():data=json.loads(cachefile.read_text())
        else:
            data=json.loads(get(f"https://api.discogs.com/releases/{r['id']}"))
            cachefile.write_text(json.dumps(data))
            time.sleep(2.6)
        images=data.get('images',[])[:7]
        def photo(entry):
            n,img=entry
            dest=folder/f"{r['id']}-{n+1}.jpg"
            if not dest.exists():
                content=get(img['uri'])
                if not content.startswith(b'\xff\xd8'):raise ValueError('Unexpected image type')
                dest.write_bytes(content)
            return {'src':'/gallery/'+dest.name,'source':img['uri'],'releaseUrl':r['url'],'width':img.get('width',600),'height':img.get('height',600),'kind':'pressing','number':n+1}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: photos=list(pool.map(photo,enumerate(images)))
        galleries[str(r['id'])]=photos or [{'src':r['cover'],'source':r['coverSource'],'releaseUrl':r['url'],'kind':'pressing','number':1}]
        out.write_text(json.dumps(galleries,ensure_ascii=False,indent=2))
        print(r['number'],len(galleries[str(r['id'])]),flush=True)
    except Exception as error:print(r['number'],str(error),flush=True)
print('Galleries',len(galleries),'photos',sum(map(len,galleries.values())),flush=True)
