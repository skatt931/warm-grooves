export const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function filterRecords(records, {query='', genre='all', format='all', sort='collection'}={}) {
  const q = query.trim().normalize('NFKC').toLocaleLowerCase();
  const filtered = records.filter(r => (!q || [r.artist,r.title,r.label,r.country,r.original,...r.genres].join(' ').normalize('NFKC').toLocaleLowerCase().includes(q)) && (genre === 'all' || r.genres.includes(genre)) && (format === 'all' || (format === 'single' ? r.format.includes('7"') : !r.format.includes('7"'))));
  return filtered.sort((a,b) => sort==='artist' ? a.artist.localeCompare(b.artist) : sort==='year' ? (Number(b.original.match(/\d{4}/)?.[0])||0) - (Number(a.original.match(/\d{4}/)?.[0])||0) || a.number-b.number : a.number-b.number);
}
export function nextIndex(index, delta, length) { return length ? (index + delta % length + length) % length : 0; }
export function safeUrl(url) { try {const u=new URL(url); return u.protocol==='https:' ? u.href : '#';} catch {return '#';} }
export function markdown(text) {
  return escapeHtml(text).replace(/\[([^\]]+)\]\((https:\/\/[^\s)]+)\)/g, (_,label,url)=>`<a href="${escapeHtml(safeUrl(url.replaceAll('&amp;','&')))}" target="_blank" rel="noopener noreferrer">${label} ↗</a>`).replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>').split(/\n\n+/).map(p=>`<p>${p.replace(/\n/g,'<br>')}</p>`).join('');
}
