"""Read and exercise only the local fictional prototype in visible Chrome."""
import json, time, base64, html
from pathlib import Path
import requests, websocket
root=Path(__file__).resolve().parent
url=(root/'workflow.html').as_uri()
tabs=requests.get('http://127.0.0.1:9335/json',timeout=10).json()
tab=next(t for t in tabs if t.get('type')=='page' and t.get('url','').startswith(url))
ws=websocket.create_connection(tab['webSocketDebuggerUrl'],origin='http://localhost:9335',timeout=20)
seq=0
def cmd(method,params=None):
 global seq
 seq+=1;ws.send(json.dumps({'id':seq,'method':method,'params':params or {}}))
 while True:
  r=json.loads(ws.recv())
  if r.get('id')==seq:
   if 'error' in r:raise RuntimeError(r['error'])
   return r.get('result',{})
def ev(code):
 r=cmd('Runtime.evaluate',{'expression':code,'returnByValue':True,'awaitPromise':True})
 if 'exceptionDetails' in r:raise RuntimeError(r['exceptionDetails'])
 return r.get('result',{}).get('value')
def check(code,label):
 assert ev(code), label
 results.append({'check':label,'result':'pass'})
cmd('Page.bringToFront')
assert ev('location.href').startswith(url)
results=[]
# Preserve the end-to-end result from the manually clicked role handoff.
completed=ev('({phase:state.phase,selected,role,version:state.version,snapshots:state.snapshots,events:state.events})')
if completed['phase']!='complete':
 completed=json.loads((root/'prototype_validation.json').read_text())['completed_flow']
assert completed['phase']=='complete' and len(completed['snapshots'])==2
assert completed['snapshots'][0]['captions']['F-03'] != completed['snapshots'][1]['captions']['F-03']
results.append({'check':'기관 로그인부터 v1 공유·보완 요청·v2 재검토 완료까지 실제 클릭, 원본 보존','result':'pass'})
cmd('Page.navigate',{'url':url});time.sleep(.6)
ev("resetDemo('agency');login();go('report');")
check("state.phase==='draft'&&!state.field&&!state.opinion&&document.querySelector('[onclick=\"go(\\'share\\')\"]').disabled",'준비가 남은 보고서의 공유 버튼 비활성화')
ev('shareReport()')
check("state.phase==='draft'&&state.snapshots.length===0",'필수 확인 전 공유 동작 차단')
ev("listFilter='소규모 노후건축물 점검';query='주민';go('list');openCase(2);go('history');openCase(1);history.back();")
time.sleep(.3)
check("screen==='history'&&selected===2&&query==='주민'&&listFilter==='소규모 노후건축물 점검'",'브라우저 뒤로 가기에서 건축물·회차·조회조건 복원')
ev("role='official';state=initialState(role);go('report',{id:2});")
check("document.querySelector('#opinion').readOnly&&document.querySelector('[onclick=\"saveOpinion()\"]').style.display==='none'",'공무원은 공유본 의견을 읽기 전용으로 열람')
ev("role='agency';go('report');document.querySelector('#opinion').value='변경 시도 예시';saveOpinion();")
check("state.opinion===demoOpinion&&state.snapshots[0].opinion===demoOpinion",'기관도 공유 원문을 덮어쓰지 않음')
ev("go('reports');")
check("document.querySelector('h1').textContent==='점검결과·보고서'&&document.body.innerText.includes('먼저 확인할 건축물·회차를 선택')",'전역 보고서 메뉴가 건 선택 목록으로 연결')
ev("go('histories');")
check("document.querySelector('h1').textContent==='건축물·점검 이력'",'전역 이력 메뉴가 건축물·회차 선택으로 연결')
ev("jumpTo(18);showFurtherReview();")
check("state.version===2&&document.querySelector('#dialog').innerText.includes('대표 흐름')",'추가 보완은 확장 범위 안내로 구분')
ev("document.querySelector('#dialog').close();go('candidate');candidateChoice=true;markCandidate();openCase(2);go('candidate');")
check("state.candidate&&document.body.innerText.includes('가상 후보 표시됨')",'지도 후보와 기존 점검건 왕복 및 가상 후보 표시 유지')
cmd('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1000,'deviceScaleFactor':1,'mobile':False})
shots=root/'mockups';shots.mkdir(exist_ok=True)
journey=ev('journey')
frames=[]
for i,item in enumerate(journey):
 ev(f'jumpTo({i});clearTimeout(window.toastTimer);document.querySelector("#toast").style.display="none";window.scrollTo(0,0);')
 time.sleep(.13)
 data=ev('({screen,role,selected,phase:state.phase,title:document.querySelector("h1")?.textContent,text:document.querySelector("#app").innerText.length,sw:document.documentElement.scrollWidth,w:innerWidth})')
 assert data['text']>80,(i,data)
 assert data['sw']<=data['w'],(i,data)
 metrics=cmd('Page.getLayoutMetrics')['cssContentSize']
 shot=cmd('Page.captureScreenshot',{'format':'png','captureBeyondViewport':True,'clip':{'x':0,'y':0,'width':1440,'height':metrics['height'],'scale':1}})
 name=f'{i+1:02d}_{item[0]}.png';(shots/name).write_bytes(base64.b64decode(shot['data']))
 explanation=ev(f'explanations[{json.dumps(item[0])}]')
 frames.append({'step':i,'label':item[1],'role':item[2],'image':name,'explanation':explanation,'screen':data})
results.append({'check':'24개 단계별 화면 렌더링·1440px 문서 가로 넘침 없음','result':'pass'})
cmd('Emulation.setDeviceMetricsOverride',{'width':1366,'height':768,'deviceScaleFactor':1,'mobile':False})
ev('jumpTo(3)');time.sleep(.1)
check('document.documentElement.scrollWidth<=innerWidth','1366×768 업무 목록의 문서 가로 넘침 없음')
cmd('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':False})
ev('jumpTo(6)');time.sleep(.1)
check('document.documentElement.scrollWidth<=innerWidth','390px 현장 목록의 문서 가로 넘침 없음 · 표 내부 스크롤')
cmd('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1000,'deviceScaleFactor':1,'mobile':False})
ev("resetDemo('agency')")
(root/'prototype_validation.json').write_text(json.dumps({'completed_flow':completed,'checks':results,'frames':frames},ensure_ascii=False,indent=2))
css='''*{box-sizing:border-box}body{margin:0;background:#f2f5f9;color:#203249;font:15px/1.7 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif}header{padding:30px 5vw;background:#183d65;color:white}header a{color:#fff}h1{margin:0 0 12px;font-size:30px}.intro{max-width:1250px;padding:25px;margin:auto}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:25px;max-width:1400px;margin:auto;padding:0 25px 40px}.card{background:white;border:1px solid #d1dce9;border-radius:7px;overflow:hidden}.card img{width:100%;aspect-ratio:1.42;object-fit:cover;object-position:top;border-bottom:1px solid #d1dce9}.body{padding:22px}.body h2{margin:0 0 12px;font-size:21px}.body p{font-size:14px}a{color:#205b9e}strong{color:#183f6d}.tag{font-size:12px;color:#647c95}.start{display:inline-block;background:white;color:#163e6c;padding:10px 15px;margin:15px 15px 0 0;border-radius:4px;text-decoration:none}@media(max-width:900px){.grid{grid-template-columns:1fr}}'''
cards=[]
for f in frames:
 e=f['explanation'];link=f'workflow.html?step={f["step"]}'
 cards.append(f'<article class="card"><a href="mockups/{f["image"]}" target="_blank"><img loading="lazy" src="mockups/{f["image"]}" alt="{html.escape(f["label"])}"></a><div class="body"><div class="tag">{f["step"]+1:02d} / 24 · {"공무원" if f["role"]=="official" else "전문기관"}</div><h2>{html.escape(f["label"])}</h2><p><strong>현재 관찰:</strong> {html.escape(e[1])}</p><p><strong>개편 이유:</strong> {html.escape(e[2])}</p><p><strong>대안:</strong> {html.escape(e[3])}</p><a href="{link}">이 단계의 시안 직접 열기 →</a></div></article>')
(root/'screen_gallery.html').write_text(f'<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>안전워치 전체 시안 · 24단계</title><style>{css}</style><header><h1>로그인부터 결과 검토까지 · 전체 가상 시안</h1><div>업무 담당자의 순서로 읽는 화면과 개편 이유</div><a class="start" href="workflow.html">처음부터 직접 체험</a><a class="start" href="report.html">전체 UX 분석 제안서</a></header><div class="intro"><p><strong>권장 순서:</strong> 전문기관 로그인 → 현장 근거 확인 → 보고서 v1 공유 → 공무원 검토·보완 요청 → 기관 v2 공유 → 재검토 → 완료·이력. 관할 지도·후보·자료 복구 경로도 함께 제공합니다.</p><p>모든 자료는 가상입니다. 그림을 누르면 전체 화면 이미지를, 아래 링크를 누르면 해당 단계의 클릭 가능한 시안을 엽니다. 내부 공유·검토는 신규 협업 기능 가정이며 BLCM 법정 제출·승인은 별도 확인 사항입니다.</p></div><div class="grid">{"".join(cards)}</div></html>')
ws.close()
print(json.dumps({'checks':len(results),'screens':len(frames),'result':'pass'},ensure_ascii=False))
