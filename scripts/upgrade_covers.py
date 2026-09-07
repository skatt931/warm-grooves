"""Optional: fetch higher-resolution covers for the exact Discogs pressing."""
import json,time
from pathlib import Path
from urllib.request import Request,urlopen
root=Path(__file__).resolve().parents[1]
records=json.loads((root/'public/collection.json').read_text())
for r in sorted(records,key=lambda r:r['number']!=19):
    dest=root/'public'/r['cover'].lstrip('/')
    if dest.stat().st_size>18000: continue
    try:
        request=Request(f"https://api.discogs.com/releases/{r['id']}",headers={'User-Agent':'WarmGroovesPersonalCollection/1.0'})
        data=json.load(urlopen(request,timeout=20))
        image=next((i for i in data.get('images',[]) if i['type']=='primary'),next(iter(data.get('images',[])),None))
        if image:
            content=urlopen(Request(image['uri'],headers={'User-Agent':'WarmGroovesPersonalCollection/1.0'}),timeout=20).read()
            if content.startswith(b'\xff\xd8'): dest.write_bytes(content)
        print(r['number'],dest.stat().st_size,flush=True)
    except Exception as e: print(r['number'],str(e),flush=True)
    time.sleep(2.6)
