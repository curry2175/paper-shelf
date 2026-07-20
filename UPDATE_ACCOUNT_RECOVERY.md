# 아이디·비밀번호 복구 기능 업데이트

## 추가된 기능

- 로그인 화면의 `아이디 또는 비밀번호를 잊으셨나요?`
- 가입 이메일로 아이디 안내 메일 발송
- 일회용 링크를 이용한 비밀번호 재설정
- 존재하지 않는 이메일을 입력해도 계정 존재 여부를 노출하지 않는 안내 화면

## 기존 공개 사이트에 반영하기

1. 이 프로젝트의 변경 파일을 GitHub 저장소에 올립니다.
2. Render Dashboard → Paper Shelf Web Service → Environment에 아래 값을 추가합니다.

```text
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=발신에 사용할 Gmail 주소
EMAIL_HOST_PASSWORD=해당 Gmail의 16자리 앱 비밀번호
DEFAULT_FROM_EMAIL=Paper Shelf <발신에 사용할 Gmail 주소>
```

3. Render에서 `Manual Deploy → Deploy latest commit`을 실행합니다.
4. 로그인 화면의 계정 복구 링크에서 아이디 찾기와 비밀번호 재설정을 각각 시험합니다.

새 데이터베이스 migration은 필요하지 않습니다.

## 로컬에서 시험하기

`.env`에도 위 이메일 설정을 입력한 뒤 다음을 실행합니다.

```cmd
python manage.py check
python manage.py test
python manage.py runserver 8000
```

SMTP 설정이 없으면 로컬 개발 환경에서는 복구 이메일 내용이 서버 터미널에 출력됩니다.
