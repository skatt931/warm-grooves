async (page) => {
 const assert=(condition,message)=>{if(!condition)throw new Error(message);};
 await page.goto('http://127.0.0.1:4173/');
 await page.getByRole('heading',{name:'I Robot',exact:true}).waitFor();
 await page.evaluate(()=>navigator.serviceWorker.ready);
 await page.waitForFunction(()=>!!navigator.serviceWorker.controller);
 const cacheCount=await page.evaluate(async()=>{const name=(await caches.keys()).find(n=>n.startsWith('warm-grooves-'));return(await(await caches.open(name)).keys()).length;});
 assert(cacheCount>=388,'Whole collection is precached');
 await page.context().setOffline(true);
 try{
  await page.reload();await page.getByRole('heading',{name:'I Robot',exact:true}).waitFor();
  await page.getByRole('button',{name:'ENG',exact:true}).click();
  await page.getByRole('button',{name:'All records',exact:true}).click();
  assert(await page.locator('.grid-record').count()===58,'58 records offline');
  await page.locator('.grid-record').last().click();
  assert(await page.locator('.unpacking-sleeve img').evaluate(img=>img.complete&&img.naturalWidth>0),'Unvisited cover available offline');
  assert(await page.locator('.tracklist li').count()>0,'Unvisited tracks offline');
  await page.locator('#gallery-content [data-action="photo-next"]').click();
  await page.locator('.gallery-image img').evaluate(img=>img.decode());
  assert(await page.locator('.gallery-image img').evaluate(img=>img.complete&&img.naturalWidth>0),'Unvisited gallery photo offline');
  await page.screenshot({path:'output/playwright/offline-production.png'});
  await page.keyboard.press('Escape');await page.locator('#detail-dialog').waitFor({state:'hidden'});
  await page.getByRole('button',{name:'Back to the collection',exact:true}).click();
  await page.setViewportSize({width:390,height:844});
  const cdp=await page.context().newCDPSession(page);
  await cdp.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1});
  await page.locator('.record-stage').scrollIntoViewIfNeeded();
  const rect=await page.locator('.record-stage').boundingBox();
  const before=await page.locator('.record-title h2').textContent();
  const x=rect.x+rect.width*.7,y=rect.y+rect.height*.5;
  await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
  await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x-110,y}]});
  await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  assert(await page.locator('.record-title h2').textContent()!==before,'Touch swipe changes record');
  assert(!await page.locator('#detail-dialog').isVisible(),'Swipe does not accidentally open release');
  await page.emulateMedia({reducedMotion:'reduce'});
  const animation=await page.locator('.main-record').evaluate(el=>getComputedStyle(el).animationDuration);
  assert(parseFloat(animation)<=0.001,'Reduced motion honoured: '+animation);
  console.log('PASS: production service worker, full offline reload, unvisited cover/tracklist, touch swipe, reduced motion. Cached assets: '+cacheCount);
 }finally{await page.context().setOffline(false);}
}
