"""Template filters for the library app.

Owner: Vladimir (issue #73).
"""

from django import template

from apps.library.models import GENRES

register = template.Library()

_GENRE_LABELS = dict(GENRES)


@register.filter
def genre_label(code):
    """Romanian display label for a Book.genre code (issue #73).

    Frozen BookVM.genre deliberately keeps the raw code (catalog filters and URLs
    compare codes), so rendering sites apply this filter instead of changing the
    viewmodel semantics. Unknown values fall back to the raw code.
    """
    return _GENRE_LABELS.get(code, code)
