from __future__ import annotations

import hashlib
import hmac
import secrets

from django.conf import settings
from django.utils import timezone

from .models import ExtensionToken

TOKEN_PREFIX = "ps"


def _digest(secret: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        secret.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def issue_extension_token(user) -> str:
    selector = secrets.token_urlsafe(9)
    secret = secrets.token_urlsafe(32)
    ExtensionToken.objects.update_or_create(
        user=user,
        defaults={
            "selector": selector,
            "verifier_digest": _digest(secret),
            "last_used_at": None,
        },
    )
    return f"{TOKEN_PREFIX}_{selector}_{secret}"


def revoke_extension_token(user) -> None:
    ExtensionToken.objects.filter(user=user).delete()


def authenticate_extension_token(raw_token: str):
    try:
        prefix, selector, secret = raw_token.strip().split("_", 2)
    except ValueError:
        return None

    if prefix != TOKEN_PREFIX or not selector or not secret:
        return None

    try:
        token = ExtensionToken.objects.select_related("user").get(
            selector=selector
        )
    except ExtensionToken.DoesNotExist:
        return None

    if not hmac.compare_digest(token.verifier_digest, _digest(secret)):
        return None

    ExtensionToken.objects.filter(pk=token.pk).update(last_used_at=timezone.now())
    return token.user
