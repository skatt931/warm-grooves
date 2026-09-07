async page=>{
 for(const width of [320,390,430]){
 await page.setViewportSize({width,height:844});await page.goto('http://127.0.0.1:5173/');await page.locator('[data-action="room"]').click();
 for(let i=0;i<4;i++){
 await page.waitForTimeout(1500);
 const delta=await page.locator('.main-record').evaluate(el=>{const a=el.getBoundingClientRect(),b=el.parentElement.getBoundingClientRect();return {x:Math.abs(a.x+a.width/2-b.x-b.width/2),y:Math.abs(a.y+a.height/2-b.y-b.height/2)}});
 if(delta.x>2||delta.y>2)throw Error('Room off-center '+JSON.stringify({width,i,...delta}));
 await page.keyboard.press('ArrowRight');
 }
 await page.screenshot({path:`output/playwright/room-centered-${width}.png`});await page.locator('.room-exit').click();
 }
}
