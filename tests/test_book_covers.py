import os
import pytest
from django.conf import settings
from django.test import Client
from apps.library.templatetags.library_tags import book_cover, COVER_IMAGES
from apps.library.models import Book


def test_cover_images_exist_on_disk():
    covers_dir = os.path.join(settings.BASE_DIR, "static", "img", "covers")
    assert os.path.isdir(covers_dir), f"Directory {covers_dir} does not exist"

    for slug, rel_path in COVER_IMAGES.items():
        full_path = os.path.join(settings.BASE_DIR, "static", rel_path.replace("/", os.sep))
        assert os.path.isfile(full_path), f"Cover image missing on disk: {full_path}"


def test_book_cover_filter_resolves_all_seeded_titles():
    expected_slugs = {
        "Amintiri din copilărie": "amintiri-din-copilarie",
        "Capra cu trei iezi": "capra-cu-trei-iezi",
        "D-l Goe…": "d-l-goe",
        "Din lumea celor care nu cuvântă": "din-lumea-celor-care-nu-cuvanta",
        "Făt-Frumos din lacrimă": "fat-frumos-din-lacrima",
        "Greuceanu": "greuceanu",
        "Povestea lui Harap-Alb": "povestea-lui-harap-alb",
        "Prâslea cel voinic și merele de aur": "praslea-cel-voinic-si-merele-de-aur",
        "Punguța cu doi bani": "punguta-cu-doi-bani",
        "Tinerețe fără bătrânețe și viață fără de moarte": "tinerete-fara-batranete-si-viata-fara-de-moarte",
        "Ursul păcălit de vulpe": "ursul-pacalit-de-vulpe",
        "Zâna Zorilor": "zana-zorilor",
    }

    for title, expected_slug in expected_slugs.items():
        mock_book = type("MockBook", (), {"title": title})()
        resolved = book_cover(mock_book)
        assert resolved == f"img/covers/{expected_slug}.jpg", f"Failed to resolve cover for '{title}': got '{resolved}'"


def test_book_cover_filter_handles_fallbacks():
    assert book_cover(None) == ""
    assert book_cover("") == ""
    mock_unknown = type("MockBook", (), {"title": "Unknown Book Title 123"})()
    assert book_cover(mock_unknown) == ""


def test_stat_cards_no_thick_top_border():
    css_path = os.path.join(settings.BASE_DIR, "static", "css", "app.css")
    with open(css_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "border-top: 3px" not in content, "Thick top border (3px) found in app.css"


@pytest.mark.django_db
def test_catalog_renders_cover_images(client: Client):
    # Ensure seed data or books exist
    from apps.library.models import Book
    if not Book.objects.exists():
        from django.core.management import call_command
        call_command("seed_demo")

    response = client.get("/carti/")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "/static/img/covers/amintiri-din-copilarie.jpg" in html
    assert "/static/img/covers/capra-cu-trei-iezi.jpg" in html
    assert "book-cover-img" in html
