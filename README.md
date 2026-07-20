# Paper Shelf Django

PubMed 논문을 검색하고, Abstract 기반 AI 설명을 만든 뒤 읽은 논문을 책처럼 쌓는 Django MVP입니다.

## 현재 포함된 기능

- 일반 회원가입과 로그인
- 최근 PubMed 논문 검색
- 논문 메타데이터와 Abstract 저장
- Gemini 구조화 요약 생성
- 웹사이트의 `읽음 완료` 버튼
- 읽은 날짜·메모·별점 저장
- 월별 책장 UI와 독서 통계
- Chrome 확장 프로그램에서 현재 논문 저장
- 확장 프로그램용 토큰 발급·교체·해제
- SQLite 로컬 실행과 PostgreSQL/Render 배포 설정

자동 이메일과 매일 예약 실행 기능은 포함하지 않습니다.

## 1. Windows에서 실행

Anaconda Prompt에서 프로젝트 폴더로 이동한 뒤 실행합니다.

```cmd
conda create -n paper_shelf_web python=3.12 -y
conda activate paper_shelf_web
pip install -r requirements.txt
copy .env.example .env
notepad .env
```

`.env`에 최소한 다음 값을 입력합니다.

```text
NCBI_EMAIL=실제 이메일
GEMINI_API_KEY=Gemini API 키
```

데이터베이스를 만들고 실행합니다.

```cmd
python manage.py migrate
python manage.py runserver 8000
```

브라우저에서 `http://127.0.0.1:8000`으로 접속합니다.

## 2. Chrome 확장 프로그램 연결

1. 웹사이트에서 계정을 만들고 로그인합니다.
2. 상단의 **확장 프로그램** 메뉴를 엽니다.
3. **연결 토큰 만들기**를 눌러 토큰을 복사합니다.
4. Chrome에서 `chrome://extensions`를 엽니다.
5. **개발자 모드**를 켭니다.
6. **압축해제된 확장 프로그램을 로드합니다**를 누릅니다.
7. 프로젝트의 `chrome_extension` 폴더를 선택합니다.
8. 확장 프로그램의 **연결 설정**에서 아래 값을 저장합니다.

```text
웹사이트 주소: http://127.0.0.1:8000
연결 토큰: ps_로 시작하는 발급 토큰
```

이제 PubMed 논문 페이지에서 Chrome 상단의 Paper Shelf 아이콘을 누르고 **읽음 완료 · 책장에 추가**를 선택할 수 있습니다.

## 3. 연결 토큰 보안

- 토큰 원문은 서버 DB에 저장되지 않고 검증용 해시만 저장됩니다.
- 발급된 토큰은 생성 직후 한 번만 표시됩니다.
- 토큰이 노출되었다고 생각되면 웹사이트에서 **새 토큰으로 교체**하거나 **연결 해제**하세요.
- 확장 프로그램은 토큰을 Chrome 확장 프로그램 전용 로컬 저장소에 보관합니다.

## 4. 관리자 계정

```cmd
python manage.py createsuperuser
```

관리자 화면은 `http://127.0.0.1:8000/admin/`입니다.

## 5. Render 공개 배포 준비

`render.yaml`과 `build.sh`가 포함되어 있습니다.

1. 프로젝트를 GitHub 저장소에 업로드합니다.
2. Render에서 **New Blueprint**를 선택합니다.
3. GitHub 저장소를 연결합니다.
4. Render 환경변수에 `NCBI_EMAIL`과 `GEMINI_API_KEY`를 입력합니다.
5. 배포가 끝나면 `https://...onrender.com` 주소가 발급됩니다.
6. 확장 프로그램의 웹사이트 주소를 새 공개 주소로 변경합니다.

현재 확장 프로그램의 `manifest.json`은 `*.onrender.com`을 허용합니다. 별도 도메인을 사용하는 경우 `host_permissions`에 도메인을 추가해야 합니다.

## 6. 주요 URL

- 홈: `/`
- 논문 검색: `/papers/search/`
- 내 책장: `/papers/bookshelf/`
- 확장 프로그램 연결: `/papers/extension/`
- 확장 프로그램 저장 API: `/papers/api/reading-records/`

## 7. 테스트

```cmd
python manage.py check
python manage.py test
```

## 공개 웹사이트 배포

공개 주소 배포는 [DEPLOY_PUBLIC.md](DEPLOY_PUBLIC.md)의 Render + Neon 안내를 따르세요.
이 구성은 Render 무료 Postgres의 30일 만료를 피하기 위해 Neon에 독서 기록을 저장합니다.
