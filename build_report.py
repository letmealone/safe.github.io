from pathlib import Path
import html, json, re, datetime
from markdown_it import MarkdownIt
from bs4 import BeautifulSoup

root = Path(__file__).resolve().parent
md = MarkdownIt('commonmark', {'html': False}).enable('table')
css = '''
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f3f5f8;color:#243344;font:16px/1.85 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic",sans-serif}a{color:#1759ad;text-underline-offset:3px}header{background:#142f52;color:white;padding:25px 4vw}header a{color:white;margin-right:22px}header p{margin:0;color:#d1deed;font-size:14px}.layout{display:grid;grid-template-columns:255px minmax(0,1fr);max-width:1530px;margin:auto;gap:28px;padding:28px}nav{position:sticky;top:20px;align-self:start;font-size:14px;background:white;padding:22px;border:1px solid #dce3ec;border-radius:8px}nav a{display:block;padding:6px 0;text-decoration:none}main{background:white;padding:38px 46px;min-width:0;border:1px solid #dce3ec;border-radius:8px}h1{font-size:34px;line-height:1.35;letter-spacing:-1px;margin-top:0}h2{font-size:25px;line-height:1.45;border-top:1px solid #dce3ec;padding-top:35px;margin-top:50px;scroll-margin-top:25px}h3{font-size:20px;line-height:1.5;margin-top:30px}p{margin:14px 0}strong{color:#163c6c}li{margin:7px 0}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.7;margin:25px 0}th{background:#edf2f8;color:#1e416b;text-align:left}td,th{padding:12px;border:1px solid #d8e0eb;vertical-align:top}th:first-child{min-width:65px}pre{white-space:pre-wrap;overflow-wrap:anywhere;padding:22px;background:#eff3f8;border-left:4px solid #2869b1;font:14px/1.9 ui-monospace,monospace}code{font-size:.9em}img{max-width:100%;height:auto;border:1px solid #dbe1e9}details{margin:18px 0;border:1px solid #d6dfeb;padding:14px;border-radius:6px}summary{cursor:pointer;font-weight:600;color:#184a83}figcaption{font-size:14px;color:#53677e}figure{margin:20px 0}.note{background:#eaf2fc;border-left:4px solid #2769b5;padding:15px 20px}.foot{font-size:13px;color:#62758c;margin-top:40px}button{background:#fff;border:1px solid #9caec2;padding:8px 15px;border-radius:5px;cursor:pointer}.table-wrap{overflow:auto}@media(max-width:1000px){.layout{display:block;padding:12px}nav{position:static;margin-bottom:15px}main{padding:25px 20px}h1{font-size:28px}}@media print{body{background:white;font-size:11pt}header,nav,.print-hide{display:none!important}.layout{display:block;padding:0}main{border:0;padding:0}h2{break-after:avoid}table{font-size:9pt}tr{break-inside:avoid}a{color:inherit}details{display:none}pre{font-size:9pt}h2{margin-top:24px;padding-top:18px}}
'''

def page(source, target, title, extra=''):
    body = BeautifulSoup(md.render(source), 'html.parser')
    toc=[]
    for i,h in enumerate(body.find_all('h2'),1):
        h['id']=f'section-{i}'
        toc.append(f'<a href="#section-{i}">{html.escape(h.get_text())}</a>')
    for a in body.find_all('a',href=True):
        if a['href']=='document_advice.md':a['href']='document_advice.html'
    for table in body.find_all('table'):
        wrapper=body.new_tag('div',attrs={'class':'table-wrap'})
        table.wrap(wrapper)
    result=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{css}</style></head><body>
    <header><a href="report.html">안전워치 UX 검토</a><a href="workflow.html">클릭 가능한 시안</a><a href="screen_gallery.html">전체 화면·설명</a><a href="entry_review.html">진입·복원 보강</a><a href="map_review.html">지도·sBIM 검토</a><a href="document_advice.html">개발 문서 자문</a><a href="evidence_index.html">화면 기록</a><p>2026.09.15 · 실제 화면 관찰 + BLCM 공식 매뉴얼 + 개발계획 문서 대조</p></header>
    <div class="layout"><nav aria-label="목차">{''.join(toc)}<hr><button onclick="window.print()">인쇄 / PDF</button></nav><main>{body}{extra}<p class="foot">검토 산출물은 로컬 파일입니다. 플랫폼의 업무 데이터를 수정하거나 저장하지 않았습니다.</p></main></div></body></html>'''
    (root/target).write_text(result)

shots=[
('01_login','기존 로그인 화면 — 계정 안내와 업무 시작'),
('39_admin_dashboard','관리자 대시보드 — 업무 진입 구조'),
('66_facility3','1366×768 목록 — 필터와 표가 차지하는 공간'),
('49_inspection_loaded','기존 회차 비교 — 유지할 강점'),
('56_ssib_report','연계 보고서 — 항목별 작성 현황'),
('61_field_phone','390×844 현장조사 — 결과 열과 화면 폭'),
('90_unlinked_records','기존 대장 연결 실패 복구 화면'),
('104_defect_by_floor','기존 층 기준 결함 목록'),
]
extra='<h2 id="screens">대표 관찰 화면</h2><p>아래 제목을 누르면 직접 확인한 화면이 펼쳐집니다. 화면의 수치는 검토 시점의 개발 데이터이며 운영 통계로 해석하지 않았습니다.</p>'
for key,label in shots:
    extra+=f'<details><summary>{html.escape(label)}</summary><figure><a href="evidence/{key}.png"><img loading="lazy" src="evidence/{key}.png" alt="{html.escape(label)}"></a><figcaption>{key} · 원본을 누르면 확대할 수 있습니다.</figcaption></figure></details>'
page((root/'UX_개편_제안서.md').read_text(),'report.html','안전워치 노후건축물 안전진단 관리 UX 개편 제안서',extra)
page((root/'document_advice.md').read_text(),'document_advice.html','개발 문서 기반 UX 자문')
page((root/'지도_sBIM_UX_검토.md').read_text(),'map_review.html','지도 탐색·결함 위치 sBIM UX 검토')
page((root/'사용자유형별_진입_보강안.md').read_text(),'entry_review.html','사용자 유형별 진입·재접속 보강안')
records=[]
for p in sorted((root/'evidence').glob('*.json')):
    try:
        d=json.loads(p.read_text())
        records.append({'name':p.stem,'time':d.get('captured_at',''),'url':d.get('url',''),'image':p.with_suffix('.png').name})
    except Exception:pass
rows=''.join(f'<tr><td>{html.escape(r["time"])}</td><td><a href="evidence/{r["image"]}">{html.escape(r["name"])}</a></td><td>{html.escape(r["url"])}</td></tr>' for r in sorted(records,key=lambda r:r['time']))
(root/'evidence_index.html').write_text(f'<!doctype html><html lang="ko"><meta charset="utf-8"><title>화면 탐색 기록</title><style>{css}</style><header><a href="report.html">제안서로 돌아가기</a><p>실제 사이트 탐색과 로컬 시안 검증 기록 · 로딩 도중 캡처도 포함하므로 상태 판단은 제안서의 최종 관찰을 따릅니다.</p></header><main><h1>화면 탐색 기록</h1><p>이미지는 실제 개발 시스템 탐색과 로컬 가상 시안의 검증 기록입니다. 경로가 file:로 시작하는 항목은 가상 시안입니다. 제안서에는 업무 분석에 필요한 대표 화면을 연결했습니다.</p><table><thead><tr><th>확인 시각</th><th>화면</th><th>경로</th></tr></thead><tbody>{rows}</tbody></table></main></html>')
print(json.dumps({'report':'report.html','observations':len(records),'unique_paths':len(set(r['url'] for r in records))},ensure_ascii=False))
