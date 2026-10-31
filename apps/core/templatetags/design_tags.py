"""Presentation-only filters for the v2 design ("Caiet de lectură").

cover_class maps Book.cover_color to one of six cloth colours whose title contrast is known (>= 4.5:1);
spine_height maps a page count to the height of a book spine on the child's shelf.
"""

from django import template

register = template.Library()

# cloth colour -> RGB; the CSS classes .c-<name> live in static/css/app.css
COVER_CLASSES = {
    "navy": (0x24, 0x41, 0x5E),
    "plum": (0x5B, 0x3A, 0x55),
    "oxblood": (0x7A, 0x2E, 0x2E),
    "teal": (0x2F, 0x5F, 0x5C),
    "moss": (0x4F, 0x6B, 0x3A),
    "ochre": (0xE0, 0xA9, 0x3B),
}


@register.filter
def cover_class(hex_color):
    """'#F4A261' -> 'c-ochre' (nearest cloth colour); anything unparsable -> 'c-navy'."""
    try:
        value = str(hex_color).strip().lstrip("#")
        if len(value) != 6:
            raise ValueError
        rgb = tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except (TypeError, ValueError):
        return "c-navy"
    name = min(COVER_CLASSES, key=lambda k: sum((a - b) ** 2 for a, b in zip(rgb, COVER_CLASSES[k])))
    return f"c-{name}"


@register.filter
def spine_height(page_count, lo=140, hi=210):
    """Page count -> spine height in px: 60 pages or fewer = 140, 400 or more = 210."""
    try:
        pages = int(page_count)
    except (TypeError, ValueError):
        return lo
    pages = min(max(pages, 60), 400)
    return lo + round((pages - 60) * (hi - lo) / 340)
