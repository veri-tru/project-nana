const fs=require('fs'),path=require('path'),assert=require('assert');
const sharp=require('C:/Users/verib/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {chromium}=require('C:/Users/verib/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const manifest=JSON.parse(fs.readFileSync(path.join(__dirname,'manifest.json'),'utf8'));
 let preserved=0;const layers=[];
 for(let row=0;row<manifest.scenes.length;row++){
  const s=manifest.scenes[row];
  for(const f of s.frames){
   const a=await sharp(path.join(__dirname,s.id+'-sheet.png')).extract(f.sourceRect).removeAlpha().raw().toBuffer();
   const b=await sharp(path.join(__dirname,f.file)).extract({left:f.pasteOffset.left,top:f.pasteOffset.top,width:f.sourceRect.width,height:f.sourceRect.height}).removeAlpha().raw().toBuffer();
   assert(a.equals(b));preserved++;
  }
  layers.push({input:Buffer.from(`<svg width="1200" height="40"><rect width="1200" height="40" fill="#faf8f3"/><text x="16" y="28" font-size="22" font-family="Arial" fill="#473b32">${s.id} | frames 01 / 04 / 07 / 12</text></svg>`),left:0,top:row*340});
  for(let col=0;col<4;col++)layers.push({input:await sharp(path.join(__dirname,s.frames[[0,3,6,11][col]].file)).resize(300,300).toBuffer(),left:col*300,top:row*340+40});
 }
 await sharp({create:{width:1200,height:1020,channels:3,background:'#faf8f3'}}).composite(layers).png().toFile(path.join(__dirname,'overview.png'));
 const browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1280,height:950}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('file:///'+path.join(__dirname,'index.html').replaceAll('\\','/'));
  const loaded=await page.evaluate(async()=>{const all=[...states.values()].flatMap(s=>s.imgs);await Promise.all(all.map(i=>i.decode()));return all.map(i=>[i.naturalWidth,i.naturalHeight]);});
  assert.equal(loaded.length,36);assert(loaded.every(v=>v[0]===400&&v[1]===400));
  await page.locator('[data-id="B-walk"][data-action="next"]').click();assert((await page.locator('#status-B-walk').textContent()).startsWith('2/12'));assert.equal(errors.length,0);
  await page.screenshot({path:path.join(__dirname,'preview-check.png'),fullPage:true});
  fs.writeFileSync(path.join(__dirname,'preview-check.json'),JSON.stringify({status:'passed',loadedImages:loaded.length,frameStepWorks:true,scriptErrors:errors,preservedSourceRectangles:preserved,pixelMismatch:0,scope:'packaging, image loading and manual step only; animation quality and device acceptance not run'},null,2)+'\n');
  console.log('36 image loads, source pixel preservation and manual stepping passed');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
