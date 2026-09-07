export function arrangeInserts(dialog,lang){
 const article=dialog.querySelector('.record-story');
 const wrap=(nodes,id)=>{const section=document.createElement('section');section.className='album-insert';section.id=id;nodes[0].before(section);nodes.forEach(n=>section.append(n));return section;};
 const historyHeading=article.querySelector('h3');
 const history=wrap([historyHeading,article.querySelector('.summary'),...article.querySelectorAll('.story-note')],'album-history');
 const tracks=wrap([article.querySelector('.track-heading'),article.querySelector('.tracklist')],'album-tracks');
 const sources=article.querySelector('.source-links');sources.classList.add('album-insert');
 const gallery=dialog.querySelector('.release-gallery');gallery.id='album-photos';gallery.classList.add('album-insert','photo-insert');
 const navigation=document.createElement('nav');navigation.className='insert-nav';navigation.setAttribute('aria-label',lang==='uk'?'Розділи альбому':'Album sections');
 for(const [id,label]of [['album-history',lang==='uk'?'Історія':'Story'],['album-photos',lang==='uk'?'Фото':'Photos'],['album-tracks',lang==='uk'?'Треки':'Tracks']]){const b=document.createElement('button');b.textContent=label;b.onclick=()=>dialog.querySelector('#'+id).scrollIntoView({behavior:document.documentElement.dataset.motion==='off'?'instant':'smooth',block:'start'});navigation.append(b);}
 dialog.querySelector('.detail-top').after(navigation);
 const rows=[...tracks.querySelectorAll('li')],sides=[...new Set(rows.map(r=>r.querySelector('.track-position').textContent.match(/^[A-Za-z]+/)?.[0]).filter(Boolean))];
 const choices=document.createElement('div');choices.className='track-side-tabs';choices.setAttribute('role','group');choices.setAttribute('aria-label',lang==='uk'?'Сторони платівки':'Record sides');
 for(const side of ['',...sides]){const b=document.createElement('button');b.textContent=side||(lang==='uk'?'Усі':'All');b.setAttribute('aria-pressed',String(!side));b.onclick=()=>{rows.forEach(r=>r.hidden=!!side&&r.querySelector('.track-position').textContent.match(/^[A-Za-z]+/)?.[0]!==side);};choices.append(b);}
 tracks.querySelector('h3').after(choices);
 const sync=()=>{for(const b of choices.children){const side=b.textContent;const all=rows.every(r=>!r.hidden);b.setAttribute('aria-pressed',String(b===choices.firstElementChild?all:!all&&rows.filter(r=>!r.hidden).every(r=>r.querySelector('.track-position').textContent.startsWith(side))));}};
 const trackObserver=new MutationObserver(sync);trackObserver.observe(tracks.querySelector('ol'),{subtree:true,attributes:true,attributeFilter:['hidden']});
 const observer=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting){entry.target.classList.add('insert-visible');observer.unobserve(entry.target);}},{root:dialog,threshold:.05});
 [history,tracks,sources,gallery].forEach(section=>{section.classList.add('insert-awaiting');observer.observe(section);});
 dialog.addEventListener('close',()=>{observer.disconnect();trackObserver.disconnect();},{once:true});
}
