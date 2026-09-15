from pathlib import Path
import json,time,base64,html
import requests,websocket
root=Path(__file__).resolve().parent;url=(root/'workflow.html').as_uri()
tabs=requests.get('http://127.0.0.1:9335/json',timeout=10).json();tab=next(t for t in tabs if t.get('type')=='page' and t.get('url','').startswith(url))
ws=websocket.create_connection(tab['webSocketDebuggerUrl'],origin='http://localhost:9335',timeout=25);seq=0
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
cmd('Page.bringToFront');cmd('Page.navigate',{'url':url});time.sleep(.4)
cmd('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1000,'deviceScaleFactor':1,'mobile':False})
steps=ev('tourSteps');frames=[];target=root/'mockups_v2';target.mkdir(exist_ok=True)
for i,s in enumerate(steps):
 ev(f'showTourStep({i});window.scrollTo(0,0);document.body.classList.add("capture-mode");')
 time.sleep(.10)
 data=ev('({screen,role,signedIn,phase:state.phase,sw:document.documentElement.scrollWidth,w:innerWidth,text:document.querySelector("#app").innerText.length})')
 assert data['text']>80,(i,data)
 assert data['sw']<=data['w'],(i,data)
 h=cmd('Page.getLayoutMetrics')['cssContentSize']['height']
 shot=cmd('Page.captureScreenshot',{'format':'png','captureBeyondViewport':True,'clip':{'x':0,'y':0,'width':1440,'height':h,'scale':1}})
 name=f'{i+1:02d}_{data["screen"]}.png';(target/name).write_bytes(base64.b64decode(shot['data']))
 explanation=ev('explanations[screen]||explanations.case')
 frames.append({'step':i,'label':s['label'],'screen':data,'image':name,'explanation':explanation})
 ev('document.body.classList.remove("capture-mode")')
checks.append({'check':f'{len(steps)} 화면 렌더링·1440px 문서 가로 넘침 없음','result':'pass'})
for width,height,ids in [(1366,768,[0,7,10,11,13,16,25]),(390,844,[0,1,2,3,4,7,10,13])]:
 cmd('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':False})
 for i in ids:
  ev(f'showTourStep({i})');time.sleep(.08)
  d=ev('({width:innerWidth,sw:document.documentElement.scrollWidth,screen})')
  assert d['sw']<=d['width'],(width,i,d)
 checks.append({'check':f'{width}×{height} 주요 {len(ids)}개 화면 가로 넘침 없음','result':'pass'})
cmd('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1000,'deviceScaleFactor':1,'mobile':False})
cmd('Page.navigate',{'url':url});time.sleep(.3)
(root/'gallery_validation_v2.json').write_text(json.dumps({'checks':checks,'frames':frames},ensure_ascii=False,indent=2))
css='''*{box-sizing:border-box}body{margin:0;background:#f2f5f9;color:#203249;font:15px/1.7 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif}header{padding:28px 5vw;background:#183d65;color:white}header a{color:#fff}h1{margin:0 0 12px;font-size:30px}.intro{max-width:1250px;padding:25px;margin:auto}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:25px;max-width:1400px;margin:auto;padding:0 25px 40px}.card{background:white;border:1px solid #d1dce9;border-radius:7px;overflow:hidden}.card img{width:100%;aspect-ratio:1.42;object-fit:cover;object-position:top;border-bottom:1px solid #d1dce9}.body{padding:22px}.body h2{margin:0 0 12px;font-size:21px}.body p{font-size:14px}a{color:#205b9e}strong{color:#183f6d}.tag{font-size:12px;color:#647c95}.start{display:inline-block;background:white;color:#163e6c;padding:10px 15px;margin:15px 15px 0 0;border-radius:4px;text-decoration:none}.jump{display:flex;gap:16px;flex-wrap:wrap;margin:20px 0}.card{scroll-margin-top:20px}@media(max-width:900px){.grid{grid-template-columns:1fr}}'''
cards=[]
for f in frames:
 e=f['explanation'];category='공개 조회·진입' if not f['screen']['signedIn'] else '공무원' if f['screen']['role']=='official' else '전문기관'
 cards.append(f'<article class="card" id="step-{f["step"]}"><a href="mockups_v2/{f["image"]}" target="_blank"><img loading="lazy" src="mockups_v2/{f["image"]}" alt="{html.escape(f["label"])}"></a><div class="body"><div class="tag">{f["step"]+1:02d} / {len(frames)} · {category}</div><h2>{html.escape(f["label"])}</h2><p><strong>현재 관찰:</strong> {html.escape(e[1])}</p><p><strong>개편 이유:</strong> {html.escape(e[2])}</p><p><strong>대안:</strong> {html.escape(e[3])}</p><a href="workflow.html?tour={f["step"]}">이 단계의 시안 직접 열기 →</a></div></article>')
(root/'screen_gallery.html').write_text(f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>안전워치 보강 시안 · {len(frames)}개 화면</title><style>{css}</style></head><body><header><h1>노후건축물 안전진단 관리 · 보강된 전체 시안</h1><div>공무원·전문기관 업무 우선 · 지역·주소·휠 탐색 · 결함 위치 sBIM 연결 · 점검 현황·이력에서 직접 열기</div><a class="start" href="workflow.html">공통 메인에서 직접 체험</a><a class="start" href="report.html">전체 UX 분석 제안서</a><a class="start" href="entry_review.html">사용자 유형별 보강 이유</a></header><div class="intro"><p><strong>왼쪽 주 경로:</strong> 업무 로그인 → 최근 작업과 현재 요청 → 내 업무/지도 분석 → 보고서 공유·보완·재검토.</p><p><strong>오른쪽 보조 경로:</strong> 노후건축물 검색 → 공개 GIS 지도 → 공개 안전진단 정보 → 공개용 3D/BIM.</p><p>상단 ‘← 이전 화면’으로 검색조건과 작성 내용을 유지하며 돌아갈 수 있습니다.</p><p>가상 작업은 이 브라우저에 보관되어 로그아웃·재접속을 체험할 수 있습니다. 아래 단계 미리보기는 독립 예시로 보관 기록을 갱신하지 않습니다. 실제 시스템과의 통신·업무 저장은 없습니다.</p><nav class="jump"><a href="#step-0">업무 우선 메인·보조 조회</a><a href="#step-7">업무 대시보드·지도</a><a href="#step-12">현장·보고서</a><a href="#step-20">검토·보완</a><a href="#step-30">재접속 복원</a><a href="#step-33">지역 탐색·건물 요약</a><a href="#step-38">결함 위치 sBIM</a><a href="#step-42">점검 현황·이력 → BIM</a></nav></div><div class="grid">{"".join(cards)}</div></body></html>')
ws.close();print(json.dumps({'checks':checks,'screens':len(frames),'result':'pass'},ensure_ascii=False))
