import { readdir, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const files=await readdir('dist',{recursive:true,withFileTypes:true});
const urls=files.filter(f=>f.isFile()&&f.name!=='sw.js').map(f=>'./' + `${f.parentPath}/${f.name}`.replace(/^dist\//,''));
const hash=createHash('sha256');hash.update(await readFile('scripts/build-sw.js'));for(const url of urls)hash.update(await readFile('dist'+url));
const version='warm-grooves-'+hash.digest('hex').slice(0,12);
await writeFile('dist/sw.js',`const CACHE=${JSON.stringify(version)};
const ASSETS=${JSON.stringify(['./',...urls])};
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('warm-grooves-')&&key!==CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',event=>{if(event.request.method!=='GET'||new URL(event.request.url).origin!==self.location.origin)return;
 if(event.request.mode==='navigate'){event.respondWith(fetch(event.request).catch(()=>caches.match('./')));return;}
 event.respondWith(caches.match(event.request,{ignoreVary:true}).then(cached=>cached||fetch(event.request)));
});`);
console.log(`Offline cache: ${urls.length+1} assets (${version})`);
