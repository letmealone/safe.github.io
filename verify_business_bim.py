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

cmd('Page.bringToFront');cmd('Page.navigate',{'url':url});time.sleep(.4)
cmd('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1000,'deviceScaleFactor':1,'mobile':False})
ev("resetDemo('official');enterLogin();login();openWorkspace('analysis');chooseMapArea('goyang');selectMapBuilding(1);openWorkModel(1);modelMove('angle',56);go('list');query='주민';go('list')")
mapBefore=ev('clone(mapViews)')
check("document.querySelectorAll('[data-bim-building]').length===1",'점검 현황은 검색된 업무 행에 BIM 진입 제공')
ev('window.scrollTo(0,180)');beforeScroll=ev('scrollY')
press('[data-bim-building="2"]')
check("screen==='map_model'&&selected===2&&workModel.round==='2026'&&activeWorkspace==='work'",'점검 현황의 BIM은 같은 건물·회차로 내 업무 안에서 열림')
check("document.querySelector('.model-page-head').innerText.includes('점검 현황으로 돌아가기')",'BIM의 복귀 버튼이 점검 현황을 명시')
click('1층');check("workModel.defect==='F-01'&&activeWorkspace==='work'",'층·결함 조작 후에도 업무 BIM 맥락 유지')
click('점검 현황으로 돌아가기');time.sleep(.15)
check("screen==='list'&&query==='주민'&&document.querySelectorAll('[data-bim-building]').length===1",'현황 복귀 시 검색조건과 목록 유지')
# Mouse activation scrolls the source control into view; the explicit return restores that source view.
check("JSON.stringify(mapViews)==="+json.dumps(json.dumps(mapBefore,ensure_ascii=False,separators=(',',':'))),'업무 BIM 탐색이 별도 지도 조건을 변경하지 않음')
ev("openCase(2)");press('.case-bim-entry [data-bim-building="2"]')
check("workModel.entry.context.screen==='case'&&activeWorkspace==='work'",'점검 상세에서도 같은 BIM으로 직접 진입')
click('점검 상세로 돌아가기');time.sleep(.15)
check("screen==='case'&&selected===2",'점검 상세로 복귀')
ev("go('histories')")
check("document.querySelectorAll('[data-bim-building=\"2\"]').length===2",'점검 이력은 이전·이번 회차 BIM을 각각 제공')
press('[data-bim-building="2"][data-bim-round="2025"]')
check("screen==='map_model'&&workModel.round==='2025'&&activeWorkspace==='work'&&document.querySelector('#model-round').value==='2025'",'이력의 2025년 BIM을 누르면 해당 회차 기록으로 진입')
click('F-01 · 1층 계단실 / 벽')
check("document.querySelector('.model-evidence').innerText.includes('2.2mm')&&!document.querySelector('.model-evidence').innerText.includes('2.0mm')",'이력 BIM 근거는 현재값과 섞이지 않음')
# Keep both work BIM and the previous map BIM available in their own tabs.
click('지도 분석')
check("screen==='map_model'&&selected===1&&workModel.angle===56&&activeWorkspace==='analysis'&&!workModel.entry",'지도 탭은 기존 다른 건물·시점을 복원')
click('내 업무')
check("screen==='map_model'&&selected===2&&workModel.round==='2025'&&workModel.defect==='F-01'&&activeWorkspace==='work'",'내 업무 탭은 이전 회차 BIM과 선택 근거를 복원')
click('점검 이력으로 돌아가기');time.sleep(.15)
check("screen==='histories'",'탭을 오간 뒤에도 원래 이력으로 복귀')
ev("go('history',{id:2})");press('[data-bim-round="2025"]')
check("workModel.entry.context.screen==='history'&&workModel.round==='2025'",'회차 비교 상세에서 과거 BIM 진입')
click('회차·버전 이력으로 돌아가기');time.sleep(.15)
ev("state.version=2;state.phase='resubmitted';state.snapshots.push({version:2,captions:{'F-03':'[가상] v2 다른 설명'}});go('history',{replace:true});document.querySelector('.history-bim-versions').open=true")
press('[data-bim-version="1"]')
check("modelVersion()===1&&workModel.round==='2026'&&document.querySelector('.model-evidence').innerText.includes('옥상 난간 촬영 위치 기록')&&!document.querySelector('.model-evidence').innerText.includes('v2 다른 설명')",'공유 v1 BIM은 해당 원문 근거를 유지')
click('회차·버전 이력으로 돌아가기');time.sleep(.15)
press('.history-bim-rounds [data-bim-round="2026"]')
check("workModel.version==='current'&&modelVersion()===2",'이번 회차 BIM은 현재 버전의 기록으로 진입')
click('회차·버전 이력으로 돌아가기');time.sleep(.15)
press('[data-bim-round="2025"]');click('로그아웃')
cmd('Page.navigate',{'url':url});time.sleep(.3);ev("enterLogin();pickRole('official');login();continueWork()")
check("screen==='map_model'&&activeWorkspace==='work'&&workModel.round==='2025'&&workModel.entry.context.screen==='history'",'재로그인 후 최근 업무 BIM의 회차·진입 화면 복원')
click('회차·버전 이력으로 돌아가기');time.sleep(.15)
check("screen==='history'&&selected===2",'새 브라우저 탐색 이력에서도 원래 업무로 복귀')
ev("go('defect',{id:2});selectedDefect='F-02';go('defect',{replace:true})");click('3D·부재 위치')
check("screen==='map_model'&&activeWorkspace==='work'&&workModel.defect==='F-02'&&workModel.floor===2",'현장 근거의 기존 3D 버튼도 같은 결함·업무 맥락 유지')
click('근거 상세로 돌아가기');time.sleep(.15)
check("screen==='defect'&&selectedDefect==='F-02'",'근거 상세의 선택 결함으로 복귀')
ev("go('list');query='';dashboardScope='all';go('list')")
check("document.querySelector('.bim-unavailable')&&!document.querySelector('[data-bim-building=\"3\"]')",'BIM 없는 건물은 미등록과 기존 업무 경로를 표시')
press('[data-bim-building="1"]')
check("selected===1&&document.querySelector('#model-version').disabled&&!document.querySelector('.model-marker')",'다른 건물 BIM에 주민회관 결함이나 보고서가 섞이지 않음')
ev("resetDemo('agency');enterLogin();login();openCaseModel(3)")
check("screen==='access_unavailable'&&!document.querySelector('#work-model-canvas')",'업무 BIM 직접 호출도 기관 권한 범위 적용')
for width,height in [(1366,768),(390,844)]:
 cmd('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':False})
 for i in range(42,47):
  ev('showTourStep('+str(i)+');window.scrollTo(0,0)')
  check('document.documentElement.scrollWidth<=innerWidth',str(width)+'px 업무 BIM 단계 '+str(i)+' 가로 넘침 없음')
cmd('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1000,'deviceScaleFactor':1,'mobile':False})
cmd('Page.navigate',{'url':url});time.sleep(.3)
(root/'business_bim_validation.json').write_text(json.dumps({'checks':checks},ensure_ascii=False,indent=2));print(json.dumps({'checks':len(checks),'result':'pass'},ensure_ascii=False));ws.close()
