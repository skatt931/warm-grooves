async page => {
 for(const width of [320,390,430]){
 await page.setViewportSize({width,height:844});await page.goto('http://127.0.0.1:5173/');
 await page.locator('.search-toggle').click();
 const controls=page.locator('#filter-panel input,#filter-panel select,#filter-panel button');
 const boxes=await controls.evaluateAll(es=>es.map(e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom}}));
 for(const b of boxes)if(b.x<0||b.right>width)throw Error('Search overflow '+width);
 for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){const a=boxes[i],b=boxes[j];if(Math.min(a.right,b.right)>Math.max(a.x,b.x)&&Math.min(a.bottom,b.bottom)>Math.max(a.y,b.y))throw Error('Controls overlap');}
 await page.locator('#search').fill('Pink Floyd');await page.waitForFunction(()=>document.querySelector('.record-title p')?.textContent==='Pink Floyd');
 await page.locator('#filter-panel [data-action="search"]').click();
 const room=page.locator('[data-action="room"]');if(!await room.innerText()||await room.locator('svg').count()!==1)throw Error('Missing room control');
 await room.click();await page.waitForTimeout(800);
 const box=await page.locator('.front-sleeve').boundingBox();if(box.x<0||box.x+box.width>width+5)throw Error('Room sleeve outside viewport '+JSON.stringify(box));
 await page.screenshot({path:`output/playwright/mobile-room-${width}.png`});await page.locator('.room-exit').click();
 await page.locator('.search-toggle').click();await page.screenshot({path:`output/playwright/mobile-search-${width}.png`});
 }
 console.log('PASS mobile search layout, filtering, visible room control and room bounds at 320/390/430px');
}
