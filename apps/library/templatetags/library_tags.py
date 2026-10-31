"""Template tags and filters for library ratings, covers, and catalog display (Refs #62)."""

import re
from django import template

register = template.Library()

COVER_IMAGES = {
    "amintiri-din-copilarie": "img/covers/amintiri-din-copilarie.jpg",
    "capra-cu-trei-iezi": "img/covers/capra-cu-trei-iezi.jpg",
    "d-l-goe": "img/covers/d-l-goe.jpg",
    "din-lumea-celor-care-nu-cuvanta": "img/covers/din-lumea-celor-care-nu-cuvanta.jpg",
    "fat-frumos-din-lacrima": "img/covers/fat-frumos-din-lacrima.jpg",
    "greuceanu": "img/covers/greuceanu.jpg",
    "povestea-lui-harap-alb": "img/covers/povestea-lui-harap-alb.jpg",
    "praslea-cel-voinic-si-merele-de-aur": "img/covers/praslea-cel-voinic-si-merele-de-aur.jpg",
    "punguta-cu-doi-bani": "img/covers/punguta-cu-doi-bani.jpg",
    "tinerete-fara-batranete-si-viata-fara-de-moarte": "img/covers/tinerete-fara-batranete-si-viata-fara-de-moarte.jpg",
    "ursul-pacalit-de-vulpe": "img/covers/ursul-pacalit-de-vulpe.jpg",
    "zana-zorilor": "img/covers/zana-zorilor.jpg",
}


@register.filter
def book_cover(book):
    """Return relative static path for a book's cover image if present."""
    if not book:
        return ""
    title = getattr(book, "title", str(book))
    norm = title.lower()
    norm = norm.replace("ă", "a").replace("â", "a").replace("î", "i")
    norm = norm.replace("ș", "s").replace("ş", "s").replace("ț", "t").replace("ţ", "t")
    slug = re.sub(r"[^a-z0-9]+", "-", norm).strip("-")
    return COVER_IMAGES.get(slug, "")


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
