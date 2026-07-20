"""Django email backend that sends transactional mail through Brevo's HTTPS API.

Render's free web services block outbound SMTP ports, but HTTPS requests remain
available. This backend lets Django's built-in password-reset flow keep using
``send_mail``/``EmailMessage`` without opening an SMTP connection.
"""

from __future__ import annotations

from email.utils import parseaddr
import logging

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class BrevoAPIBackend(BaseEmailBackend):
    endpoint = "https://api.brevo.com/v3/smtp/email"

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        api_key = getattr(settings, "BREVO_API_KEY", "").strip()
        if not api_key:
            error = RuntimeError("BREVO_API_KEY가 설정되지 않았습니다.")
            if self.fail_silently:
                logger.error("Brevo email was not sent: %s", error)
                return 0
            raise error

        sent_count = 0
        for message in email_messages:
            try:
                self._send_one(message, api_key)
                sent_count += 1
            except Exception:
                if self.fail_silently:
                    logger.exception("Brevo API email delivery failed")
                    continue
                raise
        return sent_count

    def _send_one(self, message, api_key):
        sender_name, sender_email = parseaddr(
            message.from_email or settings.DEFAULT_FROM_EMAIL
        )
        if not sender_email:
            sender_email = getattr(settings, "BREVO_SENDER_EMAIL", "").strip()
        if not sender_name:
            sender_name = getattr(settings, "BREVO_SENDER_NAME", "Paper Shelf")
        if not sender_email:
            raise RuntimeError("BREVO_SENDER_EMAIL 또는 DEFAULT_FROM_EMAIL이 필요합니다.")

        payload = {
            "sender": {"name": sender_name, "email": sender_email},
            "to": [self._recipient(address) for address in message.to],
            "subject": message.subject,
            "textContent": message.body or "",
        }

        if message.cc:
            payload["cc"] = [self._recipient(address) for address in message.cc]
        if message.bcc:
            payload["bcc"] = [self._recipient(address) for address in message.bcc]
        if message.reply_to:
            reply_name, reply_email = parseaddr(message.reply_to[0])
            if reply_email:
                payload["replyTo"] = {
                    "name": reply_name or reply_email,
                    "email": reply_email,
                }

        html_content = self._html_alternative(message)
        if html_content:
            payload["htmlContent"] = html_content

        response = requests.post(
            self.endpoint,
            headers={
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json",
            },
            json=payload,
            timeout=getattr(settings, "EMAIL_TIMEOUT", 30),
        )
        if response.status_code not in {200, 201, 202}:
            detail = response.text[:1000]
            raise RuntimeError(
                f"Brevo API가 메일을 거부했습니다 "
                f"(HTTP {response.status_code}): {detail}"
            )

    @staticmethod
    def _recipient(address):
        name, email = parseaddr(address)
        recipient = {"email": email or address}
        if name:
            recipient["name"] = name
        return recipient

    @staticmethod
    def _html_alternative(message):
        for alternative in getattr(message, "alternatives", ()):
            content = getattr(alternative, "content", None)
            mimetype = getattr(alternative, "mimetype", None)
            if content is None and isinstance(alternative, (tuple, list)):
                content, mimetype = alternative
            if mimetype == "text/html":
                return content
        return ""
