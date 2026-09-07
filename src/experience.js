// Physical interactions use transforms only; no animation framework or remote assets.
export const reduced = () => document.documentElement.dataset.motion === 'off' || matchMedia('(prefers-reduced-motion: reduce)').matches;
const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
let lightingToken=0;
const palettes=new Map();
export async function lightAlbum(src){
 const token=++lightingToken;
 try{
  if(!palettes.has(src)){
   const img=new Image();img.src=/^https?:/.test(src)?src:`${import.meta.env.BASE_URL}${String(src).replace(/^\/+/, '')}`;await img.decode();
   const canvas=document.createElement('canvas');canvas.width=canvas.height=24;
   const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(img,0,0,24,24);
   const pixels=ctx.getImageData(0,0,24,24).data;let r=0,g=0,b=0,total=0;
   for(let i=0;i<pixels.length;i+=4){const max=Math.max(...pixels.slice(i,i+3)),min=Math.min(...pixels.slice(i,i+3));if(max<40||min>220)continue;const weight=1+(max-min)/24;r+=pixels[i]*weight;g+=pixels[i+1]*weight;b+=pixels[i+2]*weight;total+=weight;}
   // A copper component keeps cooler sleeves within the room's warm lighting.
   palettes.set(src,total?[Math.round(r/total*.75+60),Math.round(g/total*.75+33),Math.round(b/total*.75+18)]:[172,117,76]);
  }
  if(token!==lightingToken)return;
  const rgb=palettes.get(src).join(' ');document.documentElement.style.setProperty('--album-light',rgb);palettes.get(src).forEach((value,i)=>document.documentElement.style.setProperty(['--light-r','--light-g','--light-b'][i],String(value)));
  document.documentElement.dataset.lighting=src;
 }catch{/* Existing copper light is the fallback. */}
}
export function wireCrate(stage,onAdvance){
 let drag=null,suppressUntil=0;
 const record=stage.querySelector('.main-record');
 function reset(){record.style.translate='';record.style.rotate='';record.style.setProperty('--bend','0deg');stage.classList.remove('dragging');}
 stage.addEventListener('pointerdown',event=>{
  if(event.button!==0)return;drag={x:event.clientX,y:event.clientY,lastX:event.clientX,time:performance.now(),velocity:0,id:event.pointerId,moved:false};
 });
 stage.addEventListener('pointermove',event=>{
  const rect=stage.getBoundingClientRect();
  if(!reduced()){record.style.setProperty('--tilt-y',`${(event.clientX-rect.x-rect.width/2)/rect.width*12}deg`);record.style.setProperty('--tilt-x',`${-(event.clientY-rect.y-rect.height/2)/rect.height*8}deg`);stage.style.setProperty('--light-x',`${(event.clientX-rect.x)/rect.width*100}%`);}
  if(!drag)return;const dx=event.clientX-drag.x,dy=event.clientY-drag.y;
  if(!drag.moved&&Math.abs(dy)>Math.abs(dx)+12){drag=null;reset();return;}
  if(Math.abs(dx)>7){drag.moved=true;stage.setPointerCapture(event.pointerId);stage.classList.add('dragging');}
  if(drag.moved){const now=performance.now();drag.velocity=(event.clientX-drag.lastX)/Math.max(1,now-drag.time);drag.time=now;drag.lastX=event.clientX;
   record.style.translate=`${dx*.85}px ${Math.abs(dx)*-.08}px`;record.style.rotate=`${clamp(dx/23,-14,14)}deg`;record.style.setProperty('--bend',`${clamp(-dx/18,-12,12)}deg`);
   stage.style.setProperty('--dig',String(clamp(Math.abs(dx)/160,0,1)));
  }
 });
 function finish(event,cancel=false){if(!drag)return;const current=drag;drag=null;const dx=event.clientX-current.x;reset();stage.style.setProperty('--dig','0');if(current.moved)suppressUntil=performance.now()+500;
  if(!cancel&&current.moved&&(Math.abs(dx)>45||Math.abs(current.velocity)>.55)){const steps=Math.abs(current.velocity)>1.8?Math.min(3,1+Math.floor(Math.abs(dx)/220)):1;onAdvance((dx<0?1:-1)*steps);}
 }
 stage.addEventListener('pointerup',event=>finish(event));stage.addEventListener('pointercancel',event=>finish(event,true));
 stage.addEventListener('lostpointercapture',event=>{if(event.target===stage&&drag){drag=null;reset();}});
 stage.addEventListener('pointerleave',()=>{if(!drag){record.style.setProperty('--tilt-x','0deg');record.style.setProperty('--tilt-y','0deg');}});
 stage.addEventListener('click',event=>{if(performance.now()<suppressUntil){event.preventDefault();event.stopPropagation();}},true);
}
export function departingSleeve(stage,direction){
 if(reduced()||!stage)return;
 const original=stage.querySelector('.main-record'),rect=original.getBoundingClientRect();
 const clone=original.cloneNode(true);clone.className='departing-record';clone.setAttribute('aria-hidden','true');clone.inert=true;
 Object.assign(clone.style,{position:'fixed',left:rect.left+'px',top:rect.top+'px',width:rect.width+'px',height:rect.height+'px',zIndex:8,pointerEvents:'none'});document.body.append(clone);
 const a=clone.animate([{opacity:.85,transform:'rotate(-7deg)'},{opacity:0,transform:`translate(${direction>0?-180:180}px,70px) rotate(${direction>0?-28:18}deg) scale(.82)`}],{duration:480,easing:'cubic-bezier(.2,.7,.3,1)'});a.finished.catch(()=>{}).finally(()=>clone.remove());
}
export async function transferRecord(dialog,source,targetSleeve,targetDisc,reverse=false){
 if(reduced()||!source||source.width<1||!targetSleeve||!targetDisc)return;
 const owner=Symbol('transfer');dialog._transferOwner=owner;
 const sleeveRect=targetSleeve.getBoundingClientRect(),discRect=targetDisc.getBoundingClientRect();
 const image=targetSleeve.querySelector('img');if(!image)return;
 const layer=document.createElement('div');layer.className='transfer-layer';layer.setAttribute('aria-hidden','true');layer.inert=true;
 const sleeve=document.createElement('img');sleeve.src=image.src;sleeve.className='transfer-sleeve';
 const disc=targetDisc.cloneNode(true);disc.className='transfer-disc vinyl';
 layer.append(disc,sleeve);dialog.append(layer);dialog.classList.add('transferring');
 const geometry=rect=>({left:rect.left+'px',top:rect.top+'px',width:rect.width+'px',height:rect.height+'px'});
 const lifted={width:source.width,height:source.height,left:source.left+source.width*.55,top:source.top-25};
 const sleeveFrames=[{...geometry(source),transform:'rotate(-7deg)',offset:0},{...geometry(source),transform:'rotate(-3deg)',offset:.35},{...geometry(sleeveRect),transform:'rotate(0deg)',offset:1}];
 const discFrames=[{...geometry(source),transform:'scale(.95) rotate(0deg)',offset:0},{...geometry(lifted),transform:'scale(.95) rotate(25deg)',offset:.38},{...geometry(discRect),transform:'scale(1) rotate(80deg)',offset:1}];
 try{await Promise.all([sleeve.animate(sleeveFrames,{duration:1150,direction:reverse?'reverse':'normal',easing:'cubic-bezier(.3,.05,.2,1)',fill:'both'}).finished,disc.animate(discFrames,{duration:1150,direction:reverse?'reverse':'normal',easing:'cubic-bezier(.3,.05,.2,1)',fill:'both'}).finished]);}
 catch{/* Interrupted transitions leave the real content usable. */}
 finally{layer.remove();if(dialog._transferOwner===owner)dialog.classList.remove('transferring');}
}
export function wireTurntable(dialog,labels){
 const table=dialog.querySelector('.turntable'),disc=table.querySelector('.playing-disc'),arm=table.querySelector('.tonearm');
 const rows=[...dialog.querySelectorAll('.tracklist li')];
 const sides=[...new Set(rows.map(row=>row.querySelector('.track-position').textContent.match(/^[A-Za-z]+/)?.[0]).filter(Boolean))];
 let sideIndex=0;
 const controls=document.createElement('div');controls.className='side-controls';controls.innerHTML=`<button class="flip-record" type="button">${labels.flip}</button><span class="side-indicator" aria-live="polite"></span><button class="all-tracks" type="button">${labels.all}</button>`;dialog.querySelector('.turntable-controls').after(controls);
 const indicator=controls.querySelector('.side-indicator');
 function showSide(){const side=sides[sideIndex]||'A';table.dataset.side=side;indicator.textContent=`${labels.side} ${side}`;disc.dataset.side=side;rows.forEach(row=>{row.hidden=(row.querySelector('.track-position').textContent.match(/^[A-Za-z]+/)?.[0]||side)!==side;});}
 controls.querySelector('.flip-record').disabled=sides.length<2;
 controls.querySelector('.flip-record').onclick=async()=>{const button=controls.querySelector('.flip-record');button.disabled=true;const wasPaused=table.classList.contains('paused');table.classList.add('paused','flipping');
  if(!reduced())await disc.animate([{transform:'perspective(700px) rotateY(0deg)'},{transform:'perspective(700px) translateY(-25px) rotateY(90deg)'},{transform:'perspective(700px) rotateY(180deg)'}],{duration:720,easing:'ease-in-out'}).finished.catch(()=>{});
  sideIndex=(sideIndex+1)%sides.length;showSide();table.classList.remove('flipping');if(!wasPaused)table.classList.remove('paused');button.disabled=false;
 };
 controls.querySelector('.all-tracks').onclick=()=>{rows.forEach(row=>row.hidden=false);};showSide();
 disc.removeAttribute('aria-hidden');disc.setAttribute('role','button');disc.tabIndex=0;disc.setAttribute('aria-label',labels.hold);
 let speedFrame=0;function speedTo(target){cancelAnimationFrame(speedFrame);const spin=disc.getAnimations().find(a=>a.animationName==='spin');if(!spin||reduced())return;const start=spin.playbackRate,time=performance.now();function step(now){const progress=Math.min(1,(now-time)/380);spin.updatePlaybackRate(start+(target-start)*(1-Math.pow(1-progress,3)));if(progress<1)speedFrame=requestAnimationFrame(step);}speedFrame=requestAnimationFrame(step);}
 const brake=()=>{table.classList.add('braking');speedTo(.08);};const release=()=>{table.classList.remove('braking');speedTo(1);};
 disc.addEventListener('pointerdown',event=>{disc.setPointerCapture(event.pointerId);brake();});for(const name of ['pointerup','pointercancel','lostpointercapture'])disc.addEventListener(name,event=>{if(name!=='lostpointercapture'||event.target===disc)release();});
 disc.addEventListener('keydown',event=>{if([' ','Enter'].includes(event.key)){event.preventDefault();brake();}});disc.addEventListener('keyup',release);disc.addEventListener('blur',release);
 arm.setAttribute('role','slider');arm.tabIndex=0;arm.setAttribute('aria-label',labels.arm);arm.setAttribute('aria-valuemin','0');arm.setAttribute('aria-valuemax','35');arm.setAttribute('aria-valuenow','25');
 let drag=null;function angle(value){const v=clamp(value,0,35);arm.style.transform=`rotate(${v}deg)`;arm.style.animation='none';arm.setAttribute('aria-valuenow',String(Math.round(v)));table.classList.toggle('paused',v<8);const button=dialog.querySelector('[data-action="rotation"]');button.textContent=v<8?labels.spin:labels.pause;button.setAttribute('aria-pressed',String(v>=8));}
 arm.addEventListener('pointerdown',event=>{drag={x:event.clientX,angle:Number(arm.getAttribute('aria-valuenow'))};arm.setPointerCapture(event.pointerId);event.preventDefault();});arm.addEventListener('pointermove',event=>{if(drag)angle(drag.angle+(drag.x-event.clientX)/3);});for(const name of ['pointerup','pointercancel','lostpointercapture'])arm.addEventListener(name,event=>{if(name!=='lostpointercapture'||event.target===arm)drag=null;});
 arm.addEventListener('keydown',event=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){event.preventDefault();angle(event.key==='Home'?0:event.key==='End'?25:Number(arm.getAttribute('aria-valuenow'))+(event.key==='ArrowLeft'?-3:3));}});
 return ()=>{table.classList.remove('braking');};
}
export function photoLift(dialog,origin){
 if(reduced())return;
 const image=dialog.querySelector('.full-photo img');if(!image)return;
 const target=image.getBoundingClientRect();if(origin&&origin.width){image.animate([{transform:`translate(${origin.left-target.left}px,${origin.top-target.top}px) scale(${origin.width/target.width}) rotate(-3deg)`,transformOrigin:'top left',opacity:.5},{transform:'none',opacity:1}],{duration:600,easing:'cubic-bezier(.2,.8,.2,1)'});}
 else image.animate([{transform:'translateX(55px) rotate(2deg)',opacity:.2},{transform:'none',opacity:1}],{duration:450,easing:'ease-out'});
}
let roomTimer;
export function wakeRoom(){document.body.classList.remove('room-idle');clearTimeout(roomTimer);if(document.body.classList.contains('record-room'))roomTimer=setTimeout(()=>{if(!document.querySelector('dialog[open]')&&!document.querySelector(':focus-visible'))document.body.classList.add('room-idle');},2600);}
export async function toggleRoom(force){
 const active=force??!document.body.classList.contains('record-room');document.body.classList.toggle('record-room',active);document.body.classList.remove('room-idle');
 document.querySelector('[data-action="room"]')?.setAttribute('aria-pressed',String(active));document.querySelector('.room-exit').hidden=!active;
 if(active){window.scrollTo({top:0});try{await document.documentElement.requestFullscreen?.();}catch{/* Immersive layout remains available without Fullscreen API. */}wakeRoom();}
 else{clearTimeout(roomTimer);if(document.fullscreenElement)await document.exitFullscreen().catch(()=>{});}
}
for(const event of ['pointermove','pointerdown','keydown','focusin'])document.addEventListener(event,wakeRoom,{passive:true});
document.addEventListener('fullscreenchange',()=>{if(!document.fullscreenElement&&document.body.classList.contains('record-room')){document.body.classList.remove('record-room','room-idle');const exit=document.querySelector('.room-exit');if(exit)exit.hidden=true;document.querySelector('[data-action="room"]')?.setAttribute('aria-pressed','false');}});
