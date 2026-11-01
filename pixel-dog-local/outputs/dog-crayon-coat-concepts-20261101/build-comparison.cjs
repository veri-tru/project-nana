const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const sharp = require('C:/Users/verib/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
(async () => {
  const items = [['A-short.png','A'],['B-medium.png','B'],['C-long.png','C']];
  const layers = [], files = [];
  for (let i=0; i<items.length; i++) {
    const [name,label] = items[i];
    const filename = path.join(__dirname,name);
    const raw = fs.readFileSync(filename);
    const meta = await sharp(raw).metadata();
    if (meta.width !== meta.height) throw new Error('Expected square source');
    layers.push({input: await sharp(raw).resize(512,512).png().toBuffer(), left:i*512, top:44});
    layers.push({input:Buffer.from('<svg width="512" height="44"><text x="256" y="31" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#51443a">'+label+'</text></svg>'),left:i*512,top:0});
    files.push({name,width:meta.width,height:meta.height,sha256:crypto.createHash('sha256').update(raw).digest('hex')});
  }
  await sharp({create:{width:1536,height:556,channels:3,background:'#fffdf8'}}).composite(layers).png().toFile(path.join(__dirname,'comparison.png'));
  fs.writeFileSync(path.join(__dirname,'review.json'),JSON.stringify({
    as_of:'2026-11-01',files,comparison:{width:1536,height:556},
    source_artwork_modified_after_generation:false,
    composition_only:'comparison resized and arranged; original artwork unchanged',
    approval:'owner_review_pending',
    comparison_limit:'Edit variants can shift linework, framing, and marking edges slightly; not a pixel-identical controlled experiment.',
    provisional_features:['Seated pose','Low tail placement','Unseen-side interpretation'],
    unverified:['Owner likeness approval','Style approval','Other directions','Animation compatibility','Small display user testing']
  },null,2)+'\n','utf8');
  console.log(JSON.stringify({files,comparison:'comparison.png',approval:'owner_review_pending'}));
})().catch(e=>{console.error(e);process.exit(1)});
