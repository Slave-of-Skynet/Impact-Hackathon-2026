"""Template filters for club membership rendering.

Owner: Vladimir (issue #17 review fix).
"""

from django import template

from apps.club.models import ClubMembership

register = template.Library()


def _field(row, name):
    """Read a field from a model row or a synthetic dict (the report context passes
    .values() dicts with the contracted {valid_until, status} keys only)."""
    if isinstance(row, dict):
        return row.get(name)
    return getattr(row, name, None)


@register.filter
def membership_is_current(row, now=None):
    """True when this single history row is still date-valid now.

    Per the issue #17 review prescription the row status derives from its OWN
    valid_until (timezone-aware) plus status — never from the reader-level
    is_member flag, which would label an old date-expired row "✓ Activ"
    whenever a separate currently-valid row exists. A row whose window end has
    passed can no longer be current even though its status stays 'active' in
    the database. The template additionally gates on is_member so a not-yet-
    started future row cannot render active while the reader has no
    entitlement.
    """
    from django.utils import timezone

    now = timezone.now() if now is None else now
    if _field(row, "status") != ClubMembership.ACTIVE:
        return False
    valid_until = _field(row, "valid_until")
    return valid_until is not None and valid_until > now
