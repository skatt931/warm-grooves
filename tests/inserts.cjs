async page=>{
 await page.setViewportSize({width:390,height:844});await page.goto('http://127.0.0.1:4173/#record-12112689');await page.locator('#detail-dialog[open]').waitFor();await page.locator('.transfer-layer').waitFor({state:'detached'});
 if(await page.locator('.album-insert').count()!==4)throw Error('Missing inserts');
 await page.locator('.insert-nav button').last().click();await page.waitForTimeout(900);
 const total=await page.locator('.tracklist li').count();if(await page.locator('.tracklist li:visible').count()!==total)throw Error('Default tracks');
 await page.locator('.track-side-tabs button').nth(1).click();if(await page.locator('.tracklist li:visible').count()>=total)throw Error('Side selection');
 await page.locator('.track-side-tabs button').first().click();
 if(/\p{Extended_Pictographic}/u.test(await page.locator('#detail-dialog').innerText()))throw Error('Emoji remains');
 if(await page.locator('#detail-dialog').evaluate(e=>e.scrollWidth>e.clientWidth))throw Error('Overflow');
 await page.screenshot({path:'output/playwright/inserts-mobile.png'});
 await page.locator('.insert-nav button').first().click();await page.waitForTimeout(800);await page.screenshot({path:'output/playwright/inserts-story.png'});
}
