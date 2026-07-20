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
    # A dot is not produced by token_urlsafe, so it is a safe delimiter.
    return f"{TOKEN_PREFIX}.{selector}.{secret}"


def revoke_extension_token(user) -> None:
    ExtensionToken.objects.filter(user=user).delete()


def authenticate_extension_token(raw_token: str):
    raw_token = raw_token.strip()
    selector = secret = ""

    # Current token format. token_urlsafe never contains a dot.
    if raw_token.startswith(f"{TOKEN_PREFIX}."):
        try:
            prefix, selector, secret = raw_token.split(".", 2)
        except ValueError:
            return None
        if prefix != TOKEN_PREFIX:
            return None
    # Backward compatibility for tokens issued by the earlier underscore format.
    # Since token_urlsafe can itself contain underscores, match the selector stored
    # in the database instead of splitting at an ambiguous delimiter.
    elif raw_token.startswith(f"{TOKEN_PREFIX}_"):
        for candidate in ExtensionToken.objects.select_related("user").all():
            marker = f"{TOKEN_PREFIX}_{candidate.selector}_"
            if raw_token.startswith(marker):
                selector = candidate.selector
                secret = raw_token[len(marker):]
                token = candidate
                break
        else:
            return None
    else:
        return None

    if not selector or not secret:
        return None

    if "token" not in locals():
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
