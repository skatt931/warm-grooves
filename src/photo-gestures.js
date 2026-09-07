export function wirePhotoViewer(element,onSwipe){
 let gesture=null;
 element.onpointerdown=event=>{
  gesture={id:event.pointerId,x:event.clientX,y:event.clientY,moved:false};
  element.setPointerCapture?.(event.pointerId);
 };
 element.onpointermove=event=>{
  if(!gesture||event.pointerId!==gesture.id)return;
  const dx=event.clientX-gesture.x,dy=event.clientY-gesture.y;
  gesture.moved||=Math.hypot(dx,dy)>8;
  const image=element.querySelector('img');
  if(image){image.style.setProperty('--photo-tilt-x',`${Math.max(-7,Math.min(7,-dy/20))}deg`);image.style.setProperty('--photo-tilt-y',`${Math.max(-9,Math.min(9,dx/18))}deg`);}
 };
 const finish=event=>{
  if(!gesture||event.pointerId!==gesture.id)return;
  const dx=event.clientX-gesture.x,dy=event.clientY-gesture.y,swipe=Math.abs(dx)>54&&Math.abs(dx)>Math.abs(dy)*1.35;
  const image=element.querySelector('img');
  image?.style.setProperty('--photo-tilt-x','0deg');image?.style.setProperty('--photo-tilt-y','0deg');
  gesture=null;
  if(swipe){event.preventDefault();onSwipe(dx<0?1:-1);}
 };
 element.onpointerup=finish;element.onpointercancel=finish;
}
