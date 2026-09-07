"""Find Commons archive candidates; selection is reviewed before publishing."""
import json,re,concurrent.futures,html
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode,unquote
root=Path(__file__).resolve().parents[1]
cache=root/'scripts/.archive-research';cache.mkdir(exist_ok=True)
records=json.loads((root/'public/collection.json').read_text())
alias={1:'Karna band Ukraine',2:'Степан Бурбан',3:'Уляна Дель Рей',4:'Alan Parsons',6:'Jiro Inagaki',8:'Glenn Miller',9:'Yes band',15:'Scott Joplin',20:'Barış Manço',22:'Glenn Miller',24:'Bee Gees',34:'Viktor Sodoma',36:'Katapult band',42:'Мертвий Півень',44:'Deep Purple',46:'Louis Armstrong',51:'Bill Haley',56:'Eva Olmerová',57:'Leopold Stokowski'}
for n in [5,21]:alias[n]='Yes band'
for n in [11,12,17,18,19]:alias[n]='Alan Parsons'
for r in records:r['searchName']=alias.get(r['number'],re.sub(r'\s*\(\d+\)|\*','',r['artist']))
def clean(v):return html.unescape(re.sub('<[^>]+>','',v)).strip()
def get(r):
 name=r['searchName'];dest=cache/(str(r['number'])+'.json')
 if dest.exists():return
 q='"'+name.replace(' band','')+'"'
 params={'action':'query','generator':'search','gsrsearch':q+' filetype:bitmap','gsrnamespace':6,'gsrlimit':18,'prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':960,'format':'json'}
 try:
  data=json.load(urlopen(Request('https://commons.wikimedia.org/w/api.php?'+urlencode(params),headers={'User-Agent':'WarmGrooves/1.0 personal music archive'}),timeout=30))
  photos=[]
  for p in data.get('query',{}).get('pages',{}).values():
   i=p.get('imageinfo',[{}])[0];m=i.get('extmetadata',{});field=lambda k:clean(m.get(k,{}).get('value',''))
   photos.append({'title':p['title'],'url':i.get('thumburl',i.get('url')),'originalUrl':i.get('url'),'page':i.get('descriptionurl'),'date':field('DateTimeOriginal'),'description':field('ImageDescription'),'author':field('Artist'),'license':field('LicenseShortName'),'licenseUrl':field('LicenseUrl'),'width':i.get('thumbwidth',960),'height':i.get('thumbheight',960)})
  dest.write_text(json.dumps(photos,ensure_ascii=False,indent=2));print(r['number'],name,len(photos),flush=True)
 except Exception as ex:print(r['number'],ex,flush=True)
# Group identical artists so the source is queried only once.
unique={}
for r in records:unique.setdefault(r['searchName'],r)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(get,unique.values()))
for r in records:
 first=unique[r['searchName']]['number'];p=cache/(str(first)+'.json')
 if p.exists() and first!=r['number']:(cache/(str(r['number'])+'.json')).write_text(p.read_text())
