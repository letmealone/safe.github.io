/* BIM is a shared inspection tool. Keep the record and the user's work origin. */
const contextBeforeBusinessBim=workContext;
workContext=function(){
  const c=contextBeforeBusinessBim();
  if(screen==='map_model'&&workModel.entry?.workspace==='work')c.model=clone(workModel);
  return c;
};
const applyContextBeforeBusinessBim=applyWorkContext;
applyWorkContext=function(c){applyContextBeforeBusinessBim(c);if(c?.model)workModel=clone(c.model);};

function openCaseModel(id,options={}){
  if(!signedIn){enterLogin({screen:'case',id});return;}
  const {model,...context}=workContext();
  const entry={workspace:'work',context:{...context,dashboardScope},scrollY:window.scrollY,
    session:navigationSession,index:navigationIndex};
  const next={building:id,round:options.round==='2025'&&id===2?'2025':'2026',
    version:options.version||'current',angle:28,zoom:1,floor:0,
    defect:options.defect||'F-03',compare:false,missing:false,entry};
  if(options.defect)next.floor=options.defect==='F-01'?1:options.defect==='F-02'?2:3;
  go('map_model',{id,model:next});
}
function modelReturnLabel(){
  if(workModel.entry?.workspace!=='work')return '지도로 돌아가기';
  const labels={home:'내 업무로',list:'점검 현황으로',case:'점검 상세로',histories:'점검 이력으로',history:'회차·버전 이력으로',
    prep:'현장 준비로',field:'현장 근거로',defect:'근거 상세로',report:'보고서로',review:'검토 화면으로'};
  return `${labels[workModel.entry.context?.screen]||'이전 업무로'} 돌아가기`;
}
function returnModelSource(){
  const entry=workModel.entry;
  if(entry?.workspace!=='work'){returnModelMap();return;}
  if(entry.context.role!==role){go('home');return;}
  const prior=entry.session===navigationSession?navigationEntries[entry.index]:null;
  if(entry.index<navigationIndex&&prior?.screen===entry.context.screen&&canReturnTo(prior)){
    rememberDraft();rememberWork();rememberNavigation();persistDemo();
    history.go(entry.index-navigationIndex);return;
  }
  dashboardScope=entry.context.dashboardScope||'mine';
  go(entry.context.screen||'case',{id:entry.context.selected||selected,workContext:entry.context});
  window.scrollTo(0,entry.scrollY||0);rememberNavigation();
}
function caseBimButton(b,label='BIM·결함 위치',options={},style='mini'){
  const model=publicBuildings.find(x=>x.id===b.id);
  return model?.model?btn(label,esc(`openCaseModel(${b.id},${JSON.stringify(options)})`),style).replace('<button ',`<button data-bim-building="${b.id}" data-bim-round="${options.round||'2026'}" data-bim-version="${options.version||'current'}" `):
    '<span class="bim-unavailable">BIM 미등록 · 점검자료에서 확인</span>';
}

const tableBeforeBusinessBim=caseTable;
caseTable=function(rows){
  let html=tableBeforeBusinessBim(rows);
  for(const b of rows){const action=btn('업무 건 열기',`openCase(${b.id})`,'mini');
    html=html.replace(action,`${action} ${caseBimButton(b,'BIM 보기')}`);}
  return html;
};
const headBeforeBusinessBim=caseHead;
caseHead=function(tab='case'){
  if(tab==='history')return headBeforeBusinessBim(tab);
  const b=building();
  return headBeforeBusinessBim(tab).replace('<div class="tabs">',
    `<div class="case-bim-entry"><div><strong>이번 점검의 공간·결함 확인</strong><span>${b.dong} · ${b.round} · 선택한 점검과 연결</span></div>${caseBimButton(b)}</div><div class="tabs">`);
};

pages.histories=()=>`<div class="bar"><div><h1>노후건축물·점검 이력</h1><p class="muted">조회범위: ${dashboardScope==='mine'?'내 담당':role==='official'?'관할 전체':'기관 전체'} · 확인할 회차의 기록과 BIM을 선택하세요.</p></div></div><section class="panel"><div class="tablebox"><table><thead><tr><th>건축물·동</th><th>업무유형·회차</th><th>표시 기록</th><th>보기</th></tr></thead><tbody>${workspaceRows().flatMap(b=>(b.id===2?['2026','2025']:['2026']).map(round=>`<tr><td>${b.name} · ${b.dong}<small>${b.address}</small></td><td>${b.type}<small>${round==='2025'?'2025년 1회차':b.round}</small></td><td>${b.id===2?round==='2025'?'이전 회차 보관 기록':`이번 회차 · 보고서 v${state.version}`:'원천 기록·모델 연결 확인'}</td><td><div class="history-row-actions">${btn(b.id===2?'회차·버전 이력 열기':'업무 개요',b.id===2?"go('history',{id:2})":`openCase(${b.id})`,'mini')}${caseBimButton(b,'이 회차 BIM',{round})}</div></td></tr>`)).join('')}</tbody></table></div></section>`;

function historyBimPanel(){
  const b=building();
  return `<section class="panel history-bim-panel"><div class="bar"><div><h2>회차별 BIM·결함 위치</h2><p class="muted">같은 본동의 기록을 선택합니다. 모델 기준일과 점검 회차는 BIM 화면에서도 확인할 수 있습니다.</p></div></div><div class="history-bim-rounds"><div><strong>2026년 2회차 · 이번 점검</strong><p>현재 보고서 v${state.version} · 연결된 현장 근거</p>${caseBimButton(b,'2026년 2회차 BIM',{round:'2026'},'primary mini')}</div><div><strong>2025년 1회차 · 이전 점검</strong><p>당시 보관 기록 · 이전 회차 관찰값</p>${caseBimButton(b,'2025년 1회차 BIM',{round:'2025'})}</div></div>${state.snapshots.length?`<details class="history-bim-versions"><summary>이번 회차의 공유 버전별 BIM 근거 확인</summary><p class="muted">공유 원문에 연결된 설명을 확인합니다. 보고서 버전과 모델 버전은 별개입니다.</p><div class="actions">${state.snapshots.map(s=>caseBimButton(b,`공유 v${s.version}의 BIM 근거`,{round:'2026',version:String(s.version)})).join('')}</div></details>`:''}</section>`;
}
const historyBeforeBusinessBim=pages.history;
pages.history=()=>historyBeforeBusinessBim().replace('<div class="grid">',historyBimPanel()+'<div class="grid history-comparison">').replace('<table>','<div class="tablebox"><table>').replace('</table>','</table></div>');

explanations.list=['점검 현황에서 BIM 바로 확인','직전 시안의 점검 현황에는 BIM 진입 버튼이 없었습니다.','선택한 업무의 모델을 보려면 지도에서 같은 대상을 다시 찾아야 했습니다.','업무 행에 BIM 보기를 연결하고 같은 건축물 동·회차를 유지합니다.','업무 처리 버튼을 유지하며 BIM을 필요한 때 사용하는 공통 도구로 제공합니다.'];
explanations.histories=['점검 이력에서 해당 회차 BIM 열기','직전 시안의 이력 목록은 회차·버전 이력으로만 연결됐습니다.','과거 기록을 확인하다 BIM으로 이동할 때 어느 회차를 보는지 다시 맞춰야 했습니다.','회차별 행에서 같은 기록의 BIM을 열고 원래 이력으로 돌아옵니다.','당시 기록과 현재 기록, 보고서 버전과 모델 기준을 구분합니다.'];
explanations.case=[...explanations.case];explanations.case[3]+=' 점검 상세에서도 같은 동·회차의 BIM과 결함을 바로 엽니다.';
explanations.history=[...explanations.history];explanations.history[2]='과거 관찰값을 읽다가 해당 회차의 공간·근거를 바로 확인하기 어렵고, 현재 기록과 혼동할 수 있습니다.';explanations.history[3]='회차별 BIM과 공유 버전별 근거를 직접 연결하고 이력 화면으로 돌아오게 합니다.';
const explanationBeforeBusinessBim=explanations.map_model;
explanations.map_model=[explanationBeforeBusinessBim[0],
  '직전 시안은 업무용 BIM이 지도 분석에 속해 점검 현황·이력과의 직접 연결이 약했습니다.',
  '점검 대상이나 과거 회차를 선택한 뒤에도 지도에서 대상을 다시 찾거나 업무 탭을 벗어나야 했습니다.',
  '지도·점검 현황·상세·이력에서 같은 BIM을 열고 진입한 업무·회차·공유 버전을 유지합니다.',
  'BIM을 닫으면 원래 화면·검색조건·스크롤로 돌아옵니다. 지도와 내 업무의 이전 위치는 각각 보관합니다.'];

const tourBeforeBusinessBim=showTourStep;
tourSteps.push(
  {label:'점검 현황 · 같은 점검의 BIM 진입',businessStage:'list'},
  {label:'점검 상세 · BIM과 업무 연결',businessStage:'case'},
  {label:'점검 이력 · 회차별 BIM 진입',businessStage:'histories'},
  {label:'회차·버전 이력 · BIM 선택',businessStage:'history'},
  {label:'이전 회차 BIM · 점검 이력으로 복귀',businessStage:'pastModel'}
);
showTourStep=function(i){
  const stage=tourSteps[i]?.businessStage;
  if(!stage){tourBeforeBusinessBim(i);return;}
  tourBeforeBusinessBim(7);selected=2;
  go(stage==='pastModel'?'histories':stage,{id:2});
  if(stage==='pastModel')openCaseModel(2,{round:'2025'});
};
