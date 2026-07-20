# Paper Shelf 공개 배포 안내 — Render + Neon

이 문서는 로컬 주소(`127.0.0.1`)가 아니라 누구나 접속할 수 있는
`https://...onrender.com` 주소를 만드는 절차입니다.

## 왜 데이터베이스를 Neon에 두나요?

Render의 무료 웹 서버는 공개 주소를 만들기 편하지만, 무료 Render Postgres는
30일 후 만료됩니다. 독서 기록을 장기간 보존하기 위해 무료 사용 기간 제한이 없는
Neon Postgres를 연결하는 구성을 사용합니다.

## 0. 절대로 GitHub에 올리면 안 되는 파일

다음 파일은 업로드하지 마세요.

- `.env`
- `db.sqlite3`
- Gemini API 키
- 확장 프로그램 연결 토큰

`.gitignore`에 이미 제외 규칙이 들어 있지만, 웹 업로드 때도 직접 확인하세요.

## 1. GitHub 저장소 만들기

1. GitHub에 로그인합니다.
2. 우측 상단 `+` → `New repository`를 누릅니다.
3. Repository name에 `paper-shelf`를 입력합니다.
4. 우선 `Private`를 권장합니다.
5. README, .gitignore, license를 GitHub에서 새로 만들지 않고 저장소를 생성합니다.
6. 새 저장소 화면에서 `uploading an existing file` 또는 `Add file → Upload files`를 누릅니다.
7. 이 프로젝트 폴더 안의 파일과 폴더를 모두 끌어놓습니다.
8. `.env`와 `db.sqlite3`가 포함되지 않았는지 확인하고 Commit합니다.

주의: 바깥쪽 프로젝트 폴더 자체가 아니라 `manage.py`가 보이는 폴더 **안의 내용**을 올려야 합니다.
GitHub 저장소 첫 화면에 `manage.py`, `render.yaml`, `requirements.txt`가 바로 보여야 합니다.

## 2. Neon 데이터베이스 만들기

1. Neon에 가입하고 새 프로젝트를 만듭니다.
2. 지역은 Render 서버와 가까운 지역을 선택합니다. 잘 모르겠으면 기본값을 사용해도 됩니다.
3. 프로젝트 Dashboard에서 `Connect`를 누릅니다.
4. `Connection string`을 선택합니다.
5. **Direct connection** 문자열을 복사합니다. 빌드 과정에서 Django migration을 실행하기 때문에 처음에는 Direct 연결을 권장합니다.
6. 문자열은 보통 아래 모양입니다.

```text
postgresql://사용자:비밀번호@호스트/neondb?sslmode=require
```

이 값 전체가 Render의 `DATABASE_URL`입니다. 외부에 공개하지 마세요.

## 3. Render Blueprint로 배포하기

1. Render에 GitHub 계정으로 가입 또는 로그인합니다.
2. Dashboard에서 `New` → `Blueprint`를 선택합니다.
3. 앞서 만든 `paper-shelf` GitHub 저장소를 연결합니다.
4. Render가 저장소 루트의 `render.yaml`을 찾으면 Blueprint 내용을 표시합니다.
5. 아래 비밀 환경변수를 입력합니다.

```text
DATABASE_URL = Neon에서 복사한 전체 connection string
NCBI_EMAIL = 본인의 실제 이메일 주소
GEMINI_API_KEY = Google AI Studio에서 만든 API 키
```

6. Blueprint를 적용합니다.
7. Build log에서 `collectstatic`, `migrate`, `gunicorn` 단계가 성공하는지 확인합니다.
8. 배포 완료 후 다음과 같은 주소가 생깁니다.

```text
https://paper-shelf-xxxx.onrender.com
```

## 4. 웹사이트에서 새 계정 만들기

공개 주소를 열고 `시작하기`에서 회원가입합니다.
로컬 SQLite의 회원과 독서 기록은 자동으로 공개 DB에 옮겨지지 않기 때문에,
처음에는 공개 사이트에서 계정을 새로 만들어야 합니다.

## 5. Chrome 확장 프로그램을 공개 사이트에 연결하기

1. 공개 Paper Shelf에 로그인합니다.
2. 상단 `확장 프로그램` 메뉴에서 새 연결 토큰을 만듭니다.
3. Chrome의 Paper Shelf 확장 프로그램 → `연결 설정`을 엽니다.
4. 웹사이트 주소를 아래처럼 변경합니다.

```text
https://paper-shelf-xxxx.onrender.com
```

5. 공개 사이트에서 새로 발급한 `ps_...` 토큰을 입력합니다.
6. 설정을 저장한 뒤 PubMed 논문에서 저장을 시험합니다.

로컬 사이트에서 발급한 토큰은 공개 사이트 DB에 존재하지 않으므로 사용할 수 없습니다.

## 6. 무료 서버의 특성

Render 무료 웹 서비스는 일정 시간 사용하지 않으면 잠들 수 있습니다.
잠든 뒤 첫 접속은 평소보다 오래 걸릴 수 있지만, 다시 깨어난 후에는 정상 작동합니다.
Neon 역시 사용하지 않을 때 compute가 일시 정지될 수 있어 첫 DB 연결이 조금 느릴 수 있습니다.

## 7. 배포 후 코드 수정

GitHub 저장소에 변경사항을 Commit하면 Render가 자동 재배포할 수 있습니다.
API 키나 DB 주소는 GitHub 파일을 수정하지 말고 Render Dashboard의 Environment에서 관리하세요.

## 8. 오류별 확인 위치

- `DisallowedHost`: Render의 `ALLOWED_HOSTS`, `RENDER_EXTERNAL_HOSTNAME` 확인
- `CSRF verification failed`: `CSRF_TRUSTED_ORIGINS` 확인
- DB 연결 오류: `DATABASE_URL` 전체 문자열과 `sslmode=require` 확인
- Gemini 오류: `GEMINI_API_KEY` 확인
- PubMed 오류: `NCBI_EMAIL` 확인
- 확장 프로그램 401: 공개 사이트에서 토큰을 새로 발급했는지 확인

Render의 Logs 탭에서 서버 오류의 마지막 줄을 확인할 수 있습니다.
