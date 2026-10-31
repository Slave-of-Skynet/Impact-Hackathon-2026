"""Short PIN verification, stored only in the authenticated server session (#60)."""

from datetime import datetime, timezone as datetime_timezone

from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

from . import throttle
from .models import Throttle

TRUST_KEY = "parent_access_v1"
TRUST_SECONDS = 30 * 60


def revoke(request):
    request.session.pop(TRUST_KEY, None)


def _credentials(user):
    # No raw password/PIN hash is copied into the session or template context.
    return salted_hmac(
        "accounts.parent_access.v1", f"{user.pk}:{user.password}:{user.pin_hash}", algorithm="sha256",
    ).hexdigest()


def verified_until(request):
    record = request.session.get(TRUST_KEY)
    if record is None:
        return None
    valid = isinstance(record, dict) and request.user.is_authenticated and bool(request.user.pin_hash)
    if valid:
        issued = record.get("issued_at")
        now = timezone.now().timestamp()
        valid = (
            # Bounded comparisons also reject NaN/infinity/oversized integers
            # without converting malformed values to a float (which can overflow).
            type(issued) in (int, float) and now - TRUST_SECONDS < issued <= now
            and record.get("account") == str(request.user.pk)
            and record.get("session") == request.session.session_key
            and isinstance(record.get("credentials"), str)
            and constant_time_compare(record["credentials"], _credentials(request.user))
        )
    if valid:
        try:
            throttle.check(Throttle.PIN, str(request.user.pk))
        except throttle.Locked:
            valid = False
    if not valid:
        revoke(request)
        return None
    return datetime.fromtimestamp(issued + TRUST_SECONDS, tz=datetime_timezone.utc)


def grant_after_pin(request):
    """Only called by pin_gate after actual PIN verification and throttle check."""
    request.session.cycle_key()
    request.session[TRUST_KEY] = {
        "account": str(request.user.pk), "session": request.session.session_key,
        "issued_at": timezone.now().timestamp(), "credentials": _credentials(request.user),
    }
