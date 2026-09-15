from pathlib import Path
root=Path(__file__).resolve().parent
p=root/'workflow.html'
s=p.read_text()
s=s.replace("let role='official',filter='전체',selected=2,caseTab='summary';", """let role='official',filter='전체',selected=2,caseTab='summary';
function nextTask(c){return role==='official'?c.next:({1:'점검보고서 작성 내용과 첨부자료 이어서 확인',2:'현장 판단 미입력 3개를 확인하고 보고서 준비',3:'실태조사 결과 자료 정리'})[c.id];}
function visibleCases(){return role==='official'?cases:cases.filter(c=>c.id!==3);}
function workTypes(){return ['전체',...new Set(visibleCases().map(c=>c.type))];}
""")
s=s.replace("function nav(id){for", "function nav(id){document.querySelector('#navregion').style.display=role==='official'?'block':'none';for")
s=s.replace("${['전체','정기점검','소규모 노후건축물 점검','3종건축물 지정 실태조사'].map(t=>", "${workTypes().map(t=>")
s=s.replace("${cases.filter(c=>filter==='전체'||c.type===filter).map(c=>", "${visibleCases().filter(c=>filter==='전체'||c.type===filter).map(c=>")
s=s.replace('${c.next}', '${nextTask(c)}')
s=s.replace('<button onclick="region()">관할 현황·대상 선별 열기</button>', '''${role==='official'?'<button onclick="region()">관할 현황·대상 선별 열기</button>':'<button onclick="openCase(2,\\'report\\')">보고서 이어보기</button>'}''')
p.write_text(s)
p=root/'build_report.py'
s=p.read_text().replace('이미지는 개발 시스템 검토용 원본입니다. 로그인·계정 비밀번호는 기록에 포함하지 않았습니다.','이미지는 개발 시스템 검토용 원본입니다. 제안서에는 업무 분석에 필요한 대표 화면을 연결했습니다.')
p.write_text(s)
print('role examples and evidence wording refined')
