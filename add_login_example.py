from pathlib import Path
p=Path(__file__).resolve().parent/'workflow.html'
s=p.read_text()
s=s.replace("onclick=\"setRole('official')\"", "onclick=\"loginScreen('official')\"").replace("onclick=\"setRole('agency')\"", "onclick=\"loginScreen('agency')\"")
s=s.replace("function setRole(v){role=v;", "function setRole(v){document.querySelector('nav').style.display='';document.querySelector('.layout').style.gridTemplateColumns='';role=v;")
s=s.replace("setRole('official');\n</script>", """function loginScreen(v){
role=v;
document.querySelector('#context').textContent='시나리오 선택: '+(v==='official'?'지자체 담당자의 로그인부터':'전문기관 담당자의 로그인부터');
document.querySelector('#official').className=v==='official'?'active':'';
document.querySelector('#agency').className=v==='agency'?'active':'';
document.querySelector('nav').style.display='none';
document.querySelector('.layout').style.gridTemplateColumns='1fr';
root.innerHTML=`<div style="max-width:1000px;margin:24px auto"><h2>로그인 화면에서 시작</h2><p class="muted">상단 역할 버튼은 개편안을 살펴보기 위한 시나리오 선택입니다. 실제 사용자는 이미 확인된 계정 권한에 따라 업무 홈으로 진입합니다.</p><div class="grid"><section class="panel"><h3>건축물 안전관리 업무 지원</h3><p>지자체의 관할 점검 관리와 전문기관의 현장점검·보고서 업무를 지원합니다.</p><p><strong>업무 계정 로그인</strong></p><label for="example-id">아이디</label><input id="example-id" disabled placeholder="입력하지 않는 화면 예시" style="display:block;width:100%;padding:12px;margin:6px 0 15px;border:1px solid #c5d1de;border-radius:4px"><label for="example-pw">비밀번호</label><input id="example-pw" type="password" disabled placeholder="입력하지 않는 화면 예시" style="display:block;width:100%;padding:12px;margin:6px 0 15px;border:1px solid #c5d1de;border-radius:4px"><button class="primary" onclick="setRole(role)">로그인 후 메인화면 보기</button><p class="muted">계정 이용 안내 · 접속 지원<br>실제 인증·계정 찾기 기능은 연결하지 않았습니다.</p></section><section class="panel"><h3>${v==='official'?'공무원의 첫 업무':'전문기관의 첫 업무'}</h3><div class="steps"><p><strong>1. 로그인</strong><br>기관 계정으로 접속</p><p><strong>2. 메인화면</strong><br>${v==='official'?'내 관할·담당 업무 확인':'내 기관의 진행 중인 점검 확인'}</p><p><strong>3. 첫 업무 선택</strong><br>${v==='official'?'정기점검의 기한·기관 현황 확인':'어제 작성하던 보고서의 누락 항목 확인'}</p></div><details><summary>처음 이용하는 경우</summary><p>소속·권한이 미확정된 경우에만 확인 절차와 진행 상태를 안내합니다. 매번 역할을 다시 선택하도록 하지 않습니다.</p></details></section></div><p class="note">설계 의도: 어떤 계정을 사용하고, 로그인 후 무엇을 할 수 있는지부터 안내합니다. 기존 ID/이메일 문구는 실제 계정 정책에 맞춰 통일합니다.</p></div>`;
}
loginScreen('official');
</script>""")
p.write_text(s)
print('login-first scenario added')
