/* Screen history only. Going back never rewinds report versions or work status. */
let navigationSession=0, navigationIndex=0, navigationEntries=[];
let navigationEpoch=0, navigationAuth={signedIn,role}, renderedNavigation=null;
const entryRender=render;
history.scrollRestoration='manual';

function navigationSnapshot(){
  return {...navContext(),pendingDestination:pendingDestination?clone(pendingDestination):null,
    deniedCaseId,signedIn,authEpoch:navigationEpoch,scrollY:0};
}
function historyEnvelope(c){return {...c,navigationSession,navigationIndex};}
function sameView(a,b){
  if(!a||a.screen!==b.screen||a.signedIn!==b.signedIn||a.role!==b.role)return false;
  if(['public_map','region'].includes(a.screen)){
    const key=a.screen==='public_map'?'public':a.role;
    const x=a.mapViews?.[key],y=b.mapViews?.[key];
    if(x?.area!==y?.area||x?.pick!==y?.pick)return false;
  }
  if(['public_building','public_bim'].includes(a.screen))return a.publicSelected===b.publicSelected;
  if(caseRoutes.has(a.screen)&&a.selected!==b.selected)return false;
  return a.screen!=='defect'||a.selectedDefect===b.selectedDefect;
}
function canReturnTo(c){
  if(!c)return false;
  if(publicRoutes.has(c.screen))return !signedIn||!['login','first'].includes(c.screen);
  return signedIn&&c.signedIn&&c.role===role&&c.authEpoch===navigationEpoch
    &&(!caseRoutes.has(c.screen)||canAccessCase(c.selected));
}
function previousNavigationIndex(from=navigationIndex){
  for(let i=from-1;i>=0;i--)if(canReturnTo(navigationEntries[i]))return i;
  return -1;
}
function fallbackRoute(){
  if(screen==='map_model')return workModel.entry?.workspace==='work'?(workModel.entry.context?.screen||'case'):'region';
  if(['login','first','public_map','home'].includes(screen))return 'landing';
  if(screen==='public_bim')return 'public_building';
  if(screen==='public_building')return 'public_map';
  if(screen==='defect')return 'field';
  if(['preview','share'].includes(screen))return 'report';
  if(caseRoutes.has(screen))return screen==='case'?'list':'case';
  if(screen==='candidate')return 'region';
  return signedIn?'home':'landing';
}
function navigationLabel(c){
  const names={landing:'서비스 메인',login:'업무 로그인',first:'계정 이용 안내',home:'내 업무 대시보드',
    list:'노후건축물·점검 현황',public_map:'공개 지도 검색 결과',public_building:'공개 노후건축물 정보',
    public_bim:'공개 3D/BIM',field:'현장조사·결함',case:'점검건 업무 요약',defect:'근거 상세',
    report:'보고서',region:'지도 분석',map_model:'결함 위치와 sBIM 근거',candidate:'후보의 근거·점검'};
  const label=names[c.screen]||explanations[c.screen]?.[0]||'업무 화면';
  return c.screen==='defect'?`${label} · ${c.selectedDefect}`:label;
}
function paintBackNavigation(){
  let bar=document.getElementById('page-navigation');
  if(!bar){bar=document.createElement('div');bar.id='page-navigation';$('#workspace-tabs').after(bar);}
  bar.hidden=screen==='landing';
  if(bar.hidden){bar.innerHTML='';return;}
  const previous=previousNavigationIndex();
  const target=previous>=0?navigationEntries[previous]:{screen:fallbackRoute()};
  bar.innerHTML=`<button id="previous-screen" onclick="previousScreen()" aria-label="이전 화면: ${esc(navigationLabel(target))}">← 이전 화면</button><span>${previous>=0?'돌아갈 곳':'상위 화면'} · ${esc(navigationLabel(target))}</span>`;
}
function rememberNavigation(writeHistory=true){
  if(!renderedNavigation)return;
  const c={...renderedNavigation,scrollY:window.scrollY};
  // These controls update the model without rebuilding the page.
  if(c.screen==='public_bim')Object.assign(c,{publicRotation,publicZoom,publicFloor});
  navigationEntries[navigationIndex]=c;
  if(writeHistory)history.replaceState(historyEnvelope(c),'',`#${c.screen}`);
}
function resetNavigation(){
  navigationSession=Date.now()+Math.random();navigationIndex=0;
  navigationAuth={signedIn,role};
  renderedNavigation=navigationSnapshot();navigationEntries=[renderedNavigation];
  history.replaceState(historyEnvelope(renderedNavigation),'',`#${screen}`);
  paintBackNavigation();
}
render=function(){entryRender();renderedNavigation=navigationSnapshot();paintBackNavigation();};

go=function(route,opts={}){
  if($('#dialog').open)$('#dialog').close();
  rememberDraft();rememberWork();rememberNavigation();
  const outgoing=navigationEntries[navigationIndex];
  if(opts.workContext)applyWorkContext(opts.workContext);
  if(opts.model)workModel=clone(opts.model);
  if(opts.id)selected=opts.id;
  if(!signedIn&&!publicRoutes.has(route)){pendingDestination={screen:route,id:selected};route='login';}
  if(signedIn&&caseRoutes.has(route)&&!canAccessCase(selected)){deniedCaseId=selected;route='access_unavailable';}
  if(navigationAuth.signedIn!==signedIn||navigationAuth.role!==role){
    navigationEpoch++;navigationAuth={signedIn,role};
  }
  screen=route;activeWorkspace=isAnalysisRoute(screen)?'analysis':'work';
  render();window.scrollTo(0,0);
  const next=navigationSnapshot();
  if(!signedIn&&outgoing?.signedIn){
    resetNavigation();
  }else if(opts.replace||sameView(outgoing,next)){
    navigationEntries[navigationIndex]=next;
    history.replaceState(historyEnvelope(next),'',`#${screen}`);
  }else{
    navigationEntries=navigationEntries.slice(0,navigationIndex+1);
    navigationEntries.push(next);navigationIndex++;
    history.pushState(historyEnvelope(next),'',`#${screen}`);
  }
  renderedNavigation=next;paintBackNavigation();
  $('#app').focus({preventScroll:true});rememberWork();persistDemo();
};

function applyNavigation(c){
  if(typeof restoreMapNavigation==='function')restoreMapNavigation(c);
  applyWorkContext(c);publicQuery=c.publicQuery||'';publicFilter=c.publicFilter||'전체';
  publicSelected=c.publicSelected||2;publicRotation=c.publicRotation??32;
  publicZoom=c.publicZoom||1;publicFloor=c.publicFloor||0;
  analysisFilter=c.analysisFilter||'전체';dashboardScope=c.dashboardScope||'mine';
  pendingDestination=c.pendingDestination?clone(c.pendingDestination):null;
  deniedCaseId=c.deniedCaseId||3;
  screen=c.screen;activeWorkspace=isAnalysisRoute(screen)?'analysis':'work';
  render();renderedNavigation={...navigationSnapshot(),scrollY:c.scrollY||0};
  navigationEntries[navigationIndex]=renderedNavigation;
  history.replaceState(historyEnvelope(renderedNavigation),'',`#${screen}`);
  paintBackNavigation();$('#app').focus({preventScroll:true});
  window.scrollTo(0,c.scrollY||0);rememberWork();persistDemo();
}
restoreNavigation=function(c){
  if($('#dialog').open)$('#dialog').close();
  rememberDraft();rememberWork();rememberNavigation(false);
  if(c?.navigationSession===navigationSession&&navigationEntries[c.navigationIndex]){
    const target=navigationEntries[c.navigationIndex];
    if(canReturnTo(target)){navigationIndex=c.navigationIndex;applyNavigation(target);return;}
    const previous=previousNavigationIndex(c.navigationIndex);
    if(previous>=0){history.go(previous-c.navigationIndex);return;}
  }
  // Reloads and account changes cannot revive a previous private session.
  screen=signedIn?'home':'landing';activeWorkspace='work';pendingDestination=null;
  render();window.scrollTo(0,0);resetNavigation();
};
function previousScreen(){
  rememberDraft();rememberWork();rememberNavigation();persistDemo();
  const previous=previousNavigationIndex();
  if(previous>=0)history.go(previous-navigationIndex);
  else go(fallbackRoute(),{replace:true});
}

// A standalone gallery frame starts with a meaningful parent, not the previous sample.
const previewTour=showTourStep;
showTourStep=function(i){previewTour(i);resetNavigation();};
resetNavigation();paintBackNavigation();
