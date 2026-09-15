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
cmd('Page.bringToFront');assert ev('location.href').startswith(url)
cmd('Page.navigate',{'url':url});time.sleep(.5)
ev("resetDemo('agency')")
check("screen==='landing'&&!signedIn&&document.body.innerText.includes('노후건축물 정보조회')",'공통 메인의 공개 조회·업무 진입')
setvalue('#entry-search','안전로20');ev('document.querySelector(".public-search").requestSubmit()')
check("screen==='public_map'&&!signedIn&&publicResults().length===1",'비로그인 주소 검색과 같은 조건의 지도·목록')
ev('document.querySelector(".public-result").click()');click('공개 3D/BIM 열기')
check("screen==='public_bim'&&!signedIn&&document.querySelector('#public-model svg')",'비로그인 공개 건물에서 3D 열람')
a=ev('document.querySelector("#public-model").innerHTML');ev('publicRotation=128;publicFloor=2;drawPublicModel()');b=ev('document.querySelector("#public-model").innerHTML');assert a!=b
check("document.querySelector('#public-floor-info').innerText.includes('2층 선택')",'공개 모델 회전·층 선택 반영')
shot('v2_public_bim_interaction.png')
click('노후건축물 정보');click('업무시스템 로그인');check("screen==='login'&&pendingDestination.id===2",'공개 건물 상단 로그인도 선택한 건 유지')
click('지자체 담당자');click('로그인 후 메인화면 보기')
check("signedIn&&screen==='case'&&selected===2",'로그인 후 원래 건축물의 업무로 연결')
ev("logoutDemo();resetDemo('agency');enterLogin();login();")
check("signedIn&&screen==='home'&&role==='agency'&&state.phase==='draft'",'일반 업무 로그인은 역할별 대시보드')
click('기관 전체');check('workspaceRows().length===2','기관 전체 조회범위 반영')
click('내 담당');ev("go('reports')")
check("document.querySelectorAll('tbody tr').length===1&&!document.querySelector('#app').innerText.includes('중앙상가')",'보고서 목록도 내 담당 범위 적용')
ev("go('histories')")
check("document.querySelectorAll('tbody tr').length>0&&[...document.querySelectorAll('tbody tr')].every(r=>r.innerText.includes('예시 주민회관'))",'회차별 이력 목록도 내 담당 건물 범위 적용')
ev("choosePublicBuilding(3);enterLogin({screen:'case',id:3})")
check("screen==='access_unavailable'&&!document.querySelector('.casehead')",'이미 로그인한 기관의 범위 밖 업무 열람 차단')
click('공개 정보 계속 보기');click('3D로 건물 보기')
check("screen==='public_bim'&&document.querySelector('#app').innerText.includes('공개 3D 자료가 아직 없습니다.')",'모델 없는 공개 건물의 기본정보 경로 유지')
ev("go('list',{id:2});")
setvalue('#type-filter','소규모 노후건축물 점검');setvalue('#search-filter','주민');click('조회');click('업무 건 열기');click('현장조사·결함');click('확인 항목 열기')
setvalue('#evidence-caption','[가상] F-03 전용 위치 설명')
ev("selectedDefect='F-01';go('defect')")
check("!document.querySelector('#evidence-caption').value.includes('F-03 전용')",'결함별 초안이 다른 근거에 섞이지 않음')
ev("selectedDefect='F-03';go('defect')")
check("document.querySelector('#evidence-caption').value.includes('F-03 전용')",'원래 근거의 초안 복원')
ev("document.querySelector('#evidence-check').click()")
click('확인 내용 반영');click('이번 회차 자료 확인 마침')
check("document.querySelector('[onclick=\"go(\\'share\\')\"]').disabled",'남은 의견이 있는 보고서의 공유 비활성화')
setvalue('#opinion','[가상] 재접속 복원 확인용 의견 초안')
click('지도 분석');setvalue('#analysis-filter','점검기록 있음');click('분석 조건 적용');click('내 업무')
check("screen==='report'&&selected===2&&document.querySelector('#opinion').value.includes('재접속 복원')",'지도 탭 왕복에서 건·회차·작성 초안 유지')
click('지도 분석');check("screen==='region'&&analysisFilter==='점검기록 있음'",'지도 분석 조건 별도 유지')
click('로그아웃');check("screen==='landing'&&!signedIn&&!document.querySelector('#app').innerText.includes('재접속 복원 확인용')",'로그아웃 후 업무 내용이 보이지 않는 공통 메인')
ev('history.back()');time.sleep(.2)
check("!signedIn&&!document.querySelector('#analysis-filter')",'로그아웃 후 뒤로 가기에서 업무 화면 노출 방지')
# Simulate closing/reopening the page, then normal sign-in.
cmd('Page.navigate',{'url':url});time.sleep(.4)
ev("enterLogin();pickRole('agency');login();")
check("screen==='home'&&restoredLogin&&query==='주민'&&listFilter==='소규모 노후건축물 점검'",'새로고침·재로그인 후 대시보드와 이전 조회조건 복원')
check("document.querySelector('#app').innerText.includes('현재 확인할 변화·요청')",'복원된 조회조건 밖의 현재 요청도 대시보드에 표시')
click('최근 작업 이어가기')
check("screen==='report'&&document.querySelector('#opinion').value.includes('재접속 복원')",'재로그인 후 최근 보고서의 초안 이어쓰기')
click('의견 정리 반영');click('공유 전 확인');ev("document.querySelector('#share-check').click()");click('v1 결과 공유')
click('공무원 검토로 이어보기');click('보완 요청 작성');click('보완 요청 확정');click('기관 보완 응답으로 이어보기');ev("document.querySelector('#reply-check').click()");click('v2 보완 결과 공유');click('공무원 재검토로 이어보기');ev("document.querySelector('#review-check').click()");click('결과 검토 완료')
check("state.phase==='complete'&&state.version===2&&state.snapshots.length===2&&state.snapshots[0].captions['F-03']!==state.snapshots[1].captions['F-03']",'기존 v1 공유→보완→v2 재검토 완주와 원문 보존')
completed=ev('({phase:state.phase,version:state.version,snapshots:state.snapshots,events:state.events})')
check("document.querySelector('#app').innerText.includes('별도 확인')",'내부 검토 완료와 BLCM 처리 상태 구분')
check('performance.getEntriesByType("resource").filter(r=>/^https?:/.test(r.name)).length===0','가상 시안의 외부 리소스 요청 없음')
# Preserve a useful local draft scenario for review; export preview does not write it.
ev("resetDemo('agency');enterLogin();login();listFilter='소규모 노후건축물 점검';query='주민';go('report',{id:2});document.querySelector('#opinion').value='[가상 예시] 이전에 정리하던 종합 의견입니다. 현장 근거 확인 후 이어서 작성합니다.';rememberDraft();persistDemo();logoutDemo();")
(root/'entry_validation.json').write_text(json.dumps({'checks':checks,'completed_flow':completed},ensure_ascii=False,indent=2))
print(json.dumps({'checks':len(checks),'result':'pass'},ensure_ascii=False),flush=True)
ws.close()
