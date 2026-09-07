"""Rebuild the local catalogue from the supplied Markdown (no runtime API needed)."""
import re, json, concurrent.futures
from pathlib import Path
from urllib.request import Request, urlopen
ROOT = Path(__file__).resolve().parents[1]
source = (ROOT/'vinyl_collection.md').read_text()
records=[]
for match in re.finditer(r'^### (\d+)\. (.*?) — (.*?)\n(.*?)(?=^### \d+\.|\Z)', source, re.M|re.S):
    number, artist, title, body = match.groups()
    fields = dict(re.findall(r'^- \*\*(.*?):\*\* (.*)$',body,re.M))
    cover=re.search(r'!\[.*?\]\((.*?)\)',body).group(1)
    url=re.search(r'\*\*Discogs:\*\* \[(.*?)\]',body).group(1)
    sections={m.group(1):m.group(2).strip() for m in re.finditer(r'^#### (.*?)\n(.*?)(?=^#### |\Z)',body,re.M|re.S)}
    original=next((k for k in sections if k.startswith('Коли створено')), '')
    trackmatch=re.search(r'```text\n(.*?)```',body,re.S)
    tracks=[]
    if trackmatch:
        raw=trackmatch.group(1).strip()
        blocks=re.split(r'(?=^[A-Z]\d*\t)',raw,flags=re.M)
        for block in blocks:
            if not block.strip(): continue
            lines=block.strip().splitlines()
            parts=lines[0].split('\t')
            if len(parts)<2: continue
            position=parts[0].strip()
            duration=next(iter(re.findall(r'\b\d{1,2}:\d{2}\b',block)), '')
            if len(lines)>1:
                track_title=next((line.strip() for line in lines[1:] if line.startswith('\t') and not re.fullmatch(r'\s*\d+:\d+\s*',line)),parts[-1])
                track_artist=parts[1].strip().rstrip('*')
                if track_artist: track_title=track_artist+' — '+track_title
            else:
                track_title=' '.join(p.strip() for p in parts[1:] if p.strip() and p.strip()!=duration)
            tracks.append({'position':position,'duration':duration,'title':track_title})
    records.append({'id':int(re.search(r'/release/(\d+)',url).group(1)), 'number':int(number),'artist':artist.rstrip('*'), 'title':title, 'cover':f'/covers/{number}.jpg','coverSource':cover,'url':url,'date':fields.get('Рік і дата релізу','—'),'country':fields.get('Країна/ринок','—'),'genres':fields.get('Жанр / стиль','').split(', '),'format':fields.get('Формат',''), 'label':fields.get('Лейбл і каталожний номер','—'),'rating':fields.get('Моя оцінка','—'),'condition':fields.get('Стан медіа / конверта','—'),'community':fields.get('Середня оцінка Discogs','—'),'original':original.split(': ',1)[-1],'summaryUk':sections.get(original,''),'sectionsUk':{k:v for k,v in sections.items() if k in ['Розширена історія','Як створювали запис і що було складним','Ключові треки / на що звернути увагу','Візуальний та архівний контекст']},'tracks':tracks,'gallery':next(iter(re.findall(r'\]\((https://www.discogs.com/release/[^\s)]+/image/[^)]+)\)',body)),url+'/images'), 'sources':list(dict.fromkeys([url for label,url in re.findall(r'^- \[(.*?)\]\((.*)\)$',sections.get('Джерела та подальше читання',''),re.M)]))})
(ROOT/'public').mkdir(exist_ok=True)
(ROOT/'public/covers').mkdir(exist_ok=True)
def download(r):
    dest=ROOT/'public'/r['cover'].lstrip('/')
    if dest.exists(): return
    try:
        data=urlopen(Request(r['coverSource'],headers={'User-Agent':'VinylCollection/1.0'}),timeout=30).read()
        if not data.startswith(b'\xff\xd8'): raise ValueError('Not a JPEG')
        dest.write_bytes(data)
    except Exception as e: print(f"Cover {r['number']} failed: {e}")
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: list(pool.map(download,records))
supplements=ROOT/'public/tracklist-supplements.json'
if supplements.exists():
    extra=json.loads(supplements.read_text())
    for record in records:
        if not record['tracks']: record['tracks']=extra.get(str(record['id']),[])
(ROOT/'public/collection.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print(f'Prepared {len(records)} records; {len(list((ROOT/"public/covers").glob("*.jpg")))} local covers')
