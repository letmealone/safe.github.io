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
def press(selector):
 pos=ev('(()=>{const e=document.querySelector('+json.dumps(selector)+');if(!e)throw Error("missing selector");e.scrollIntoView({block:"center",behavior:"instant"});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()')
 cmd('Input.dispatchMouseEvent',{'type':'mouseMoved',**pos});cmd('Input.dispatchMouseEvent',{'type':'mousePressed','button':'left','clickCount':1,**pos});cmd('Input.dispatchMouseEvent',{'type':'mouseReleased','button':'left','clickCount':1,**pos});time.sleep(.12)
cmd('Page.bringToFront');cmd('Page.navigate',{'url':url});time.sleep(.5)
cmd('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1000,'deviceScaleFactor':1,'mobile':False})
ev("resetDemo('official');openPublicMap()")
check("screen==='public_map'&&!signedIn&&mapView().area==='kr'&&document.querySelectorAll('.gis-region').length===17",'비로그인 지도는 남한 17개 시도에서 시작')
for area in ['KR-41','goyang','ilsaneast','janghang1']:
 ev('chooseMapArea('+json.dumps(area)+')')
 check('mapView().area==='+json.dumps(area),'클릭 탐색 단계 '+area)
check("gisResults().length===1&&gisResults()[0].id===2",'행정동 선택 시 지도·목록이 같은 대상 집합')
press('.gis-pin')
check("mapView().pick===2&&document.querySelector('.gis-summary').innerText.includes('행정구역: 장항1동 / 건축물 동: 본동')",'지도 핀 실클릭으로 동을 구분한 요약 열기')
check("!document.querySelector('.gis-summary').innerText.includes('F-03')&&!document.querySelector('.model-marker')",'공개 요약에는 비공개 결함 근거 미노출')
click('노후건축물 정보 상세');check("document.querySelector('#app').innerText.includes('2025년 1회차 · 공개 요약 예시')&&!document.querySelector('#app').innerText.includes('공개 점검 요약 미등록')",'공개 지도와 상세가 같은 회차의 공개 기록 표시')
click('← 이전 화면');time.sleep(.12)
click('공개 3D/BIM 열기');check("screen==='public_bim'&&!signedIn&&!document.querySelector('.model-marker')",'공개 모델은 외형만 제공')
click('← 이전 화면');time.sleep(.15)
check("screen==='public_map'&&mapView().area==='janghang1'&&mapView().pick===2",'공개 모델에서 원래 지도·선택 요약 복귀')
click('상위 지역으로');check("mapView().area==='ilsaneast'",'상위 지역 버튼은 공간 범위를 한 단계 확장')
ev("chooseMapArea('KR-11')");check("gisResults().length===0&&document.querySelector('.gis-list').innerText.includes('가상 사례가 없습니다')",'사례가 없는 시도도 열리고 자료 없음 안내')
setvalue('#public-search','안전로20');click('검색')
check("mapView().area==='kr'&&gisResults().length===1&&gisResults()[0].id===2",'주소 검색으로 지역 단계 건너뛰기')
check("mapView().viewport.w>=12&&document.querySelectorAll('.gis-region').length>=3",'한 건 검색도 주변 행정구역을 알아볼 수 있는 범위 유지')
initial=ev('clone(mapView().viewport)');scope=ev('({area:mapView().area,ids:gisResults().map(x=>x.id),query:publicQuery})')
pos=ev('(()=>{const r=document.querySelector("#gis-svg").getBoundingClientRect();return {x:r.x+r.width*.5,y:r.y+r.height*.5}})()')
cmd('Input.dispatchMouseEvent',{'type':'mouseWheel',**pos,'deltaX':0,'deltaY':-150});time.sleep(.2)
check('mapView().viewport.w<'+str(initial['w']),'실제 휠 이벤트로 지도 확대')
check('JSON.stringify({area:mapView().area,ids:gisResults().map(x=>x.id),query:publicQuery})==='+json.dumps(__import__('json').dumps(scope,ensure_ascii=False,separators=(',',':'))),'휠 확대가 검색어·조회 지역·결과를 바꾸지 않음')
click('이 화면 범위에서 조회');before=ev('gisResults().map(x=>x.id)');ev('panMap(.7,0)')
check('JSON.stringify(gisResults().map(x=>x.id))==='+json.dumps(json.dumps(before,separators=(',',':'))),'화면 범위 조회 후 지도 이동도 확정된 조회 범위를 유지')
check("document.querySelector('#gis-result-count').innerText===`조회 전체 ${gisResults().length}건 · 현재 화면 ${gisResults().filter(b=>pointInViewport(mapMeta[b.id].point,mapView().viewport)).length}건`",'이동 후 전체 조회 수와 화면 안 대상 수 구분 갱신')
ev("resetDemo('official');enterLogin();login();openWorkspace('analysis')")
check("screen==='region'&&mapView().area==='goyang'&&gisResults().length===3",'공무원은 관할 고양시에서 지도 시작')
ev("chooseMapArea('ilsaneast');selectMapBuilding(2);mapZoom(.85)");context=ev('clone(mapView())')
click('결함 위치 · sBIM 보기')
check("screen==='map_model'&&selected===2&&document.querySelectorAll('.model-marker').length===3",'업무 요약에서 결함 매핑 sBIM 열기')
check("document.querySelector('.model-evidence svg').textContent.includes('옥상 평면 예시')",'옥상 결함의 근거 도식도 옥상 위치로 일치')
click('1층');check("workModel.defect==='F-01'&&document.querySelector('.model-evidence h2').innerText.includes('1층')&&!document.querySelector('.model-evidence h2').innerText.includes('옥상')",'층을 바꾸면 해당 층의 모델·근거를 함께 선택')
click('전체')
press('.model-marker[aria-label^="F-01"]')
check("workModel.defect==='F-01'&&workModel.floor===1&&document.querySelector('.model-evidence h2').innerText.includes('F-01')",'모델 표시 실클릭으로 같은 결함·층·근거 선택')
click('F-02 · 2층 복도 천장 / 슬래브')
check("workModel.defect==='F-02'&&document.querySelector('.model-marker.selected').getAttribute('aria-label').startsWith('F-02')",'결함 목록 선택도 같은 모델 위치 강조')
setvalue('#model-round','2025');ev("document.querySelector('#model-round').dispatchEvent(new Event('change',{bubbles:true}))")
check("workModel.round==='2025'&&document.querySelector('.model-evidence').innerText.includes('0.4mm')&&!document.querySelector('.model-evidence').innerText.includes('0.3mm')",'지난 회차 선택 시 해당 회차 관찰값과 기록 표시')
press('#model-compare');check("document.querySelector('.model-compare').innerText.includes('0.3mm')&&document.querySelector('.model-compare').innerText.includes('0.4mm')",'회차 비교를 켜면 이전·이번 관찰값을 구분하여 제공')
click('지도로 돌아가기')
check("screen==='region'&&JSON.stringify(mapView())==="+json.dumps(json.dumps(context,ensure_ascii=False,separators=(',',':'))),'sBIM을 닫으면 같은 지역·시점·검색·건물 요약 복원')
click('결함 위치 · sBIM 보기');click('모델 로딩 실패 예시')
check("document.querySelector('.model-missing')&&!document.querySelector('.model-marker')",'모델 로딩 실패에도 기존 기록 경로 제공')
click('가상 모델 다시 열기');check("document.querySelector('#work-model-canvas svg')",'모델 실패 예시에서 다시 열기 가능')
click('지도로 돌아가기');ev('selectMapBuilding(3)');click('모델 없는 자료 확인')
check("selected===3&&document.querySelector('.model-missing')&&document.querySelector('#app').innerText.includes('기존 점검자료 보기')",'모델 미등록 건물도 업무 자료 확인 가능')
# Capture selected model and map environment across sign out/reload.
ev("returnModelMap();chooseMapArea('ilsaneast');selectMapBuilding(2);openWorkModel(2);workModel.angle=112;workModel.defect='F-01';workModel.round='2025';go('map_model',{replace:true});logoutDemo()")
cmd('Page.navigate',{'url':url});time.sleep(.4);ev("enterLogin();pickRole('official');login();openWorkspace('analysis')")
check("screen==='map_model'&&selected===2&&workModel.angle===112&&workModel.round==='2025'&&workModel.defect==='F-01'",'재로그인 후 지도 탭의 모델·회차·선택 근거 복원')
ev("resetDemo('agency');enterLogin();login();openWorkspace('analysis')")
check("gisResults().length===2&&!gisResults().some(b=>b.id===3)",'전문기관 지도는 기관 권한의 두 건만 조회')
ev('openWorkModel(3)');check("screen==='access_unavailable'&&!document.querySelector('#work-model-canvas')",'모델 직접 호출에도 담당 범위 밖 업무 차단')
ev("go('region');selectMapBuilding(2);openWorkModel(2)")
check("document.querySelector('.model-evidence').innerText.includes('대략 위치')",'확인 전 위치는 정확한 매핑으로 표시하지 않음')
# Shared versions keep their own text even after a later correction.
ev("state=initialState('official');state.version=2;state.phase='resubmitted';state.evidence=true;state.snapshots.push({version:2,opinion:'v2',captions:{'F-03':'[가상] v2 별도 설명'}});workModel.defect='F-03';workModel.version='1';workModel.round='2026';go('map_model',{replace:true})")
check("!document.querySelector('.model-evidence').innerText.includes('v2 별도 설명')&&document.querySelector('.model-evidence').innerText.includes('옥상 난간 촬영 위치 기록')",'sBIM에서 공유 v1을 선택하면 보완 v2와 원문 구분')
ev("returnModelMap();resetMapConditions();chooseMapArea('goyang');selectMapBuilding(1);openWorkModel(1)")
check("selected===1&&document.querySelector('.model-floor-tabs').innerText.includes('3층')&&document.querySelector('#model-version').disabled&&document.querySelector('#model-version').innerText.includes('연계 미확인')",'다른 건물의 실제 예시 층수·미연계 보고서 상태를 구분')
ev("returnModelMap();mapView().viewport=fitMapBounds(MAP_REGIONS.goyang.bounds);refreshMap()")
rect=ev('(()=>{const r=document.querySelector("#gis-svg").getBoundingClientRect();return {x:r.x+r.width*.4,y:r.y+r.height*.4}})()');oldx=ev('mapView().viewport.x')
cmd('Input.dispatchMouseEvent',{'type':'mouseMoved',**rect});cmd('Input.dispatchMouseEvent',{'type':'mousePressed','button':'left','clickCount':1,**rect});cmd('Input.dispatchMouseEvent',{'type':'mouseMoved','button':'left','buttons':1,'x':rect['x']+65,'y':rect['y']+15});cmd('Input.dispatchMouseEvent',{'type':'mouseReleased','button':'left','clickCount':1,'x':rect['x']+65,'y':rect['y']+15});time.sleep(.12)
check('Math.abs(mapView().viewport.x-'+str(oldx)+')>.001', '구역 위 실드래그로 지도 이동')
check('performance.getEntriesByType("resource").filter(r=>/^https?:/.test(r.name)).length===0','지도·sBIM 실행은 외부 서버 요청 없이 동작')
for width,height in [(1366,768),(390,844)]:
 cmd('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':False})
 for i in [1,33,34,35,36,37,38,39,40,41]:
  ev('showTourStep('+str(i)+');window.scrollTo(0,0)')
  if width==1366 and i==38:check("[...document.querySelectorAll('.model-defect-list button')].every(b=>b.getBoundingClientRect().bottom<innerHeight)",'업무용 1366×768 첫 화면에서 결함 세 항목 선택 가능')
  check('document.documentElement.scrollWidth<=innerWidth',str(width)+'px 지도·모델 단계 '+str(i)+' 가로 넘침 없음')
cmd('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1000,'deviceScaleFactor':1,'mobile':False})
cmd('Page.navigate',{'url':url});time.sleep(.3)
(root/'map_validation.json').write_text(json.dumps({'checks':checks},ensure_ascii=False,indent=2));print(json.dumps({'checks':len(checks),'result':'pass'},ensure_ascii=False));ws.close()
