# Paper Shelf Chrome Extension

## 로컬 설치

1. Chrome 주소창에 `chrome://extensions`를 입력합니다.
2. 오른쪽 위의 **개발자 모드**를 켭니다.
3. **압축해제된 확장 프로그램을 로드합니다**를 누릅니다.
4. 이 `chrome_extension` 폴더를 선택합니다.
5. Paper Shelf 웹사이트에 로그인하고 **확장 프로그램** 메뉴에서 연결 토큰을 발급합니다.
6. Chrome 확장 프로그램의 **연결 설정**에 웹사이트 주소와 토큰을 저장합니다.

## 지원 페이지

- PubMed: URL에서 PMID를 직접 인식하므로 가장 안정적으로 작동합니다.
- 주요 저널 페이지: `citation_doi`, `citation_title` 등의 메타태그가 있으면 DOI와 제목을 인식합니다.

## 배포 도메인

현재 `manifest.json`은 아래 주소에 대한 API 요청을 허용합니다.

- `http://127.0.0.1/*`
- `http://localhost/*`
- `https://*.onrender.com/*`

별도 도메인을 연결하면 `host_permissions`에 그 도메인을 추가한 뒤 확장 프로그램을 다시 로드하세요.


## 연결 토큰 형식

현재 발급되는 토큰은 `ps.`로 시작합니다. 표시된 토큰을 점과 밑줄을 바꾸지 말고 그대로 붙여넣으세요. 이전 `ps_` 토큰도 계속 지원합니다.
