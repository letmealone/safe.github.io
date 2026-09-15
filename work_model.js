/* Linked sBIM and evidence, using the same fictional case as the work flow. */
function openWorkModel(id){
  if(!signedIn){enterLogin({screen:'map_model',id});return;}
  const next=workModel.building===id?clone(workModel):{building:id,round:'2026',version:'current',angle:28,zoom:1,floor:0,defect:'F-03',compare:false,missing:false};
  delete next.entry;
  go('map_model',{id,model:next});
}
function modelBuilding(){return publicBuildings.find(b=>b.id===selected)||publicBuildings[1];}
function returnModelMap(){
  const m=mapView(role),b=modelBuilding();
  if(m.pick!==selected||!gisResults().some(x=>x.id===selected)){
    m.area=mapMeta[selected].area;m.query='';m.withinView=false;m.pick=selected;
    m.viewport=boundsForBuildings([b]);analysisFilter='전체';
  }
  go('region');mapSave();
}
function modelVersion(){return workModel.version==='current'?state.version:Number(workModel.version);}
function modelRoundLabel(){return workModel.round==='2025'?'2025년 1회차':buildings.find(b=>b.id===selected).round;}
function modelDefects(){return selected===2?defects:[];}
function modelCaption(d){
  if(workModel.round==='2025')return d.id==='F-03'?'[가상 이전 기록] 옥상 난간 주변의 사진 기록. 이번 자료와 촬영 위치를 대조합니다.':`[가상 이전 기록] ${d.place}의 ${d.kind} 관찰.`;
  const snapshot=state.snapshots.find(s=>s.version===modelVersion());
  return snapshot?.captions?.[d.id]||(workModel.version==='current'?state.captions?.[d.id]:null)||(d.id==='F-03'?'[가상 현재 기록] 옥상 난간 촬영 위치의 설명 확인이 필요합니다.':`[가상 현재 기록] ${d.place} ${d.part}의 관찰 기록.`);
}
function modelLocation(d){return d.id==='F-03'&&workModel.round==='2026'&&!state.evidence?'대략 위치 · 설명 확인 필요':'연결 위치 · 가상 매핑';}
function modelRecordTitle(){if(selected!==2)return `${modelRoundLabel()} · 보고서 연계 미확인`;return `${modelRoundLabel()} · ${workModel.round==='2025'?'보관 기록':`보고서 v${modelVersion()}${workModel.version==='current'&&state.phase==='draft'?' 작성 중':''}`}`;}
function selectModelDefect(id){
  const d=modelDefects().find(x=>x.id===id);if(!d)return;
  workModel.defect=id;workModel.floor=id==='F-01'?1:id==='F-02'?2:3;workModel.angle=28;
  go('map_model',{replace:true});
}
function selectModelFloor(floor){
  workModel.floor=floor;
  if(floor){const d=modelDefects().find(d=>floor===(d.id==='F-01'?1:d.id==='F-02'?2:3));workModel.defect=d?.id||'';workModel.angle=28;}
  else if(!modelDefects().some(d=>d.id===workModel.defect))workModel.defect=modelDefects()[0]?.id||'';
  go('map_model',{replace:true});
}
function modelChangeRound(value){workModel.round=value;workModel.version='current';workModel.floor=0;go('map_model',{replace:true});}
function modelChangeVersion(value){workModel.version=value;go('map_model',{replace:true});}
function modelMove(action,value){
  if(action==='angle')workModel.angle=Number(value);
  if(action==='zoom')workModel.zoom=Math.max(.6,Math.min(1.7,workModel.zoom+value));
  if(action==='reset'){workModel.angle=28;workModel.zoom=1;workModel.floor=0;}
  drawWorkModel();if(typeof renderedNavigation!=='undefined'){renderedNavigation=navigationSnapshot();rememberNavigation();}
}
function openModelEvidence(){
  const d=modelDefects().find(x=>x.id===workModel.defect);if(!d)return;
  if(workModel.round==='2026'&&modelVersion()===state.version){selectedDefect=d.id;go('defect',{id:selected});}
  else modal('선택한 기록의 근거',`<p><strong>${modelBuilding().name} · ${modelBuilding().dong}</strong><br>${modelRecordTitle()} / ${d.id} · ${d.place}</p>${sketch(d.id==='F-03'?'roof':'wall','가상 현장사진 도식')}<p>${esc(modelCaption(d))}</p><p>관찰값: ${workModel.round==='2025'?d.before:d.value}</p><p class="muted">선택한 보관 기록을 읽기 전용으로 확인합니다.</p>`);
}
function modelEvidencePanel(){
  const d=modelDefects().find(x=>x.id===workModel.defect);if(!d)return `<section class="model-evidence"><h3>연결된 결함 근거가 없습니다.</h3><p>모델 등록 여부와 점검 근거 등록은 구분합니다.</p>${btn('점검 자료 확인',`openCase(${selected})`)}</section>`;
  return `<section class="model-evidence" aria-live="polite"><div class="eyebrow">선택한 위치와 연결된 근거</div><h2>${d.id} · ${d.place}</h2><div class="summary-status">${chip(d.kind,'blue')}${chip(modelLocation(d),d.id==='F-03'?'warn':'')}</div>${sketch(d.id==='F-03'?'roof':'wall',`${d.id} · 현장사진을 대신한 가상 도식`)}<dl class="kv"><dt>부재</dt><dd>${d.part}</dd><dt>관찰값</dt><dd>${workModel.round==='2025'?d.before:d.value}</dd><dt>기록 시점</dt><dd>${workModel.round==='2025'?'2025.10.14':'2026.09.10'} · 예시</dd><dt>근거 설명</dt><dd>${esc(modelCaption(d))}</dd></dl>${workModel.compare?`<div class="model-compare"><strong>같은 위치의 회차 비교 · 가상 대응</strong><p>2025년 1회차: ${d.before}</p><p>2026년 2회차: ${d.value}</p><small>촬영·측정 조건을 확인한 뒤 해석합니다. 수치 변화만으로 보수 완료·안전 여부를 판정하지 않습니다.</small></div>`:''}<div class="actions">${btn('선택 기록의 근거 상세','openModelEvidence()','primary')}${btn('회차·보고서 이력',"go('history',{id:2})")}</div><p class="reviewnote">그림과 측정값은 가상 자료입니다. 실제 점검·진단 결과가 아닙니다.</p></section>`;
}
pages.map_model=()=>{
  const b=modelBuilding(),record=buildings.find(x=>x.id===selected),hasModel=b.model&&!workModel.missing;
  return `<div class="model-page-head"><div><div class="eyebrow">업무용 sBIM · 결함 위치와 근거 연결</div><h1>${b.name} · ${b.dong}</h1><p class="muted">${b.address} · 가상 주소</p></div>${btn(modelReturnLabel(),"returnModelSource()")}</div><section class="model-context"><div><strong>건축물 동</strong><span>${b.dong}</span></div><div><strong>업무유형</strong><span>${record.type}</span></div><div><label for="model-round">점검 회차</label><select id="model-round" onchange="modelChangeRound(this.value)"><option value="2026" ${workModel.round==='2026'?'selected':''}>${record.round}</option>${selected===2?`<option value="2025" ${workModel.round==='2025'?'selected':''}>2025년 1회차</option>`:''}</select></div><div><label for="model-version">보고서 버전</label><select id="model-version" ${workModel.round==='2025'||selected!==2?'disabled':''} onchange="modelChangeVersion(this.value)"><option value="current">${selected!==2?'연계 미확인':workModel.round==='2025'?'보관 기록':`현재 v${state.version}${state.phase==='draft'?' · 작성 중':''}`}</option>${workModel.round==='2026'&&selected===2?state.snapshots.filter(s=>s.version!==state.version).map(s=>`<option value="${s.version}" ${String(s.version)===workModel.version?'selected':''}>공유 원문 v${s.version}</option>`).join(''):''}</select></div><div><strong>모델 기준</strong><span>${workModel.round==='2025'?'M-2025.10':'M-2026.09'} · 가상</span></div></section>${!hasModel?`<section class="panel model-missing"><h2>${b.model?'모델을 불러오지 못한 경우':'연결된 sBIM이 없습니다.'}</h2><p>건물의 안전 상태와 모델 등록·로딩 상태는 별개입니다. 사용 가능한 점검자료를 이어서 확인하세요.</p><div class="actions">${btn('기존 점검자료 보기',`openCase(${selected})`,'primary')}${b.model?btn('가상 모델 다시 열기',"workModel.missing=false;go('map_model',{replace:true})"):''}${btn(modelReturnLabel(),"returnModelSource()")}</div></section>`:`<div class="work-model-layout"><section class="work-model-main"><div class="bar"><div><h2>결함 위치</h2><p class="muted">${modelRecordTitle()}</p></div>${btn('전체 시점','modelMove(\'reset\')','mini')}</div><div class="model-defect-list"><h3>결함·확인 항목 전체 · ${modelDefects().length}건</h3><div class="model-defect-options">${modelDefects().map(d=>btn(`${d.id} · ${d.place} / ${d.part}`,`selectModelDefect('${d.id}')`,d.id===workModel.defect?'active':'')).join('')||'<p>이 모델에 연결된 결함 근거는 예시에 없습니다.</p>'}</div></div><div class="model-floor-tabs">${[0,...Array.from({length:b.floors+1},(_,i)=>i+1)].map(f=>btn(f===0?'전체':f===b.floors+1?'옥상':f+'층',`selectModelFloor(${f})`,workModel.floor===f?'active':'')).join('')}</div><div id="work-model-canvas"></div><div class="model-tools"><div><label for="work-model-rotation">회전 <span id="work-rotation-label">${workModel.angle}°</span></label><input type="range" id="work-model-rotation" min="0" max="360" value="${workModel.angle}" oninput="modelMove('angle',this.value)"></div><div class="actions">${btn('축소',"modelMove('zoom',-.15)",'mini')}${btn('확대',"modelMove('zoom',.15)",'mini')}</div></div><p class="model-legend">● 연결 위치　◌ 대략 위치　선택한 결함은 파란색으로 강조합니다.</p><div class="checkline"><input id="model-compare" type="checkbox" ${workModel.compare?'checked':''} onchange="workModel.compare=this.checked;go('map_model',{replace:true})"><label for="model-compare">같은 위치의 이전·이번 회차 관찰값 함께 보기</label></div><div class="actions">${btn('모델 로딩 실패 예시',"workModel.missing=true;go('map_model',{replace:true})",'text mini')}</div></section>${modelEvidencePanel()}</div>`}`;
};
function drawWorkModel(){
  const el=$('#work-model-canvas');if(!el)return;
  const angle=workModel.angle*Math.PI/180,z=workModel.zoom;
  const project=(x,y,h)=>[370+(x*Math.cos(angle)-y*Math.sin(angle))*1.7*z,320+((x*Math.sin(angle)+y*Math.cos(angle))*.5-h*1.5)*z];
  const points=ps=>ps.map(p=>project(...p).map(n=>n.toFixed(1)).join(',')).join(' ');
  const floors=modelBuilding().floors;const faces=[];for(let f=1;f<=floors;f++){
    const z0=(f-1)*48,z1=f*48,p=[[-105,-68,z0],[105,-68,z0],[105,68,z0],[-105,68,z0],[-105,-68,z1],[105,-68,z1],[105,68,z1],[-105,68,z1]];
    for(const [ids,color] of [[[0,1,5,4],'#a9c5d7'],[[1,2,6,5],'#789aaf'],[[2,3,7,6],'#aecbdb'],[[3,0,4,7],'#8dabbc'],[[4,5,6,7],'#d6e4ec']]){const ps=ids.map(i=>p[i]);faces.push({f,ps,color,depth:ps.reduce((a,p)=>a+p[0]*Math.sin(angle)+p[1]*Math.cos(angle),0)/4});}
  }
  faces.sort((a,b)=>a.f-b.f||a.depth-b.depth);
  const positions={'F-01':[-75,-69,20],'F-02':[70,-69,70],'F-03':[80,-69,104]};
  const roof=floors*48+8;const lines=[[-105,-68,roof],[105,-68,roof],[105,68,roof],[-105,68,roof],[-105,-68,roof]];
  const marks=modelDefects().filter(d=>!workModel.floor||workModel.floor===(d.id==='F-01'?1:d.id==='F-02'?2:3)).map(d=>{
    const p=project(...positions[d.id]),active=d.id===workModel.defect,approx=d.id==='F-03'&&workModel.round==='2026'&&!state.evidence;
    return `<g class="model-marker ${active?'selected':''}" role="button" tabindex="0" aria-label="${d.id} ${d.place} 근거 보기" onclick="selectModelDefect('${d.id}')" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();selectModelDefect('${d.id}')}"><circle cx="${p[0]}" cy="${p[1]}" r="${active?14:11}" fill="${active?'#1e64a4':approx?'white':'#c68132'}" stroke="${approx?'#c68132':'white'}" stroke-width="3" ${approx?'stroke-dasharray="3 2"':''}/><rect x="${p[0]+17}" y="${p[1]-14}" width="55" height="27" rx="4" fill="white" stroke="#b9cddd"/><text x="${p[0]+44}" y="${p[1]+4}" text-anchor="middle" font-size="12" fill="#224766">${d.id}</text></g>`;
  }).join('');
  el.innerHTML=`<svg viewBox="0 0 740 420" role="group" aria-label="${modelBuilding().name}의 가상 sBIM과 결함 위치"><defs><pattern id="work-grid" width="35" height="35" patternUnits="userSpaceOnUse"><path d="M35 0H0V35" fill="none" stroke="#dfe8ee"/></pattern></defs><rect width="740" height="420" fill="#f5f8fa"/><rect width="740" height="420" fill="url(#work-grid)"/><ellipse cx="365" cy="327" rx="235" ry="48" fill="#234c6a12"/>${faces.map(f=>`<polygon points="${points(f.ps)}" fill="${f.color}" fill-opacity="${workModel.floor&&workModel.floor!==f.f?.25:1}" stroke="#6489a0" stroke-width="1.2"/>`).join('')}<polyline points="${points(lines)}" fill="none" stroke="#587e97" stroke-width="4"/>${marks}<text x="22" y="28" font-size="13" fill="#526f85">${modelBuilding().dong} · ${workModel.floor===floors+1?'옥상':workModel.floor?workModel.floor+'층':'전체'} / ${modelRoundLabel()}</text><text x="22" y="397" font-size="12" fill="#647d90">가상 sBIM · 실제 IFC 모델과 안전진단 결과가 아닙니다.</text></svg>`;
  $('#work-rotation-label').textContent=workModel.angle+'°';$('#work-model-rotation').value=workModel.angle;
}
Object.assign(explanations,{
 region:['지역·검색·휠로 찾는 업무 지도','직전 시안의 지도는 고정된 예시 도식이었습니다.','지역을 단계별로 찾거나 보던 범위를 확대하며 대상과 근거를 확인하기 어려웠습니다.','직전·관할 범위에서 시작해 지역 클릭·주소 검색·휠을 병행하고 선택 건물의 요약을 옆에 고정합니다.','조회 범위와 지도 시점을 구분하고, 같은 건의 sBIM·업무로 이어갑니다.'],
 public_map:['전국 공개 지도와 대상 요약','직전 시안은 공개 검색 결과의 위치를 고정 도식으로 표시했습니다.','지역 탐색과 건물 상세를 연속해서 확인하는 경험을 체험하기 어려웠습니다.','전국에서 지역을 선택하거나 주소로 바로 찾고, 공개 요약과 모델로 연결합니다.','경계 시점과 가상 구획·사례의 범위를 표시합니다. 공개 조회에 업무용 결함을 노출하지 않습니다.'],
 map_model:['결함 위치와 근거가 연결된 sBIM','현행 플랫폼에 BIM·현장 근거·회차 비교가 있으나 화면을 오가며 대상을 다시 확인해야 했습니다.','위치만 표시하면 해당 사진·측정값·회차를 별도로 찾아야 합니다.','결함 목록과 모델 표시를 양방향으로 연결하고 같은 회차·버전의 근거를 함께 보여줍니다.','모델이 없어도 기록을 확인하고, 닫으면 같은 지도 범위와 건물로 복귀합니다.']
});
const originalMapTour=showTourStep;
tourSteps.push(
 {label:'전국에서 경기 지역 선택',mapStage:'province'},
 {label:'고양시에서 구 선택',mapStage:'city'},
 {label:'일산동구에서 행정동 선택',mapStage:'district'},
 {label:'공개 지도 · 선택 건물 요약',mapStage:'publicSummary'},
 {label:'업무 지도 · 점검 요약과 다음 확인',mapStage:'workSummary'},
 {label:'업무용 sBIM · 결함 위치와 근거',mapStage:'model'},
 {label:'sBIM · 이전 회차와 관찰값 비교',mapStage:'compare'},
 {label:'sBIM 미등록 · 기존 기록 확인',mapStage:'missing'},
 {label:'가상 사례가 없는 지역',mapStage:'empty'}
);
showTourStep=function(i){
  mapViews={};workModel={building:2,round:'2026',version:'current',angle:28,zoom:1,floor:0,defect:'F-03',compare:false,missing:false};
  const t=tourSteps[i];if(!t?.mapStage){originalMapTour(i);return;}
  originalMapTour(['workSummary','model','compare','missing'].includes(t.mapStage)?8:1);
  const stage=t.mapStage,m=mapView();
  m.area=({province:'KR-41',city:'goyang',district:'ilsaneast',publicSummary:'janghang1',workSummary:'goyang',model:'janghang1',compare:'janghang1',missing:'madu1',empty:'KR-11'})[stage];
  m.viewport=fitMapBounds(MAP_REGIONS[m.area].bounds);m.pick=['publicSummary','workSummary','model','compare'].includes(stage)?2:stage==='missing'?3:0;
  if(['model','compare','missing'].includes(stage)){openWorkModel(stage==='missing'?3:2);if(stage==='compare'){workModel.round='2025';workModel.compare=true;workModel.defect='F-01';workModel.floor=1;render();}}
  else {if(m.pick)m.viewport=boundsForBuildings([publicBuildings.find(b=>b.id===m.pick)]);render();}
};

const sourceBeforeLinkedModel=showSource;
showSource=function(type){if(type==='BIM'&&signedIn){openCaseModel(selected,{defect:screen==='defect'?selectedDefect:'F-03'});}else sourceBeforeLinkedModel(type);};
