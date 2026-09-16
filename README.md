# 안전워치 가상 시안

노후건축물 안전진단 업무와 공개 정보조회 흐름을 체험하는 정적 웹 시안입니다.
건물·점검자료·모델은 가상이며 실제 시스템에 연결되지 않습니다.

## Netlify 배포

빌드 명령·패키지 설치·API 키가 필요하지 않은 정적 사이트입니다.
저장소 최상위의 `netlify.toml`에 게시 폴더를 `.`으로 설정했습니다.

### GitHub 저장소 연동

1. `netlify.toml`을 포함한 변경 사항을 GitHub의 `main` 브랜치에 커밋하고 푸시합니다.
2. [Netlify](https://app.netlify.com/)에 로그인합니다.
3. **Add new project → Import an existing project → GitHub**를 선택합니다.
4. GitHub 접근 권한을 연결하고 **letmealone/safe.github.io** 저장소를 선택합니다.
5. 아래 설정을 확인하고 **Publish**를 누릅니다.

| 항목 | 값 |
| --- | --- |
| 배포 브랜치 | `main` |
| Base directory | 비워 둠 |
| Build command | 비워 둠 |
| Publish directory | `.` |
| 환경 변수 | 없음 |

배포가 끝나면 Netlify가 제공하는 `https://프로젝트명.netlify.app` 주소로 접속합니다.
이후 `main`에 푸시하면 Netlify에서 자동으로 다시 배포합니다.
GitHub Pages 사용 여부와 관계없이 이 저장소를 Netlify에 연결할 수 있습니다.

공식 안내: [저장소에서 배포하기](https://docs.netlify.com/start/quickstarts/deploy-from-repository/)

### 배포 후 확인

- 첫 화면, 업무 화면(`workflow.html`), 안내 화면(`about.html`)과 지도가 열리는지 확인합니다.
- 공유할 사이트라면 로그아웃한 브라우저에서도 접속되는지 확인합니다.
  팀의 기본 비공개 설정에 따라 공개 접근 설정이 필요할 수 있습니다.
- 실제 이용할 사내·기관 네트워크에서 새 주소의 접속 여부를 확인합니다.
  기존 GitHub Pages 접속 실패의 원인은 아직 확인되지 않았습니다.
- 가상 계정의 브라우저 저장 기록은 주소별로 구분되므로 기존 GitHub Pages의 기록이 새 주소로 자동 이전되지 않습니다.

## 체험 범위

- index.html: 첫 화면
- workflow.html: 같은 시안 및 기존 단계 미리보기 주소
- about.html: 사용 안내
- reference/map/README.md: 지도 경계 출처와 이용 조건

가상 계정의 작업 기록은 브라우저에만 보관됩니다.
실제 인증·서버 저장·사용자 간 공유 기능은 제공하지 않습니다.
