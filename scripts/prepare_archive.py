"""Rebuild local artist archives from the reviewed source manifest.

The manifest preserves the selected image's caption, photograph date, author,
license and original Commons page. It does not substitute live search results.
"""
import json,time
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'scripts/archive-sources.json').read_text())
for photos in manifest.values():
    for photo in photos:
        destination=ROOT/'public'/photo['src'].lstrip('/')
        if destination.exists():continue
        destination.parent.mkdir(parents=True,exist_ok=True)
        request=Request(photo['url'],headers={'User-Agent':'WarmGroovesArchive/1.0 (personal vinyl catalogue)'})
        content=urlopen(request,timeout=35).read()
        if not(content.startswith(b'\xff\xd8')or content.startswith(b'\x89PNG')):
            raise ValueError(f"Unexpected file type for {photo['source']}")
        destination.write_bytes(content)
        time.sleep(2)
(ROOT/'public/archive.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(f'Prepared artist archives for {len(manifest)} releases.')
