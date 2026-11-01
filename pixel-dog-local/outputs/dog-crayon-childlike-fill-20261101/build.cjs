const fs=require('fs'),path=require('path'),crypto=require('crypto');
const sharp=require('C:/Users/verib/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const spec=JSON.parse(fs.readFileSync(path.join(__dirname,'prompts.json'),'utf8'));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 fs.copyFileSync(spec.generated_intermediate,path.join(__dirname,'intermediate.png'));
 const rawPath=path.join(__dirname,'P1-walk-generated.png');
 fs.copyFileSync(spec.generated_final,rawPath);
 const {data,info}=await sharp(rawPath).removeAlpha().raw().toBuffer({resolveWithObject:true});
 if(info.width!==1254||info.height!==1254)throw Error('Unexpected canvas');
 let top=1254,bottom=-1;
 for(let y=0;y<1254;y++){let n=0;for(let x=0;x<1254;x++){let j=(y*1254+x)*info.channels;if(data[j]<160&&data[j+1]<140&&data[j+2]<125)n++;}if(n>=4){top=Math.min(top,y);bottom=y;}}
 const dy=1104-bottom;if(top+dy<0)throw Error('Cropping subject');
 const extended=await sharp(rawPath).extend({top:Math.max(0,dy),bottom:Math.max(0,-dy),left:0,right:0,background:'#fffdf8'}).png().toBuffer();
 const finalPath=path.join(__dirname,'P1-walk-childlike.png');
 await sharp(extended).extract({left:0,top:Math.max(0,-dy),width:1254,height:1254}).png().toFile(finalPath);
 const beforePath=path.join(__dirname,spec.source),layers=[];
 for(const [i,file,title] of [[0,beforePath,'Before'],[1,finalPath,'P1 revised']]){
  layers.push({input:Buffer.from('<svg width="600" height="44"><text x="300" y="31" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#51443a">'+title+'</text></svg>'),left:i*600,top:0});
  layers.push({input:await sharp(file).resize(600,600).png().toBuffer(),left:i*600,top:44});
 }
 await sharp({create:{width:1200,height:644,channels:3,background:'#fffdf8'}}).composite(layers).png().toFile(path.join(__dirname,'comparison.png'));
 fs.writeFileSync(path.join(__dirname,'review.json'),JSON.stringify({
 as_of:'2026-11-01',file:'P1-walk-childlike.png',canvas:[1254,1254],ground_y_px:1104,vertical_translation_px:dy,
 source_sha256:hash(fs.readFileSync(beforePath)),final_sha256:hash(fs.readFileSync(finalPath)),
 visual_observations:['Less filled gray regions with broad paper gaps','Fewer interior fur lines and simpler outline','Small round dot eyes and low tail remain','Gray/white palette remains the intended basis'],
 limitations:['Whole style edit; contours and markings are not pixel-identical','Fill coverage not numerically measured','Incomplete filling can weaken marking visibility; owner likeness review pending','Only one walking example; other actions and P2 unchanged','No animated frame continuity validation'],
 owner_review:'pending',other_assets_modified:false
 },null,2)+'\n','utf8');
 console.log(JSON.stringify({canvas:[1254,1254],baseline:1104,dy,comparison:'comparison.png'}));
})().catch(e=>{console.error(e);process.exit(1)});
