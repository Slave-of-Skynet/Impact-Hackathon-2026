"""Template tags and filters for library ratings and catalog display (Refs #62)."""

from django import template

register = template.Library()


@register.filter
def get_rating(book_ratings, book_id):
    """Safely retrieve book rating metadata dictionary by book.public_id UUID."""
    if not isinstance(book_ratings, dict):
        return None
    return book_ratings.get(book_id)


@register.filter
def get_personal_rating(personal_ratings, book_id):
    """Safely retrieve personal rating integer (1..5) by book.public_id UUID."""
    if not isinstance(personal_ratings, dict):
        return None
    return personal_ratings.get(book_id)


@register.filter
def format_avg(value):
    """Format float average rating to one decimal place (e.g. 4.3)."""
    if value is None:
        return ""
    try:
        return f"{float(value):.1f}"
    except (ValueError, TypeError):
        return ""
