async page => {
 await page.setViewportSize({width:390,height:844});
 await page.goto('http://127.0.0.1:4173/#record-12112689');
 await page.locator('#detail-dialog[open]').waitFor();
 await page.locator('.transfer-layer').waitFor({state:'detached'});
 const total=await page.locator('.tracklist li').count();
 if(await page.locator('.tracklist li:visible').count()!==total)throw Error('Default tracks hidden');
 await page.locator('.flip-record').click();
 await page.waitForFunction(()=>!document.querySelector('.flip-record').disabled);
 if(await page.locator('.tracklist li:visible').count()>=total)throw Error('Side filter ineffective');
 await page.locator('.all-tracks').click();
 if(await page.locator('.tracklist li:visible').count()!==total)throw Error('All tracks not restored');
 await page.locator('.archive-strip').scrollIntoViewIfNeeded();
 await page.locator('.archive-strip img').evaluateAll(imgs=>Promise.all(imgs.map(i=>i.decode())));
 if(/[↗⛶🔗↕]/u.test(await page.locator('#detail-dialog').innerText()))throw Error('Unwanted UI symbols');
 await page.screenshot({path:'output/playwright/archive-preview-fixed.png'});
 console.log('PASS archive previews load, all tracks default, side filtering, no unwanted link symbols');
}
