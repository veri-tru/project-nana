const fs=require('fs'),path=require('path'),crypto=require('crypto');
const sharp=require('C:/Users/verib/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
(async()=>{
 const names=['P1-with-guidance.png','P2-without-identity-guidance.png','P3-minimal.png'];
 const layers=[],files=[];
 for(let i=0;i<names.length;i++){
  const raw=fs.readFileSync(path.join(__dirname,names[i])),m=await sharp(raw).metadata();
  layers.push({input:await sharp(raw).resize(512,512).png().toBuffer(),left:i*512,top:44});
  layers.push({input:Buffer.from('<svg width="512" height="44"><text x="256" y="31" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#51443a">P'+(i+1)+'</text></svg>'),left:i*512,top:0});
  files.push({file:names[i],width:m.width,height:m.height,sha256:crypto.createHash('sha256').update(raw).digest('hex')});
 }
 await sharp({create:{width:1536,height:556,channels:3,background:'#fffdf8'}}).composite(layers).png().toFile(path.join(__dirname,'comparison.png'));
 fs.writeFileSync(path.join(__dirname,'validation.json'),JSON.stringify({as_of:'2026-11-01',files,comparison:{width:1536,height:556},originals_unchanged:true,owner_review:'pending',replicates_per_condition:1},null,2)+'\n','utf8');
 console.log(JSON.stringify({files,comparison:'comparison.png'}));
})().catch(e=>{console.error(e);process.exit(1)});
