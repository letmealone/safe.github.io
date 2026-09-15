# 안전워치 가상 시안

노후건축물 안전진단 업무와 공개 정보조회 흐름을 체험하는 정적 웹 시안입니다.
건물·점검자료·모델은 가상이며 실제 시스템에 연결되지 않습니다.

## GitHub Pages 배포

1. 이 폴더 **안의 파일과 reference 폴더**를 저장소 최상위에 올립니다.
   최상위에 index.html이 보여야 합니다. ZIP 파일 자체를 올리지 마세요.
2. 저장소의 Settings → Pages를 엽니다.
3. Build and deployment의 Source: **Deploy from a branch**.
4. Branch: **main**, 폴더: **/(root)** → Save.
   실제 업로드한 브랜치명이 다르면 해당 브랜치를 선택합니다.
5. 배포가 끝나면 Pages의 Visit site로 접속합니다.

일반 저장소 주소: https://계정명.github.io/저장소명/
계정명.github.io라는 저장소의 주소: https://계정명.github.io/

빌드 명령·패키지 설치·API 키가 필요하지 않습니다.
웹 업로드에서 숨김 파일이 빠졌다면 저장소 최상위에 빈 .nojekyll 파일을 추가할 수 있습니다.
이 시안은 Jekyll 전용 문법이나 밑줄로 시작하는 자산을 사용하지 않습니다.

## 체험 범위

- index.html: 첫 화면
- workflow.html: 같은 시안 및 기존 단계 미리보기 주소
- about.html: 사용 안내
- reference/map/README.md: 지도 경계 출처와 이용 조건

가상 계정의 작업 기록은 브라우저에만 보관됩니다.
실제 인증·서버 저장·사용자 간 공유 기능은 제공하지 않습니다.

공식 안내: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
