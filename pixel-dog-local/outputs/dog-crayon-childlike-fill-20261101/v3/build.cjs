const fs=require('fs'),path=require('path'),crypto=require('crypto');
const sharp=require('C:/Users/verib/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const spec=JSON.parse(fs.readFileSync(path.join(__dirname,'prompts.json'),'utf8'));
const regions=[{label:'eye-near',left:222,top:398,width:46,height:48},{label:'eye-far',left:347,top:425,width:49,height:49},{label:'nose',left:240,top:478,width:82,height:67},{label:'tongue-mouth',left:240,top:546,width:85,height:66}];
(async()=>{
fs.copyFileSync(spec.generated_path,path.join(__dirname,'imagegen-face-edit.png'));
const m=await sharp(spec.generated_path).metadata();if(m.width!==1254||m.height!==1254)throw Error('Wrong canvas');
const layers=[];
for(const r of regions){
const {data,info}=await sharp(spec.generated_path).extract({left:r.left,top:r.top,width:r.width,height:r.height}).ensureAlpha().raw().toBuffer({resolveWithObject:true});
for(let y=0;y<r.height;y++)for(let x=0;x<r.width;x++){const d=Math.min(x,y,r.width-1-x,r.height-1-y);data[(y*r.width+x)*4+3]=Math.round(255*Math.min(1,d/4));}
layers.push({input:await sharp(data,{raw:{width:info.width,height:info.height,channels:4}}).png().toBuffer(),left:r.left,top:r.top});
}
const final=path.join(__dirname,'P1-walk-v3.png');await sharp(spec.source_absolute).composite(layers).png().toFile(final);
const a=await sharp(spec.source_absolute).ensureAlpha().raw().toBuffer(),b=await sharp(final).ensureAlpha().raw().toBuffer();
let outside=0,inside=0;
for(let y=0;y<1254;y++)for(let x=0;x<1254;x++){const j=(y*1254+x)*4;if([0,1,2,3].every(c=>a[j+c]===b[j+c]))continue;if(regions.some(r=>x>=r.left&&x<r.left+r.width&&y>=r.top&&y<r.top+r.height))inside++;else outside++;}
if(outside)throw Error('Unexpected changes beyond face regions');
const layersFace=[];
for(const [i,file,label] of [[0,spec.source_absolute,'Before'],[1,final,'Revised']]){
layersFace.push({input:Buffer.from('<svg width="500" height="44"><text x="250" y="31" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#51443a">'+label+'</text></svg>'),left:i*500,top:0},{input:await sharp(file).extract({left:150,top:350,width:310,height:310}).resize(500,500).png().toBuffer(),left:i*500,top:44});
}
await sharp({create:{width:1000,height:544,channels:3,background:'#fffdf8'}}).composite(layersFace).png().toFile(path.join(__dirname,'face-comparison.png'));
fs.writeFileSync(path.join(__dirname,'review.json'),JSON.stringify({as_of:'2026-11-01',file:'P1-walk-v3.png',canvas:[1254,1254],regions,changed_inside_regions:inside,changed_outside_regions:outside,sha256:crypto.createHash('sha256').update(fs.readFileSync(final)).digest('hex'),visual_check:'Nose central open voids filled; minor irregular pigment remains. No automatic symmetry measurement.',owner_review:'pending',other_poses_modified:false},null,2)+'\n','utf8');
console.log(JSON.stringify({inside,outside,final:'P1-walk-v3.png'}));
})().catch(e=>{console.error(e);process.exit(1)});
