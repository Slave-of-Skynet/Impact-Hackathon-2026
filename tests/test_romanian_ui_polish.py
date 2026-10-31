"""Issue #73: Romanian UI polish — brand header, locale-pinned dates, Romanian error
pages, human-readable genre labels.

Each area was reproduced manually before the fix (see PR); these tests pin the
corrected behavior. Render edge errors (Render 502) are out of Django's control
and intentionally not covered here (issue #59).
"""

import re
from datetime import date, timedelta

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone, translation
from django.views.defaults import permission_denied, server_error

from apps.accounts.models import Reader
from apps.club.models import Achievement, AchievementGrant, ClubMembership
from apps.library import services
from apps.library.models import Book
from apps.library.templatetags.library_extras import genre_label
from tests.conftest import make_child

CYRILLIC = re.compile(r"[\u0400-\u04FF]")
RU_BROWSER = {"HTTP_ACCEPT_LANGUAGE": "ru-RU,ru;q=0.9,en;q=0.8"}
EN_BROWSER = {"HTTP_ACCEPT_LANGUAGE": "en-US,en;q=0.8"}
UNKNOWN_BOOK = "/carti/00000000-0000-0000-0000-000000000000/"


def make_book(genre="fairy_tale", title="Capra cu trei iezi"):
    return Book.objects.create(
        title=title, author="Demo", page_count=24, genre=genre,
        age_band="7-8", cover_color="#F4A261", cover_emoji="🐐",
    )


# ---------- A. Brand header without the book emoji ----------


def test_base_template_brand_has_no_emoji():
    content = (settings.BASE_DIR / "templates" / "base.html").read_text(encoding="utf-8")
    assert "📖" not in content
    assert "brand-icon" not in content
    assert "Gustul Cărților" in content  # brand text and link kept


@pytest.mark.django_db
def test_landing_header_has_no_book_emoji(client):
    html = client.get("/").content.decode("utf-8")
    header = html.split("<main")[0]
    assert "brand-icon" not in header
    assert "📖" not in header
    assert "Gustul Cărților" in header


# ---------- B. Locale pinned to Romanian; numeric dates ----------


def test_language_policy_pinned_to_romanian():
    assert settings.LANGUAGE_CODE == "ro"
    assert settings.LANGUAGES == [("ro", "Română")]


def test_numeric_date_format_is_locale_independent():
    tpl = Template('{{ d|date:"d.m.Y" }}')
    for lang in ("ro", "ru", "en"):
        with translation.override(lang):
            assert tpl.render(Context({"d": date(2026, 10, 31)})) == "31.10.2026", lang
    # d M Y / E are the locale-sensitive formats that previously leaked Russian months.
    assert "d M Y" not in (settings.BASE_DIR / "templates" / "adult" / "child_report.html").read_text("utf-8")


@pytest.mark.django_db
def test_child_report_dates_romanian_under_ru_and_en_headers(adult_client, guardian, child):
    badge = Achievement.objects.create(
        code="first", title="Primul pas", description="d",
        rule=Achievement.SHELF_SIZE_GTE, threshold=1, members_only=True, icon="star",
    )
    AchievementGrant.objects.create(reader=child.reader, achievement=badge)
    ClubMembership.objects.create(
        reader=child.reader, source=ClubMembership.ADMIN,
        valid_from=timezone.now() - timedelta(days=1),
        valid_until=timezone.now() + timedelta(days=30),
    )
    for headers in (RU_BROWSER, EN_BROWSER):
        resp = adult_client.get(f"/familie/{child.public_id}/", **headers)
        assert resp.status_code == 200
        html = resp.content.decode("utf-8")
        assert not CYRILLIC.search(html), "no Russian month names may appear"
        assert re.search(r"\d{2}\.\d{2}\.\d{4}", html), "grants/membership dates render as dd.mm.yyyy"


# ---------- C. Romanian app-owned error pages ----------


@pytest.mark.django_db
def test_404_page_is_romanian(client):
    resp = client.get(UNKNOWN_BOOK)
    assert resp.status_code == 404
    html = resp.content.decode("utf-8")
    assert "Pagina nu a fost găsită" in html
    assert "The requested resource was not found" not in html
    assert "Traceback" not in html


@pytest.mark.django_db
def test_404_page_romanian_under_ru_header(client):
    resp = client.get(UNKNOWN_BOOK, **RU_BROWSER)
    assert resp.status_code == 404
    html = resp.content.decode("utf-8")
    assert "Pagina nu a fost găsită" in html
    assert not CYRILLIC.search(html)


def test_403_template_renders_with_status_403():
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    resp = permission_denied(request, None)
    assert resp.status_code == 403
    assert "Acces interzis" in resp.content.decode("utf-8")


def test_csrf_failure_is_branded_romanian_403():
    client = Client(enforce_csrf_checks=True)
    resp = client.post("/cont/intrare/", {"email": "a@b.local", "password": "pw123456"})
    assert resp.status_code == 403
    html = resp.content.decode("utf-8")
    assert "Acces interzis" in html
    assert "CSRF verification failed" not in html


def test_500_handler_renders_romanian_with_status_500():
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    resp = server_error(request)
    assert resp.status_code == 500
    html = resp.content.decode("utf-8")
    assert "Ceva nu a funcționat" in html
    assert "Server Error (500)" not in html


@pytest.mark.django_db
def test_form_errors_stay_romanian_under_ru_header(client):
    resp = client.post(reverse("login"), {}, **RU_BROWSER)
    assert resp.status_code == 422
    html = resp.content.decode("utf-8")
    assert "Acest câmp este obligatoriu." in html
    assert not CYRILLIC.search(html)


# ---------- D. Romanian genre labels, code semantics unchanged ----------


def test_genre_label_filter_maps_all_codes():
    from apps.library.models import GENRES

    for code, label in GENRES:
        assert genre_label(code) == label
    assert genre_label("nonexistent") == "nonexistent", "defensive fallback to raw code"


@pytest.mark.django_db
def test_book_vm_keeps_raw_code_semantics():
    from apps.library.views import _book_vm

    book = make_book(genre="humor")
    assert _book_vm(book).genre == "humor", "BookVM.genre must stay the code (filters/URLs rely on it)"


@pytest.mark.django_db
def test_adult_book_detail_shows_romanian_genre(client):
    book = make_book(genre="fairy_tale")
    resp = client.get(f"/carti/{book.public_id}/")
    assert resp.status_code == 200
    html = resp.content.decode("utf-8")
    assert "Basme" in html
    assert "fairy_tale" not in html


@pytest.mark.django_db
def test_shelf_entry_shows_romanian_genre(adult_client, guardian):
    reader = Reader.objects.get(account=guardian)
    book = make_book(genre="humor", title="Bancuri bune")
    entry, _ = services.add_to_shelf(reader, book)
    resp = adult_client.get(f"/raft/{entry.public_id}/")
    assert resp.status_code == 200
    html = resp.content.decode("utf-8")
    assert "Umor" in html
    assert "humor" not in html


@pytest.mark.django_db
def test_child_book_detail_shows_romanian_genre(child_client, child):
    book = make_book(genre="poetry", title="Versuri pentru copii")
    resp = child_client.get(f"/carti/{book.public_id}/")
    assert resp.status_code == 200
    html = resp.content.decode("utf-8")
    assert "Poezie" in html
    assert "poetry" not in html


@pytest.mark.django_db
def test_catalog_genre_filter_still_uses_codes(client):
    make_book(genre="fairy_tale")
    make_book(genre="poetry", title="Versuri pentru copii")
    resp = client.get("/carti/", {"genre": "fairy_tale"})
    assert resp.status_code == 200
    html = resp.content.decode("utf-8")
    assert "Capra cu trei iezi" in html
    assert "Versuri pentru copii" not in html  # the filter still selects by code
