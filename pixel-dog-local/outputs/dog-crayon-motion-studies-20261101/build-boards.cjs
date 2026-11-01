const fs=require('fs'),path=require('path'),crypto=require('crypto');
const sharp=require('C:/Users/verib/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const manifest=JSON.parse(fs.readFileSync(path.join(__dirname,'prompts.json'),'utf8'));
const names=['WALK','LIE','PAW HOVER','STRETCH','SHAKE'];
const tile=360,header=42,rowH=402;
function text(label,w,h,size=20){
 return Buffer.from('<svg width="'+w+'" height="'+h+'"><rect width="100%" height="100%" fill="#fffdf8"/><text x="'+(w/2)+'" y="'+(h-12)+'" text-anchor="middle" font-family="sans-serif" font-size="'+size+'" fill="#51443a">'+label+'</text></svg>');
}
async function board(width,height,layers,filename){
 await sharp({create:{width,height,channels:3,background:'#fffdf8'}}).composite(layers).png().toFile(path.join(__dirname,filename));
}
(async()=>{
 const files=[],all=[],rows={P1:[],P2:[]};
 for(const item of manifest.items){
  const dest=path.join(__dirname,item.output_filename);
  fs.copyFileSync(item.generated_path,dest);
  const raw=fs.readFileSync(dest),meta=await sharp(raw).metadata();
  if(meta.width!==1254||meta.height!==1254)throw Error('Unexpected canvas: '+item.output_filename);
  files.push({file:item.output_filename,base:item.base,action:item.action,width:meta.width,height:meta.height,sha256:crypto.createHash('sha256').update(raw).digest('hex')});
  const col=Number(item.action.slice(0,2))-1,row=item.base==='P1'?0:1;
  const pic=await sharp(raw).resize(tile,tile).png().toBuffer();
  const caption=text(item.base+' / '+(col+1)+' '+names[col],tile,header);
  rows[item.base].push({input:caption,left:col*tile,top:0},{input:pic,left:col*tile,top:header});
  all.push({input:caption,left:col*tile,top:row*rowH},{input:pic,left:col*tile,top:row*rowH+header});
 }
 await board(tile*5,rowH*2,all,'comparison-all.png');
 for(const base of ['P1','P2'])await board(tile*5,rowH,rows[base],base+'-five-actions.png');
 for(let col=0;col<5;col++){
  const pair=[];
  for(let row=0;row<2;row++){
   const item=manifest.items.find(i=>i.base==='P'+(row+1)&&Number(i.action.slice(0,2))===col+1);
   pair.push({input:text(item.base+' / '+names[col],600,44,24),left:row*600,top:0});
   pair.push({input:await sharp(path.join(__dirname,item.output_filename)).resize(600,600).png().toBuffer(),left:row*600,top:44});
  }
  await board(1200,644,pair,'pair-'+manifest.actions[col].id+'.png');
 }
 fs.writeFileSync(path.join(__dirname,'validation.json'),JSON.stringify({as_of:'2026-11-01',expected:10,actual:files.length,files,source_images_modified:false,comparison:{columns:'5 action types',rows:['P1 updated round eyes','P2 updated round eyes'],width:1800,height:804},validation_scope:'file count, dimensions and hashes; visual assessment documented in README; no animated playback validation'},null,2)+'\n','utf8');
 console.log(JSON.stringify({files:files.length,canvas:'1254x1254 each',comparison:'1800x804',eye_reference:'updated round-eye P1/P2'}));
})().catch(e=>{console.error(e);process.exit(1)});
