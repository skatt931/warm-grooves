import {spawnSync} from 'node:child_process';
import {mkdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
for(const port of [5173,4173]){
 try{const response=await fetch(`http://127.0.0.1:${port}/`,{signal:AbortSignal.timeout(3000)});if(!response.ok)throw Error('HTTP '+response.status);}
 catch{console.error(`Start ${port===5173?'npm run dev':'npm run preview'} in another terminal before running browser checks.`);process.exit(1);}
}
mkdirSync('output/playwright',{recursive:true});
const cli=resolve('node_modules/.bin/playwright-cli');
const session=`vinyl-check-${Date.now()}`;
function run(args,name){
 const result=spawnSync(cli,[`-s=${session}`,...args],{encoding:'utf8',timeout:180000});
 const output=(result.stdout||'')+(result.stderr||'');
 writeFileSync(`output/playwright/${name}.log`,output);
 if(result.status!==0||output.includes('### Error'))throw Error(`${name} failed. See output/playwright/${name}.log\n${output.slice(-1800)}`);
 console.log(`PASS ${name}`);
}
try{
 run(['open','http://127.0.0.1:5173/'],'browser-open');
 run(['run-code','--filename','tests/browser-checks.cjs'],'browser-regression');
 run(['run-code','--filename','tests/gallery-checks.cjs'],'gallery-regression');
 run(['run-code','--filename','tests/mobile-search-room.cjs'],'mobile-search-room');
 run(['run-code','--filename','tests/experience-checks.cjs'],'physical-experience');
 run(['run-code','--filename','tests/presentation-regressions.cjs'],'presentation-regressions');
 run(['run-code','--filename','tests/offline-checks.cjs'],'offline-and-touch');
 console.log('All browser checks passed. Screenshots and logs: output/playwright/');
}catch(error){console.error(error.message);process.exitCode=1;}
finally{spawnSync(cli,[`-s=${session}`,'close'],{encoding:'utf8',timeout:15000});}
