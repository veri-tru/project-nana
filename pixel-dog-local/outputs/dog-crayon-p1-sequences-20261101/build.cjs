const fs=require('fs'),path=require('path'),crypto=require('crypto');
const sharp=require('C:/Users/verib/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const scenes=[
 {id:'A-rest',name:'쉬면서 옆 대상 확인',situation:'CTX_REST_CHECK',targets:['기본 방향','옆 대상','옆 대상','옆 대상','옆 대상','옆 대상 · 깜박임','옆 대상','옆 대상','복귀','복귀','복귀','기본 방향'],durations:[500,125,125,125,250,125,250,125,125,125,125,500],phases:['기본','진입','진입','진입','확인','확인','확인','확인','복귀','복귀','복귀','기본']},
 {id:'B-walk',name:'걷는 중 후측방 확인',situation:'CTX_WALK_CHECK',targets:['진행 방향','전환','전환','후측방 대상','후측방 대상','후측방 대상','후측방 대상','복귀','복귀','복귀','진행 방향','진행 방향'],durations:Array(12).fill(125),phases:['기본','진입','진입','확인','확인','확인','확인','복귀','복귀','복귀','기본','기본']},
 {id:'C-alternate',name:'장난감과 사람 번갈아 확인',situation:'CTX_TARGET_PRESENT',targets:['기본 방향','장난감','장난감','장난감','사람으로 전환','사람','사람','장난감','장난감','복귀','복귀','기본 방향'],durations:[500,125,125,375,125,125,375,125,375,125,125,500],phases:['기본','진입','진입','확인','전환','전환','확인','전환','확인','복귀','복귀','기본']}
];
(async()=>{
 const manifest={version:'0.1.0',policyVersion:'1.0',status:'CANDIDATE_REVIEW_PENDING',runtimeReady:false,fps:8,tickMs:125,timeBasis:'production_default_not_observation',rendering:'flattened_generated_frames_not_independent_rig',scenes:[]};
 const audit={status:'packaging_passed',visualReview:'static_sheets_reviewed',playbackReview:'pending_step_3',deviceReview:'not_run',userApproval:'pending',scenes:[]};
 for(const s of scenes){
  const source=path.join(__dirname,s.id+'-sheet.png'),meta=await sharp(source).metadata();
  if(meta.width%4||meta.height%3||meta.width/4!==meta.height/3)throw Error('Unexpected grid');
  const cell=meta.width/4,size=400,dir=path.join(__dirname,s.id);fs.mkdirSync(dir,{recursive:true});
  const full=await sharp(source).removeAlpha().raw().toBuffer({resolveWithObject:true});
  const seams=[];
  for(let row=0;row<3;row++){
   const cuts=[0];
   for(let col=1;col<4;col++){
    const nominal=col*cell;let best=nominal,bestScore=Infinity;
    for(let x=nominal-30;x<=nominal+30;x++){
     let count=0;for(let y=row*cell;y<(row+1)*cell;y++){const j=(y*meta.width+x)*full.info.channels;if(Math.max(full.data[j],full.data[j+1],full.data[j+2])<180)count++;}
     const score=count*1000+Math.abs(x-nominal);if(score<bestScore){best=x;bestScore=score;}
    }
    if(bestScore>=1000)throw Error('No clear inter-frame seam');cuts.push(best);
   }
   cuts.push(meta.width);seams.push(cuts);
  }
  const frames=[];let t=0;
  for(let i=0;i<12;i++){
   const file=s.id+'/'+String(i+1).padStart(2,'0')+'.png';
   const row=Math.floor(i/4),col=i%4;
   const crop={left:seams[row][col],top:row*cell,width:seams[row][col+1]-seams[row][col],height:cell};
   const cropped=await sharp(source).extract(crop).png().toBuffer();
   const {data,info}=await sharp(cropped).removeAlpha().raw().toBuffer({resolveWithObject:true});
   let minX=size,minY=size,maxX=-1,maxY=-1;
   for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++){const j=(y*info.width+x)*info.channels;if(Math.max(data[j],data[j+1],data[j+2])<180){minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);}}
   if(maxX<minX)throw Error('Empty frame');
   crop.height=Math.min(cell,maxY+4);
   const packed=await sharp(source).extract(crop).png().toBuffer();
   const left=Math.round((size-crop.width)/2),top=360-maxY;
   if(left<0||top<0||top+crop.height>size)throw Error('Padding would crop source');
   const buf=await sharp({create:{width:size,height:size,channels:3,background:'#fcfaf5'}}).composite([{input:packed,left,top}]).png().toBuffer();
   fs.writeFileSync(path.join(__dirname,file),buf);
   frames.push({index:i+1,file,startMs:t,durationMs:s.durations[i],phase:s.phases[i],target:s.targets[i],sourceRect:crop,pasteOffset:{left,top},sha256:hash(buf),darkPixelBounds:{minX:minX+left,minY:minY+top,maxX:maxX+left,maxY:maxY+top}});t+=s.durations[i];
  }
  manifest.scenes.push({id:s.id,name:s.name,situationId:s.situation,canvas:{width:size,height:size},totalMs:t,loop:false,repeatLimit:1,autonomousReplay:false,replay:'explicit_preview_button_only',inputLatencyMs:0,expiresAtMs:t,targetValidity:'fixed_virtual_scene_targets_until_end',body:s.id==='B-walk'?'walk_in_place_translation_not_implemented':'maintain_pose',mouth:'relaxed_open_tongue_visible_baseline_not_pant',returnPolicy:'reevaluate_current_state_in_runtime; fixed_baseline_in_preview',frames});
  audit.scenes.push({id:s.id,sourceSize:[meta.width,meta.height],sourceSha256:hash(fs.readFileSync(source)),frames:12,allDistinct:new Set(frames.map(f=>f.sha256)).size===12,canvasSize:[size,size],cropAndPadNoScale:true,seams,darkPixelBottomProxy:360,timingAligned125ms:frames.every(f=>f.durationMs%125===0),totalMs:t});
 }
 fs.writeFileSync(path.join(__dirname,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 fs.writeFileSync(path.join(__dirname,'validation.json'),JSON.stringify(audit,null,2)+'\n');
 const cards=manifest.scenes.map(s=>`<article><h2>${s.name}</h2><img id="img-${s.id}" src="${s.frames[0].file}" alt="${s.name} 프레임"><p id="status-${s.id}" aria-live="off"></p><button data-id="${s.id}" data-action="play">처음부터 재생</button> <button data-id="${s.id}" data-action="pause">일시정지</button> <button data-id="${s.id}" data-action="next">다음 프레임</button><p><a href="${s.id}-sheet.png">12장 전체 보기</a> · ${s.totalMs/1000}초</p></article>`).join('');
 const html=`<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P1 연속 프레임 후보</title><style>body{max-width:1280px;margin:40px auto;padding:0 20px;background:#faf8f3;color:#342c26;font:16px/1.6 system-ui}h1{font-size:26px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:24px}article{border-top:1px solid #c9c0b4;padding-top:12px}h2{font-size:19px}img{width:100%;max-width:362px;display:block}button{padding:8px;border:1px solid #9b8e7f;background:white;border-radius:4px;cursor:pointer}a{color:#79512f}.note{max-width:900px}footer{margin-top:32px;border-top:1px solid #c9c0b4;padding-top:20px}</style><h1>P1 · 상황별 연속 동작 후보</h1><p class="note">시작 → 대상 확인 → 복귀. 8fps 기준, 정지 구간은 같은 그림을 유지합니다. 기본은 자동 재생하지 않습니다. 대상 이름은 장면 설정이며 실제 눈동자 추적 검증 결과가 아닙니다.</p><p class="note">정책 v1.0 / 프레임 후보 v0.1. 재생 자연스러움·실제 표시 크기·실기기·사용자 승인은 3단계에서 확인합니다. 걷기는 제자리 발 동작이며 화면 이동은 포함하지 않았습니다.</p><main>${cards}</main><footer><a href="README.md">제작·검수 기록</a> · <a href="manifest.json">프레임·시간표</a> · <a href="../../docs/contextual-motion-policy.md">상황 정책 정본</a></footer><script>const manifest=${JSON.stringify(manifest)};
 const states=new Map();
 for(const scene of manifest.scenes){const imgs=scene.frames.map(f=>{const i=new Image();i.src=f.file;return i});states.set(scene.id,{scene,imgs,index:0,running:false,elapsed:0,origin:0});show(states.get(scene.id));}
 function show(st){const f=st.scene.frames[st.index];document.getElementById('img-'+st.scene.id).src=f.file;document.getElementById('status-'+st.scene.id).textContent=f.index+'/12 · '+f.phase+' · '+f.target+' · '+f.durationMs+'ms';}
 document.addEventListener('click',e=>{const b=e.target.closest('button[data-id]');if(!b)return;const s=states.get(b.dataset.id);if(b.dataset.action==='play'){s.index=0;s.elapsed=0;s.origin=performance.now();s.running=true;}else if(b.dataset.action==='pause'){if(s.running)s.elapsed=performance.now()-s.origin;s.running=false;}else{s.running=false;s.index=(s.index+1)%s.scene.frames.length;s.elapsed=s.scene.frames[s.index].startMs;}show(s);});
 function tick(now){for(const s of states.values()){if(!s.running)continue;const elapsed=now-s.origin;if(elapsed>=s.scene.totalMs){s.index=s.scene.frames.length-1;s.running=false;}else{s.index=s.scene.frames.findIndex(f=>elapsed<f.startMs+f.durationMs);}show(s);}requestAnimationFrame(tick);}requestAnimationFrame(tick);
 </script></html>`;
 fs.writeFileSync(path.join(__dirname,'index.html'),html);
 console.log(JSON.stringify(audit));
})().catch(e=>{console.error(e);process.exit(1)});
