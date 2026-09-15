/* Offline geographic interaction and fictional inspection records. */
const MAP_KEY='safetywatch-map-v3';
const mapMeta={1:{area:'janghang2',street:'중앙로 10'},2:{area:'janghang1',street:'안전로 20'},3:{area:'madu1',street:'문화로 30'}};
for(const b of publicBuildings){
  const m=mapMeta[b.id],r=MAP_REGIONS[m.area];
  m.point=r.label.slice();m.admDong=r.name;
  b.address=`경기도 고양시 일산동구 ${r.name} · 예시 ${m.street}`;
  buildings.find(x=>x.id===b.id).address=b.address;
}
caseRoutes.add('map_model');analysisRoutes.add('map_model');
let mapViews={},workModel={building:2,round:'2026',version:'current',angle:28,zoom:1,floor:0,defect:'F-03',compare:false,missing:false};
let mapDrag=null,mapWheelTime=0;
function mapMode(){return screen==='public_map'?'public':role;}
function mapView(mode=mapMode()){
  if(!mapViews[mode]){
    const saved=mode!=='public'?demoProfiles[mode]?.map:null;
    mapViews[mode]=saved&&MAP_REGIONS[saved.area]?clone(saved):{area:mode==='public'?'kr':'goyang',query:'',pick:0,viewport:null,withinView:false};
  }
  const m=mapViews[mode];if(!m.viewport)m.viewport=fitMapBounds(MAP_REGIONS[m.area].bounds);
  return m;
}
function fitMapBounds(b){
  let w=Math.max(b[2]-b[0],.025)*1.25,h=Math.max(b[3]-b[1],.025)*1.25;
  if(w/h<1.65)w=h*1.65;else h=w/1.65;
  return {x:(b[0]+b[2]-w)/2,y:(b[1]+b[3]-h)/2,w,h};
}
function mapAncestors(id){const items=[];for(let r=MAP_REGIONS[id];r;r=MAP_REGIONS[r.parent])items.unshift(r);return items;}
function mapInArea(b,id){return id==='kr'||mapAncestors(mapMeta[b.id].area).some(r=>r.id===id);}
function accessibleMapBuildings(){return publicBuildings.filter(b=>screen==='public_map'||canAccessCase(b.id));}
function gisResults(){
  const m=mapView(),q=screen==='public_map'?publicQuery:m.query;
  return accessibleMapBuildings().filter(b=>mapInArea(b,m.area)&&(!q||normalize(`${b.name}${b.dong}${b.address}${mapMeta[b.id].street}`).includes(normalize(q)))
    &&(screen!=='public_map'||publicFilter==='전체'||b.model)
    &&(screen==='public_map'||analysisFilter==='전체'||(analysisFilter==='점검기록 있음'?b.id!==3:b.id===3))
    &&(!m.withinView||pointInViewport(mapMeta[b.id].point,m.queryBounds||m.viewport)));
}
function pointInViewport(p,v){return p[0]>=v.x&&p[0]<=v.x+v.w&&p[1]>=v.y&&p[1]<=v.y+v.h;}
function mapSave(){
  if(signedIn&&screen!=='public_map'&&!stagePreview){profile().map=clone(mapView(role));persistDemo();}
}
const rememberBeforeMap=rememberWork;
rememberWork=function(){
  rememberBeforeMap();
  if(signedIn&&isAnalysisRoute(screen)){
    profile().map=clone(mapView(role));
    profile().analysis={screen,filter:analysisFilter,selected,model:clone(workModel)};
  }
};
openWorkspace=function(which){
  rememberDraft();rememberWork();persistDemo();
  if(which==='analysis'){
    const c=profile().analysis||{screen:'region',filter:'전체'};
    analysisFilter=c.filter||'전체';
    go(c.screen||'region',c.screen==='map_model'?{id:c.selected||2,model:c.model}:{});
  }else{const c=lastWorkView||{screen:'home',selected:2};go(c.screen||'home',{workContext:c});}
};
function refreshMap(replace=true){go(screen,{replace});mapSave();}
function chooseMapArea(id){
  const m=mapView();if(!MAP_REGIONS[id])return;
  m.area=id;m.pick=0;m.withinView=false;m.viewport=fitMapBounds(MAP_REGIONS[id].bounds);
  refreshMap(false);
}
function searchGIS(inputId){
  const q=document.getElementById(inputId)?.value.trim()||'',m=mapView();
  m.query=q;m.area='kr';m.withinView=false;m.pick=0;
  if(screen==='public_map')publicQuery=q;
  const rows=gisResults();m.viewport=rows.length?boundsForBuildings(rows):fitMapBounds(MAP_REGIONS.kr.bounds);
  refreshMap(true);
}
function boundsForBuildings(rows){
  const points=rows.map(b=>mapMeta[b.id].point),xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
  const cx=(Math.min(...xs)+Math.max(...xs))/2,cy=(Math.min(...ys)+Math.max(...ys))/2;
  // Keep nearby administrative context even when a search finds one building.
  const w=Math.max(12,Math.max(...xs)-Math.min(...xs)+3),h=Math.max(7,Math.max(...ys)-Math.min(...ys)+3);
  return fitMapBounds([cx-w/2,cy-h/2,cx+w/2,cy+h/2]);
}
function mapResultCount(){const rows=gisResults();return `조회 전체 ${rows.length}건 · 현재 화면 ${rows.filter(b=>pointInViewport(mapMeta[b.id].point,mapView().viewport)).length}건`;}

function selectMapBuilding(id){
  const m=mapView();if(!gisResults().some(b=>b.id===id))return;
  m.pick=id;if(screen==='public_map')publicSelected=id;
  if(m.viewport.w>25||!pointInViewport(mapMeta[id].point,m.viewport))m.viewport=boundsForBuildings([publicBuildings.find(b=>b.id===id)]);
  refreshMap(false);
}
function clearMapSelection(){mapView().pick=0;refreshMap(false);}
function mapReturn(){go(signedIn?'region':'public_map');}
function resetMapConditions(){const m=mapView();m.query='';m.withinView=false;m.pick=0;if(screen==='public_map'){publicQuery='';publicFilter='전체';}else analysisFilter='전체';refreshMap();}
function mapZoom(factor,anchor=null){
  const m=mapView(),v=m.viewport,newW=Math.max(.035,Math.min(1300,v.w*factor));factor=newW/v.w;
  const p=anchor||[v.x+v.w/2,v.y+v.h/2];
  m.viewport={x:p[0]-(p[0]-v.x)*factor,y:p[1]-(p[1]-v.y)*factor,w:newW,h:v.h*factor};
  updateMapCanvas();commitMapView();
}
function panMap(dx,dy){const v=mapView().viewport;v.x+=v.w*dx;v.y+=v.h*dy;updateMapCanvas();commitMapView();}
function commitMapView(){
  if(typeof renderedNavigation!=='undefined'){renderedNavigation=navigationSnapshot();rememberNavigation();}
  mapSave();
}
function showMapSources(){modal('지도와 예시 자료의 범위',`<p>시·도는 2021년, 고양시는 2020년 공개 경계를 단순화했습니다. 구·동의 도형은 탐색 조작을 설명하는 가상 구획입니다.</p><p>세 건물의 위치·주소·점검자료·sBIM과 근거 그림은 모두 가상입니다. 지역별 숫자는 이 시안의 사례 수이며 위험도나 실제 관리 통계가 아닙니다.</p><p><a href="reference/map/README.md" target="_blank">경계 출처·이용 조건</a> · geoBoundaries / Natural Earth / citypopulation.de</p>`);}
function mapSVG(){
  const m=mapView(),v=m.viewport,rows=gisResults(),r=MAP_REGIONS[m.area];
  let children=Object.values(MAP_REGIONS).filter(x=>x.parent===m.area);
  // Wheel zoom can expose finer layers without changing the selected search area.
  if(v.w<45&&['kr','KR-41','goyang'].includes(m.area))children=Object.values(MAP_REGIONS).filter(x=>x.parent==='goyang');
  if(v.w<22&&(['kr','KR-41','goyang','ilsaneast'].includes(m.area)||r.parent==='ilsaneast'))children=Object.values(MAP_REGIONS).filter(x=>x.parent==='ilsaneast');
  const unit=v.w/850;
  const base=Object.values(MAP_REGIONS).filter(x=>x.level===0).map(x=>`<path d="${x.path}" class="gis-base"/>`).join('');
  const areaPaths=children.map(x=>{const count=rows.filter(b=>mapInArea(b,x.id)).length;return `<g class="gis-region" role="button" tabindex="0" aria-label="${x.name} 지역 확대" onclick="chooseMapArea('${x.id}')" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();chooseMapArea('${x.id}')}"><path d="${x.path}" fill="${count?'#c4dded':'#e2e9ed'}"/><title>${x.name} · 가상 사례 ${count}건</title>${v.w<100||x.id==='KR-41'||!['KR-11','KR-28','KR-30','KR-50','KR-29','KR-27','KR-31','KR-26'].includes(x.id)?`<text x="${x.label[0]}" y="${x.label[1]-(count&&v.w<25?unit*27:0)}" style="font-size:${unit*13}px">${x.name}${count?' · '+count:''}</text>`:''}</g>`;}).join('');
  let pins='';
  if(v.w<25){pins=rows.map(b=>{const p=mapMeta[b.id].point;return `<g class="gis-pin ${m.pick===b.id?'selected':''}" role="button" tabindex="0" aria-label="${b.name} ${b.dong} 요약 열기" onclick="selectMapBuilding(${b.id})" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();selectMapBuilding(${b.id})}"><rect x="${p[0]-unit*14}" y="${p[1]-unit*12}" width="${unit*28}" height="${unit*23}" rx="${unit*3}"/><text x="${p[0]}" y="${p[1]+unit*4}" style="font-size:${unit*13}px">${b.id}</text><text class="gis-building-label" x="${p[0]}" y="${p[1]+unit*31}" style="font-size:${unit*12}px">${b.name} · ${b.dong}</text></g>`;}).join('');}
  return `<svg id="gis-svg" viewBox="${v.x} ${v.y} ${v.w} ${v.h}" role="group" aria-label="노후건축물 탐색 지도" tabindex="0"><rect x="9700" y="-4000" width="1300" height="1200" fill="#eaf3f7"/>${base}${r.path?`<path class="gis-selected-area" d="${r.path}"/>`:''}${areaPaths}${pins}</svg>`;
}
function updateMapCanvas(){const node=$('#gis-canvas');if(node){node.innerHTML=mapSVG();bindMapGestures();$('#gis-scale').textContent=mapView().viewport.w<25?'개별 건물 표시':'지역별 분포 표시';$('#gis-result-count').textContent=mapResultCount();}}
function bindMapGestures(){
  const svg=$('#gis-svg');if(!svg)return;
  svg.addEventListener('wheel',e=>{e.preventDefault();const now=performance.now();if(now-mapWheelTime<70)return;mapWheelTime=now;const p=svg.createSVGPoint();p.x=e.clientX;p.y=e.clientY;const q=p.matrixTransform(svg.getScreenCTM().inverse());mapZoom(e.deltaY>0?1.3:1/1.3,[q.x,q.y]);},{passive:false});
  svg.addEventListener('keydown',e=>{const ops={'+':()=>mapZoom(.75),'-':()=>mapZoom(1.3),'ArrowLeft':()=>panMap(-.15,0),'ArrowRight':()=>panMap(.15,0),'ArrowUp':()=>panMap(0,-.15),'ArrowDown':()=>panMap(0,.15)};if(e.target===svg&&ops[e.key]){e.preventDefault();ops[e.key]();}});
  svg.addEventListener('pointerdown',e=>{if(e.button!==0)return;mapDrag={x:e.clientX,y:e.clientY,viewport:clone(mapView().viewport),moved:false};});
  svg.addEventListener('pointermove',e=>{if(!mapDrag)return;if(!mapDrag.moved&&Math.hypot(e.clientX-mapDrag.x,e.clientY-mapDrag.y)<5)return;mapDrag.moved=true;svg.setPointerCapture(e.pointerId);const rect=svg.getBoundingClientRect(),v=mapDrag.viewport;mapView().viewport={...v,x:v.x-(e.clientX-mapDrag.x)*v.w/rect.width,y:v.y-(e.clientY-mapDrag.y)*v.h/rect.height};const p=mapView().viewport;svg.setAttribute('viewBox',`${p.x} ${p.y} ${p.w} ${p.h}`);});
  const end=()=>{if(mapDrag){const moved=mapDrag.moved;mapDrag=null;if(moved){updateMapCanvas();commitMapView();}}};svg.addEventListener('pointerup',end);svg.addEventListener('pointercancel',end);
}
function mapSummary(b){
  const pub=screen==='public_map',m=mapMeta[b.id],record=buildings.find(x=>x.id===b.id);
  return `<div class="gis-summary"><div class="bar"><span class="eyebrow">선택한 노후건축물</span>${btn('선택 닫기','clearMapSelection()','text mini')}</div><h2>${b.name} · ${b.dong}</h2><p class="muted">${b.address} · 가상 주소</p><div class="identity-note">행정구역: ${m.admDong} / 건축물 동: ${b.dong}</div><div class="summary-status">${chip(b.id===3?'검토 후보':'점검 관리 대상',b.id===3?'warn':'blue')}${chip(pub?'공개된 정보만 열람':'업무 권한 범위','')}</div><dl class="kv"><dt>사용승인</dt><dd>${b.year}년 · 가상</dd><dt>업무유형</dt><dd>${record.type}</dd><dt>표시 기록</dt><dd>${pub?publicSafetySummary(b).record:record.round}</dd><dt>${pub?'자료 범위':'진행상태'}</dt><dd>${pub?'공개 기본정보·모델':caseStatus(record)}</dd></dl><section class="gis-finding"><h3>${pub?'공개 안전정보':'지금 확인할 사항'}</h3><p>${pub?publicSafetySummary(b).description:(b.id===2?nextTask(record):b.id===1?'정기점검 보고자료와 원천 기록의 연결을 확인합니다.':'동 식별정보와 대장 연결을 확인한 후 관련 조사자료를 대조합니다.')}</p>${!pub&&b.id===2?`<p class="muted">현장 근거 3건 · ${state.evidence?'위치 설명 확인됨':'F-03 위치 설명 확인 필요'}</p>`:''}</section><div class="summary-actions">${pub?(b.model?btn('공개 3D/BIM 열기',`publicSelected=${b.id};go('public_bim')`,'primary'):btn('공개 정보 상세',`choosePublicBuilding(${b.id})`,'primary')):btn(b.model?'결함 위치 · sBIM 보기':'모델 없는 자료 확인',`openWorkModel(${b.id})`,'primary')}${pub?btn('노후건축물 정보 상세',`choosePublicBuilding(${b.id})`):btn('이 점검건 업무 열기',`openCase(${b.id})`)}${!pub?btn('근거·기존 점검 확인',b.id===2?"go('candidate')":`openCase(${b.id})`,'text'):''}</div><p class="source-line">가상 기록 기준일 2026.09.15<br>안전등급: ${pub?'공개 자료 미제공':'해당 평가 원천 기록 별도 확인'}</p></div>`;
}
function gisPage(){
  const pub=screen==='public_map',m=mapView(),rows=gisResults(),region=MAP_REGIONS[m.area];
  if(pub)m.query=publicQuery;
  const chosen=rows.find(b=>b.id===m.pick),children=Object.values(MAP_REGIONS).filter(r=>r.parent===m.area);
  const input=pub?'public-search':'gis-search';
  return `<div class="bar gis-heading"><div><div class="eyebrow">${pub?'GIS+sBIM 기반 공개 정보조회':'내 업무와 연결된 지도 분석'}</div><h1>노후건축물 ${pub?'공개 지도':'지도 분석'}</h1><p class="muted">${pub?'로그인 없이 공개 자료 조회':role==='official'?'조회 권한: 예시 지자체 관할':'조회 권한: 예시 B점검기관 담당 건'} · 건물과 기록은 가상 예시</p></div>${btn(pub?'서비스 메인':'작업 화면으로 돌아가기',pub?"go('landing')":"openWorkspace('work')")}</div><section class="gis-searchbar"><form onsubmit="event.preventDefault();searchGIS('${input}')"><label class="sr-only" for="${input}">주소 또는 노후건축물명 검색</label><input id="${input}" value="${esc(m.query)}" placeholder="주소·건물명 검색 · 예: 안전로 20, 주민회관"><button class="primary" type="submit">${pub?'검색':'주소·건물 검색'}</button></form><div class="gis-condition"><label for="${pub?'public-model-filter':'analysis-filter'}">${pub?'공개 3D':'자료 상태'}</label><select id="${pub?'public-model-filter':'analysis-filter'}" ${pub?'onchange="publicFilter=this.value;mapView().pick=0;refreshMap()"':''}>${(pub?['전체','3D 있음']:['전체','점검기록 있음','연결 확인 필요']).map(v=>`<option ${(pub?publicFilter:analysisFilter)===v?'selected':''}>${v}</option>`).join('')}</select>${pub?'':btn('분석 조건 적용',"analysisFilter=document.querySelector('#analysis-filter').value;mapView().pick=0;refreshMap()")}${btn('조건 초기화','resetMapConditions()','text')}</div></section><div class="gis-breadcrumb" aria-label="행정구역 경로">${mapAncestors(m.area).map(r=>btn(r.name,`chooseMapArea('${r.id}')`,r.id===m.area?'active':'text')).join('<span>›</span>')}<span class="muted">${m.area==='kr'?'남한 전체':'선택한 조회 지역'}</span></div><div class="gis-layout"><section class="gis-map-panel"><div class="gis-map-top"><strong>${region.name} · ${m.withinView?'선택한 화면 범위':'지역 범위'} 조회</strong><span id="gis-result-count" aria-live="polite">${mapResultCount()}</span></div><div class="gis-map-wrap"><div id="gis-canvas">${mapSVG()}</div><div class="gis-map-tools">${btn('＋',"mapZoom(.7)")}${btn('−',"mapZoom(1.4)")}${btn('↑',"panMap(0,-.2)")}${btn('←',"panMap(-.2,0)")}${btn('→',"panMap(.2,0)")}${btn('↓',"panMap(0,.2)")}</div><div class="gis-map-bottom">${btn('선택 지역에 맞추기',"mapView().viewport=fitMapBounds(MAP_REGIONS[mapView().area].bounds);refreshMap()",'mini')}${btn('이 화면 범위에서 조회',"mapView().withinView=true;mapView().queryBounds=clone(mapView().viewport);mapView().pick=0;refreshMap()",'mini')}<span id="gis-scale">${m.viewport.w<25?'개별 건물 표시':'지역별 분포 표시'}</span></div></div><div class="gis-area-choices"><div class="bar"><strong>${children.length?'하위 지역 선택':'지역 안의 대상'}</strong>${region.parent?btn('상위 지역으로',`chooseMapArea('${region.parent}')`,'text mini'):''}</div><div class="gis-region-buttons">${children.map(r=>btn(`${r.name}${accessibleMapBuildings().filter(b=>mapInArea(b,r.id)).length?' · '+accessibleMapBuildings().filter(b=>mapInArea(b,r.id)).length+'건':''}`,`chooseMapArea('${r.id}')`,'mini')).join('')||`<span class="muted">${rows.length?'지도 또는 오른쪽 목록에서 건물을 선택하세요.':'이 지역의 가상 사례가 없습니다.'}</span>`}</div></div><div class="gis-map-note">휠: 확대·축소 / 빈 지도 드래그: 이동 · 확대해도 조회 지역은 유지됩니다.<br>시·도 경계 2021 / 고양시 경계 2020 / 구·동은 가상 구획. 색·숫자는 위험도가 아닙니다. ${btn('지도·자료 출처','showMapSources()','text mini')}</div></section><aside class="gis-side" aria-label="선택 건물 요약과 같은 조건의 결과">${chosen?mapSummary(chosen):`<div class="gis-intro"><div class="eyebrow">${pub?'공개 정보 확인':'대상과 근거 확인'}</div><h2>어느 노후건축물을 볼까요?</h2><p>지역을 선택하거나 주소를 검색하세요. 건물을 누르면 ${pub?'공개 정보와 공개용 모델':'진행상태·현장 근거·sBIM'}로 연결합니다.</p></div>`}<div class="gis-list"><h3>같은 조건의 결과 · ${rows.length}건</h3>${rows.map(b=>`<button class="public-result ${m.pick===b.id?'active':''}" onclick="selectMapBuilding(${b.id})"><strong>${b.name} · ${b.dong}</strong><span>${mapMeta[b.id].admDong} · 예시 ${mapMeta[b.id].street}</span><span>${b.id===3?'대장 연결 확인 필요':pub?'공개 기본정보 있음':caseStatus(buildings.find(x=>x.id===b.id))} · ${b.model?'3D 있음':'3D 미등록'}</span></button>`).join('')||`<div class="empty"><p>현재 조건의 가상 사례가 없습니다.</p>${btn('예시가 있는 고양시 보기',"resetMapConditions();chooseMapArea('goyang')")}</div>`}</div></aside></div>`;
}
pages.public_map=gisPage;pages.region=gisPage;
const oldSearchPublic=searchPublic;
searchPublic=function(inputId='public-search'){
  if(screen==='public_map'){searchGIS(inputId);return;}
  publicQuery=document.getElementById(inputId)?.value.trim()||'';
  const m=mapView('public');m.query=publicQuery;m.area='kr';m.pick=0;m.withinView=false;
  const rows=publicResults();m.viewport=rows.length?boundsForBuildings(rows):fitMapBounds(MAP_REGIONS.kr.bounds);go('public_map');
};
const baseMapRender=render;
render=function(){baseMapRender();const isMap=['public_map','region','map_model'].includes(screen);document.body.classList.toggle('gis-mode',isMap);if(isMap){$('#sidebar').style.display='none';$('#shell').style.gridTemplateColumns='1fr';}if(['public_map','region'].includes(screen))bindMapGestures();if(screen==='map_model')drawWorkModel();};
const mapNavContext=navContext;
navContext=()=>({...mapNavContext(),mapViews:clone(mapViews),workModel:clone(workModel)});
function restoreMapNavigation(c){if(c.mapViews)mapViews=clone(c.mapViews);if(c.workModel)workModel=clone(c.workModel);}
const mapReset=resetDemo;
resetDemo=function(r='agency'){mapViews={};workModel={building:2,round:'2026',version:'current',angle:28,zoom:1,floor:0,defect:'F-03',compare:false,missing:false};mapReset(r);};
