const fs=require('fs'),path=require('path'),crypto=require('crypto');
const sharp=require('C:/Users/verib/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const spec=JSON.parse(fs.readFileSync(path.join(__dirname,'prompts.json'),'utf8'));
const names=['WALK','LIE','PAW HOVER','STRETCH','SHAKE'];
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
async function bounds(file){
 const {data,info}=await sharp(file).removeAlpha().raw().toBuffer({resolveWithObject:true});
 let minX=info.width,maxX=-1,minY=info.height,maxY=-1;
 for(let y=0;y<info.height;y++){
  let count=0;
  for(let x=0;x<info.width;x++){
   const j=(y*info.width+x)*info.channels;
   if(data[j]<160&&data[j+1]<140&&data[j+2]<125){count++;minX=Math.min(minX,x);maxX=Math.max(maxX,x);}
  }
  if(count>=4){minY=Math.min(minY,y);maxY=y;}
 }
 return {minX,maxX,minY,maxY,width:info.width,height:info.height};
}
function caption(s,w=360,h=42){
 return Buffer.from('<svg width="'+w+'" height="'+h+'"><rect width="100%" height="100%" fill="#fffdf8"/><text x="'+w/2+'" y="'+(h-12)+'" text-anchor="middle" font-family="sans-serif" font-size="20" fill="#51443a">'+s+'</text></svg>');
}
async function board(w,h,layers,name){
 await sharp({create:{width:w,height:h,channels:3,background:'#fffdf8'}}).composite(layers).png().toFile(path.join(__dirname,name));
}
(async()=>{
 const rows=[],p1row=[],p2row=[],validation=[],guides=[];
 for(let i=0;i<spec.items.length;i++){
  const item=spec.items[i],rawName='P1-'+item.action+'-generated.png',rawPath=path.join(__dirname,rawName);
  fs.copyFileSync(item.generated_path,rawPath);
  const b=await bounds(rawPath);if(b.width!==1254||b.height!==1254)throw Error('Unexpected source size');
  const dy=1104-b.maxY;
  if(b.minY+dy<20||b.maxY+dy>=1254)throw Error('Would crop artwork');
  const final='P1-'+item.action+'.png',finalPath=path.join(__dirname,final);
  const extended=await sharp(rawPath).extend({top:Math.max(0,dy),bottom:Math.max(0,-dy),left:0,right:0,background:'#fffdf8'}).png().toBuffer();
  await sharp(extended).extract({left:0,top:Math.max(0,-dy),width:1254,height:1254}).png().toFile(finalPath);
  const after=await bounds(finalPath);if(after.maxY!==1104)throw Error('Ground alignment failed');
  const beforeRaw=await sharp(rawPath).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  const afterRaw=await sharp(finalPath).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  let mismatches=0;
  for(let y=b.minY;y<=b.maxY;y++)for(let x=0;x<1254;x++)for(let c=0;c<4;c++)if(beforeRaw.data[(y*1254+x)*4+c]!==afterRaw.data[((y+dy)*1254+x)*4+c])mismatches++;
  if(mismatches)throw Error('Artwork altered beyond translation');
  const p2source=path.join(__dirname,'../dog-crayon-motion-studies-20261101/P2-'+item.action+'.png'),p2name='P2-'+item.action+'.png',p2path=path.join(__dirname,p2name);
  fs.copyFileSync(p2source,p2path);
  const p2same=digest(fs.readFileSync(p2source))===digest(fs.readFileSync(p2path));if(!p2same)throw Error('P2 changed');
  validation.push({action:item.action,p1:{file:final,raw_generated:rawName,canvas:[1254,1254],vertical_translation_px:dy,ground_y_px:1104,ground_detection:'last row with >=4 dark foreground pixels; visual contact proxy, not skeletal measurement',source_bounds:b,aligned_bounds:after,translated_artwork_mismatches:0,sha256:digest(fs.readFileSync(finalPath))},p2:{file:p2name,unchanged_from_previous:true,sha256:digest(fs.readFileSync(p2path))}});
  const p1tile=await sharp(finalPath).resize(360,360).png().toBuffer(),p2tile=await sharp(p2path).resize(360,360).png().toBuffer();
  p1row.push({input:caption('P1 / '+(i+1)+' '+names[i]),left:i*360,top:0},{input:p1tile,left:i*360,top:42});
  p2row.push({input:caption('P2 / '+(i+1)+' '+names[i]),left:i*360,top:0},{input:p2tile,left:i*360,top:42});
  rows.push({input:caption('P1 / '+(i+1)+' '+names[i]),left:i*360,top:0},{input:p1tile,left:i*360,top:42},{input:caption('P2 / '+(i+1)+' '+names[i]),left:i*360,top:402},{input:p2tile,left:i*360,top:444});
  const nearLineY=42+1104*360/1254;
  guides.push({input:Buffer.from('<svg width="360" height="402"><line x1="0" y1="'+nearLineY+'" x2="360" y2="'+nearLineY+'" stroke="#b35555" stroke-width="1" stroke-dasharray="4 4"/></svg>'),left:i*360,top:0});
  const pair=[{input:caption('P1 / '+names[i],600,44),left:0,top:0},{input:await sharp(finalPath).resize(600,600).png().toBuffer(),left:0,top:44},{input:caption('P2 / '+names[i],600,44),left:600,top:0},{input:await sharp(p2path).resize(600,600).png().toBuffer(),left:600,top:44}];
  await board(1200,644,pair,'pair-'+item.action+'.png');
 }
 await board(1800,804,rows,'comparison-all.png');
 await board(1800,402,p1row,'P1-five-actions.png');
 await board(1800,402,p2row,'P2-five-actions.png');
 await board(1800,402,[...p1row,...guides],'P1-ground-review.png');
 fs.writeFileSync(path.join(__dirname,'validation.json'),JSON.stringify({as_of:'2026-11-01',validation,canvas_origin:[0,0],body_root_anchor:null,frame_timing:null,clip_id:null,review_status:'static_candidates_owner_review_pending',limits:['Dark silhouette baseline is a contact proxy; individual foot contacts remain visual checks.','No skeleton registration or measured body-ratio invariance.','No 8fps playback, transitions or timing validation.']},null,2)+'\n','utf8');
 console.log(JSON.stringify(validation.map(v=>({action:v.action,dy:v.p1.vertical_translation_px,ground:v.p1.ground_y_px,pixels_mismatched:v.p1.translated_artwork_mismatches,p2_unchanged:v.p2.unchanged_from_previous}))));
})().catch(e=>{console.error(e);process.exit(1)});
