const fs=require('fs'),path=require('path'),crypto=require('crypto');
const sharp=require('C:/Users/verib/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const cases=[
 {id:'P1',source:'../dog-crayon-prompt-comparison-20261101/P1-with-guidance.png',generated:'C:/Users/verib/.codex/generated_images/01a1481a-ccb4-7c01-ab9d-59788a0b4db4/exec-36392edb-1725-4391-8fc1-07e7c6319587.png',eyes:[{from:[407.5,405],side:76,to:[407,402]},{from:[553.5,431.5],side:78,to:[553,430]}]},
 {id:'P2',source:'../dog-crayon-prompt-comparison-20261101/P2-without-identity-guidance.png',generated:'C:/Users/verib/.codex/generated_images/01a1481a-ccb4-7c01-ab9d-59788a0b4db4/exec-07c8e12b-5dd2-4fb1-b5cd-4c066b78cd6c.png',eyes:[{from:[422.5,384],side:84,to:[420,378]},{from:[570,410.5],side:86,to:[573,408]}]}
];
(async()=>{
const review=[],board=[];
for(let i=0;i<cases.length;i++){
 const c=cases[i],source=path.join(__dirname,c.source),layers=[],regions=[];
 fs.copyFileSync(c.generated,path.join(__dirname,c.id+'-imagegen-edit.png'));
 for(const e of c.eyes){
  const crop={left:Math.round(e.from[0]-e.side/2),top:Math.round(e.from[1]-e.side/2),width:e.side,height:e.side};
  const {data,info}=await sharp(c.generated).extract(crop).resize(64,64).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  for(let y=0;y<64;y++)for(let x=0;x<64;x++){const r=Math.hypot(x-31.5,y-31.5),a=Math.max(0,Math.min(1,(32-r)/4));data[(y*64+x)*4+3]=Math.round(255*a);}
  const region={left:e.to[0]-32,top:e.to[1]-32,width:64,height:64};regions.push(region);
  layers.push({input:await sharp(data,{raw:{width:info.width,height:info.height,channels:4}}).png().toBuffer(),left:region.left,top:region.top});
 }
 const file=c.id+'-round-eyes.png',dest=path.join(__dirname,file);
 await sharp(source).composite(layers).png().toFile(dest);
 const a=await sharp(source).ensureAlpha().raw().toBuffer({resolveWithObject:true});
 const b=await sharp(dest).ensureAlpha().raw().toBuffer({resolveWithObject:true});
 let changedInside=0,changedOutside=0;
 for(let y=0;y<a.info.height;y++)for(let x=0;x<a.info.width;x++){
  const k=(y*a.info.width+x)*4;
  if(a.data[k]===b.data[k]&&a.data[k+1]===b.data[k+1]&&a.data[k+2]===b.data[k+2]&&a.data[k+3]===b.data[k+3])continue;
  if(regions.some(r=>x>=r.left&&x<r.left+r.width&&y>=r.top&&y<r.top+r.height))changedInside++;else changedOutside++;
 }
 if(changedOutside)throw Error('Unexpected modification outside eyes');
 review.push({id:c.id,file,width:a.info.width,height:a.info.height,eye_regions:regions,eye_diameter_px_approx:32,changed_inside_regions:changedInside,changed_outside_regions:changedOutside,sha256:crypto.createHash('sha256').update(fs.readFileSync(dest)).digest('hex')});
 board.push({input:await sharp(dest).resize(600,600).png().toBuffer(),left:i*600,top:44});
 board.push({input:Buffer.from('<svg width="600" height="44"><text x="300" y="31" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#51443a">'+c.id+'</text></svg>'),left:i*600,top:0});
}
await sharp({create:{width:1200,height:644,channels:3,background:'#fffdf8'}}).composite(board).png().toFile(path.join(__dirname,'comparison.png'));
fs.writeFileSync(path.join(__dirname,'validation.json'),JSON.stringify({as_of:'2026-11-01',review,method:'Built-in image_gen eye edits; only local generated eye patches scaled to a common size and blended into originals. No hand-drawn replacement eyes.',excluded:'P3 per user feedback',owner_review:'pending'},null,2)+'\n','utf8');
console.log(JSON.stringify(review));
})().catch(e=>{console.error(e);process.exit(1)});
