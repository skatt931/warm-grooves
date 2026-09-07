async page => {
 let previous;
 for(let i=0;i<8;i++){
  await page.goto('http://127.0.0.1:5173/');
  await page.locator('.front-sleeve').waitFor();
  const id=await page.locator('.front-sleeve').getAttribute('data-record');
  if(id===previous)throw Error('Consecutive launches repeated the same record');
  previous=id;
 }
 await page.goto('http://127.0.0.1:5173/#record-12112689');
 await page.locator('#detail-dialog[open]').waitFor();
 if(await page.locator('#detail-title').textContent()!=='Yeni Bir Gün')throw Error('Deep link changed');
 console.log('PASS: eight launches without consecutive repeats; album deep link preserved');
}
