const fs=require('fs'),path=require('path'),crypto=require('crypto');
const sharp=require('C:/Users/verib/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const spec=JSON.parse(fs.readFileSync(path.join(__dirname,'prompts.json'),'utf8'));
function title(s,w){return Buffer.from('<svg width="'+w+'" height="44"><text x="'+w/2+'" y="31" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#51443a">'+s+'</text></svg>');}
(async()=>{
const rawPath=path.join(__dirname,'P1-walk-generated.png');fs.copyFileSync(spec.generated_final,rawPath);
const {data,info}=await sharp(rawPath).removeAlpha().raw().toBuffer({resolveWithObject:true});
if(info.width!==1254||info.height!==1254)throw Error('Unexpected canvas');
let bottom=-1;for(let y=0;y<1254;y++){let n=0;for(let x=0;x<1254;x++){const j=(y*1254+x)*info.channels;if(data[j]<160&&data[j+1]<140&&data[j+2]<125)n++;}if(n>=4)bottom=y;}
const dy=1104-bottom,finalPath=path.join(__dirname,'P1-walk-v2.png');
const extended=await sharp(rawPath).extend({top:Math.max(0,dy),bottom:Math.max(0,-dy),left:0,right:0,background:'#fffdf8'}).png().toBuffer();
await sharp(extended).extract({left:0,top:Math.max(0,-dy),width:1254,height:1254}).png().toFile(finalPath);
const layers=[],faces=[];
for(const [i,file,label] of [[0,spec.source_absolute,'Original P1'],[1,finalPath,'P1 revised']]){
layers.push({input:title(label,600),left:i*600,top:0},{input:await sharp(file).resize(600,600).png().toBuffer(),left:i*600,top:44});
faces.push({input:title(label,500),left:i*500,top:0},{input:await sharp(file).extract({left:150,top:350,width:310,height:310}).resize(500,500).png().toBuffer(),left:i*500,top:44});
}
await sharp({create:{width:1200,height:644,channels:3,background:'#fffdf8'}}).composite(layers).png().toFile(path.join(__dirname,'comparison.png'));
await sharp({create:{width:1000,height:544,channels:3,background:'#fffdf8'}}).composite(faces).png().toFile(path.join(__dirname,'face-comparison.png'));
const hash=crypto.createHash('sha256').update(fs.readFileSync(finalPath)).digest('hex');
fs.writeFileSync(path.join(__dirname,'review.json'),JSON.stringify({as_of:'2026-11-01',canvas:[1254,1254],file:'P1-walk-v2.png',sha256:hash,ground_y_px:1104,vertical_translation_px:dy,method:'image_gen full style edit with translation-only baseline alignment',fill_density_measured:false,scope:'one walking pose',owner_review:'pending',other_assets_modified:false},null,2)+'\n','utf8');
console.log(JSON.stringify({canvas:[1254,1254],dy,final:'P1-walk-v2.png',comparison:'comparison.png',detail:'face-comparison.png'}));
})().catch(e=>{console.error(e);process.exit(1)});
