# Render Free 이메일 전송 수정

Render 무료 Web Service는 SMTP 포트 25, 465, 587을 차단합니다. 이 버전은 SMTP 대신 Brevo의 HTTPS transactional email API를 사용합니다.

## Render Environment

다음 값을 추가하거나 변경합니다.

- `EMAIL_BACKEND=papers.email_backends.BrevoAPIBackend`
- `BREVO_API_KEY=<Brevo API key>`
- `BREVO_SENDER_EMAIL=<Brevo에서 인증한 발신 이메일>`
- `BREVO_SENDER_NAME=Paper Shelf`
- `DEFAULT_FROM_EMAIL=Paper Shelf <인증한 발신 이메일>`

기존의 다음 SMTP 환경변수는 삭제해도 됩니다.

- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_TLS`
- `EMAIL_USE_SSL`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`

환경변수 저장 후 Render에서 `Clear build cache & deploy`를 실행합니다.
