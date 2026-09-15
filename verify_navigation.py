"""Exercise only the local fictional prototype in visible Chrome."""
from pathlib import Path
import json,time,base64
import requests,websocket
root=Path(__file__).resolve().parent
url=(root/'workflow.html').as_uri()
tabs=requests.get('http://127.0.0.1:9335/json',timeout=10).json()
tab=next(t for t in tabs if t.get('type')=='page' and t.get('url','').startswith(url))
ws=websocket.create_connection(tab['webSocketDebuggerUrl'],origin='http://localhost:9335',timeout=25)
seq=0
checks=[]
def cmd(method,params=None):
 global seq
 seq+=1;ws.send(json.dumps({'id':seq,'method':method,'params':params or {}}))
 while True:
  r=json.loads(ws.recv())
  if r.get('id')==seq:
   if 'error' in r:raise RuntimeError(r['error'])
   return r.get('result',{})
def ev(code):
 r=cmd('Runtime.evaluate',{'expression':code,'returnByValue':True,'awaitPromise':True,'userGesture':True})
 if 'exceptionDetails' in r:raise RuntimeError(r['exceptionDetails'])
 return r.get('result',{}).get('value')
def check(code,label):
 assert ev('Boolean('+code+')'),label
 checks.append({'check':label,'result':'pass'});print('PASS '+label,flush=True)
def click(label):
 ev('(()=>{const b=[...document.querySelectorAll("button")].find(b=>b.textContent.trim()==='+json.dumps(label)+'&&!b.disabled&&b.getClientRects().length);if(!b)throw new Error("button missing: "+'+json.dumps(label)+');b.click();})()')
 time.sleep(.08)
def setvalue(selector,value):
 ev('(()=>{const e=document.querySelector('+json.dumps(selector)+');e.value='+json.dumps(value)+';e.dispatchEvent(new Event("input",{bubbles:true}));})()')
def shot(name):
 ev('clearTimeout(window.toastTimer);document.querySelector("#toast").style.display="none";window.scrollTo(0,0)')
 time.sleep(.1)
 r=cmd('Page.captureScreenshot',{'format':'png'});(root/'mockups'/name).write_bytes(base64.b64decode(r['data']))
cmd('Page.bringToFront');cmd('Page.navigate',{'url':url});time.sleep(.4)
ev("resetDemo('agency')")
check("document.querySelector('.entry-grid').firstElementChild.classList.contains('work-entry')",'업무 진입이 DOM·키보드·모바일 순서의 첫 경로')
check("document.querySelector('.work-entry').getBoundingClientRect().left < document.querySelector('.public-entry').getBoundingClientRect().left",'데스크톱에서 업무가 왼쪽, 공개 조회가 오른쪽')
check("document.title.includes('노후건축물 안전진단')&&document.querySelector('h1').innerText.includes('노후건축물')&&document.querySelector('.public-entry').innerText.includes('GIS+sBIM 기반 노후건축물 안전진단 정보조회 서비스')",'서비스 제목·주 대상·보조 서비스 명칭 일치')
setvalue('#entry-search','안전로20');ev('document.querySelector(".public-search").requestSubmit()')
start_index=ev('navigationIndex')
ev("publicFilter='3D 있음';go('public_map')")
check('navigationIndex==='+str(start_index),'동일 화면의 조건 변경으로 뒤로가기 단계가 늘지 않음')
cmd('Emulation.setDeviceMetricsOverride',{'width':1440,'height':768,'deviceScaleFactor':1,'mobile':False})
ev('window.scrollTo(0,170)');time.sleep(.1);offset=ev('window.scrollY')
ev('choosePublicBuilding(2)');click('공개 3D/BIM 열기')
click('← 이전 화면');time.sleep(.15)
check("screen==='public_building'&&publicSelected===2",'공개 BIM에서 바로 이전 상세로 복귀')
click('← 이전 화면');time.sleep(.15)
check("screen==='public_map'&&publicQuery==='안전로20'&&publicFilter==='3D 있음'&&publicResults().length===1",'상세에서 검색어·조건·결과가 같은 공개 지도로 복귀')
check('Math.abs(window.scrollY-'+str(offset)+')<3','검색 결과의 세로 스크롤 위치 복원')
ev("choosePublicBuilding(2);go('public_bim');publicRotation=128;publicFloor=2;publicZoom=1.3;drawPublicModel();go('public_building')")
click('← 이전 화면');time.sleep(.15)
check("screen==='public_bim'&&publicRotation===128&&publicFloor===2&&publicZoom===1.3",'BIM 재방문 시 회전·확대·선택 층 유지')
ev("go('public_building');choosePublicBuilding(1)")
click('← 이전 화면');time.sleep(.15)
check("screen==='public_building'&&publicSelected===2",'동일 상세 화면의 서로 다른 대상도 구분하여 복귀')
ev("logoutDemo();resetDemo('agency');enterLogin();login();go('list')")
setvalue('#search-filter','주민');click('조회');ev('window.scrollTo(0,140)');time.sleep(.1)
click('업무 건 열기');click('현장조사·결함');click('확인 항목 열기')
setvalue('#evidence-caption','[가상] 뒤로가기 후에도 유지할 F-03 초안')
ev("selectedDefect='F-01';go('defect')")
click('← 이전 화면');time.sleep(.15)
check("screen==='defect'&&selectedDefect==='F-03'&&document.querySelector('#evidence-caption').value.includes('유지할 F-03')",'다른 결함을 본 뒤 이전 근거의 대상·초안 복원')
click('← 이전 화면');time.sleep(.15)
check("screen==='field'&&selected===2",'근거 상세에서 이전 현장조사 화면으로 복귀')
click('← 이전 화면');time.sleep(.15);click('← 이전 화면');time.sleep(.15)
check("screen==='list'&&query==='주민'&&document.querySelector('#search-filter').value==='주민'",'점검건을 닫은 뒤 업무 목록 검색조건 유지')
ev("go('report',{id:2})");setvalue('#opinion','[가상] 이전 화면 이동 전 보고서 초안')
click('지도 분석');click('← 이전 화면');time.sleep(.15)
check("screen==='report'&&document.querySelector('#opinion').value.includes('보고서 초안')",'이전 화면 버튼으로 분석에서 작성 중인 보고서 복귀')
ev("go('preview');history.back()");time.sleep(.2)
check("screen==='report'&&document.querySelector('#opinion').value.includes('보고서 초안')",'브라우저 뒤로가기도 동일한 보고서 초안 유지')
ev('history.forward()');time.sleep(.2)
check("screen==='preview'",'브라우저 앞으로가기와 화면 내 뒤로가기 호환')
click('로그아웃');ev('history.back()');time.sleep(.2)
check("!signedIn&&screen==='landing'&&!document.querySelector('#opinion')",'로그아웃 후 이전 로그인 세션의 업무 접근 차단')
cmd('Page.navigate',{'url':url+'?tour=15'});time.sleep(.4)
check("screen==='defect'&&document.querySelector('#previous-screen')",'단독 단계 링크에서도 이전 화면 버튼 제공')
click('← 이전 화면');time.sleep(.15)
check("screen==='field'&&location.href.startsWith('file:')",'직접 열린 상세는 앱 안의 상위 화면으로 이동')
# Navigation restores a view, never an obsolete business-state snapshot.
ev("showTourStep(25);go('history');state.phase='complete';state.reviewChecked=true")
click('← 이전 화면');time.sleep(.15)
check("state.phase==='complete'&&state.version===2",'뒤로가기로 이미 처리된 업무 상태·버전을 취소하지 않음')
cmd('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':False})
ev('showTourStep(0)')
check("document.querySelector('.work-entry').getBoundingClientRect().top < document.querySelector('.public-entry').getBoundingClientRect().top && document.documentElement.scrollWidth<=innerWidth",'390px 모바일에서도 업무가 먼저 표시되고 가로 넘침 없음')
cmd('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1000,'deviceScaleFactor':1,'mobile':False})
# Leave the same useful fictional draft for the user to resume.
cmd('Page.navigate',{'url':url});time.sleep(.3)
ev("resetDemo('agency');enterLogin();login();listFilter='소규모 노후건축물 점검';query='주민';go('report',{id:2});document.querySelector('#opinion').value='[가상 예시] 이전에 정리하던 종합 의견입니다. 현장 근거 확인 후 이어서 작성합니다.';rememberDraft();persistDemo();logoutDemo();")
(root/'navigation_validation.json').write_text(json.dumps({'checks':checks},ensure_ascii=False,indent=2))
print(json.dumps({'checks':len(checks),'result':'pass'},ensure_ascii=False));ws.close()
