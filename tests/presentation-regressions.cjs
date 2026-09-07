async page=>{
 const assert=(value,message)=>{if(!value)throw Error(message);};
 await page.setViewportSize({width:1600,height:1200});
 await page.goto('http://127.0.0.1:5173/');
 await page.locator('.front-sleeve').waitFor();
 const desktop=await page.evaluate(()=>{const box=s=>document.querySelector(s).getBoundingClientRect();const record=box('.main-record'),caption=box('.record-caption');return {recordBottom:record.bottom,captionTop:caption.top};});
 assert(desktop.recordBottom<=desktop.captionTop,'Desktop sleeve overlaps caption');
 await page.locator('[data-action="room"]').click();
 const room=page.locator('.room-exit');assert(await room.isVisible(),'Room exit is visible');
 const roomBox=await room.boundingBox();assert(Math.abs((roomBox.y+roomBox.height/2)-42)<3,'Room exit control is vertically misaligned');
 const toolsBox=await page.locator('.view-tools').boundingBox();assert(roomBox.x>=toolsBox.x+toolsBox.width,'Room exit overlaps room controls');
 await room.click();
 await page.setViewportSize({width:390,height:844});
 await page.goto('http://127.0.0.1:5173/#record-12112689');
 await page.locator('#detail-dialog[open]').waitFor();await page.locator('.gallery-image').click();
 const photo=page.locator('#photo-dialog .full-photo');await photo.waitFor();
 const initial=await page.locator('#photo-dialog .gallery-navigation span').innerText();
 await photo.dispatchEvent('pointerdown',{pointerId:41,pointerType:'touch',clientX:300,clientY:300});
 await photo.dispatchEvent('pointermove',{pointerId:41,pointerType:'touch',clientX:100,clientY:294});
 await photo.dispatchEvent('pointerup',{pointerId:41,pointerType:'touch',clientX:100,clientY:294});
 await page.waitForTimeout(150);const after=await page.locator('#photo-dialog .gallery-navigation span').innerText();
 assert(initial!==after,'A single swipe did not change image');
 const next=await page.locator('#photo-dialog .gallery-navigation span').innerText();await page.waitForTimeout(250);assert(await page.locator('#photo-dialog .gallery-navigation span').innerText()===next,'Swipe changed more than one image');
 await photo.click();assert(await page.locator('#photo-dialog').evaluate(el=>el.classList.contains('photo-minimal')),'Image-only view did not open');
 const background=await page.locator('#photo-dialog').evaluate(el=>getComputedStyle(el).backgroundColor);assert(background!=='rgb(13, 14, 11)','Image-only view darkened background');
 console.log('PASS desktop sleeve/caption and room control; mobile single-swipe and calm tilt viewer');
}
