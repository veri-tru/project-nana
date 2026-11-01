const fs=require('fs'),path=require('path'),crypto=require('crypto');
const sharp=require('C:/Users/verib/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const spec=JSON.parse(fs.readFileSync(path.join(__dirname,'prompts.json'),'utf8'));
const protect=JSON.parse(fs.readFileSync(spec.face_region_ref,'utf8')).regions;
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function protectedPixel(x,y){return protect.some(r=>x>=r.left-4&&x<r.left+r.width+4&&y>=r.top-4&&y<r.top+r.height+4);}
(async()=>{
const source=await sharp(spec.source).ensureAlpha().raw().toBuffer({resolveWithObject:true});
const {width:w,height:h}=source.info;if(w!==1254||h!==1254)throw Error('Wrong canvas');
const dist=new Uint16Array(w*h);dist.fill(60000);
for(let y=0;y<h;y++)for(let x=0;x<w;x++){const p=y*w+x,k=p*4,r=source.data[k],g=source.data[k+1],b=source.data[k+2];if(r<150&&g<90&&b<70&&r-g>23&&g-b>12&&!protectedPixel(x,y))dist[p]=0;}
for(let y=0;y<h;y++)for(let x=0;x<w;x++){const p=y*w+x;let d=dist[p];if(x)d=Math.min(d,dist[p-1]+1);if(y)d=Math.min(d,dist[p-w]+1);if(x&&y)d=Math.min(d,dist[p-w-1]+1);if(y&&x<w-1)d=Math.min(d,dist[p-w+1]+1);dist[p]=d;}
for(let y=h-1;y>=0;y--)for(let x=w-1;x>=0;x--){const p=y*w+x;let d=dist[p];if(x<w-1)d=Math.min(d,dist[p+1]+1);if(y<h-1)d=Math.min(d,dist[p+w]+1);if(y<h-1&&x<w-1)d=Math.min(d,dist[p+w+1]+1);if(y<h-1&&x)d=Math.min(d,dist[p+w-1]+1);dist[p]=d;}
const alpha=new Uint8Array(w*h);
for(let y=0;y<h;y++)for(let x=0;x<w;x++){const p=y*w+x;alpha[p]=protectedPixel(x,y)?0:Math.round(255*Math.max(0,Math.min(1,(12-dist[p])/6)));}
const review=[];
for(const item of spec.items){
fs.copyFileSync(item.generated_path,path.join(__dirname,item.id+'-imagegen.png'));
const edit=await sharp(item.generated_path).ensureAlpha().raw().toBuffer({resolveWithObject:true});
if(edit.info.width!==w||edit.info.height!==h)throw Error('Edit canvas mismatch');
for(let p=0;p<w*h;p++)edit.data[p*4+3]=alpha[p];
const overlay=await sharp(edit.data,{raw:{width:w,height:h,channels:4}}).png().toBuffer();
const filename=item.id+(item.id==='A'?'-weak.png':'-strong.png'),dest=path.join(__dirname,filename);
await sharp(spec.source).composite([{input:overlay,left:0,top:0}]).png().toFile(dest);
const final=await sharp(dest).ensureAlpha().raw().toBuffer();
let changed=0,outside=0,face=0;
for(let y=0;y<h;y++)for(let x=0;x<w;x++){const p=y*w+x,k=p*4;if([0,1,2,3].every(c=>source.data[k+c]===final[k+c]))continue;changed++;if(alpha[p]===0)outside++;if(protectedPixel(x,y))face++;}
if(outside||face)throw Error('Protected artwork changed');
review.push({id:item.id,file:filename,changed_pixels:changed,changed_outside_contour_band:outside,changed_in_protected_face:face,sha256:hash(fs.readFileSync(dest))});
}
const bPath=path.join(__dirname,'B-current.png');fs.copyFileSync(spec.source,bPath);review.push({id:'B',file:'B-current.png',unchanged_from_source:hash(fs.readFileSync(bPath))===hash(fs.readFileSync(spec.source)),sha256:hash(fs.readFileSync(bPath))});
const layers=[],detail=[],labels=[['A','A-weak.png'],['B','B-current.png'],['C','C-strong.png']];
for(let i=0;i<labels.length;i++){const [id,name]=labels[i],file=path.join(__dirname,name);layers.push({input:Buffer.from('<svg width="500" height="44"><text x="250" y="31" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#51443a">'+id+'</text></svg>'),left:i*500,top:0},{input:await sharp(file).resize(500,500).png().toBuffer(),left:i*500,top:44});detail.push({input:Buffer.from('<svg width="400" height="44"><text x="200" y="31" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#51443a">'+id+'</text></svg>'),left:i*400,top:0},{input:await sharp(file).extract({left:110,top:695,width:300,height:300}).resize(400,400).png().toBuffer(),left:i*400,top:44});}
await sharp({create:{width:1500,height:544,channels:3,background:'#fffdf8'}}).composite(layers).png().toFile(path.join(__dirname,'comparison.png'));
await sharp({create:{width:1200,height:444,channels:3,background:'#fffdf8'}}).composite(detail).png().toFile(path.join(__dirname,'outline-detail.png'));
fs.writeFileSync(path.join(__dirname,'review.json'),JSON.stringify({as_of:'2026-11-01',canvas:[w,h],review,method:'Built-in image_gen contour edits blended only in a <=12px neighborhood of warm-dark source contours; facial regions protected. B is source file copy.',limits:['Changes near contours include adjacent pigment; not a vector stroke-width edit.','Outline levels are qualitative, not calibrated line widths.','Strong outlines can extend the visible outer edge near feet without altering underlying pose.'],owner_review:'pending'},null,2)+'\n','utf8');
console.log(JSON.stringify(review));
})().catch(e=>{console.error(e);process.exit(1)});
