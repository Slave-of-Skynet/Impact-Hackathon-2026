"""UI and Accessibility integration tests for Book Ratings (Refs #62B).

Author: Denis (Antigravity)
Scope: Child and adult 5-star rating controls, radiogroup accessibility,
       privacy threshold display in catalog and book detail, error handling,
       and HTMX end-to-end success/error integration.
"""

import re
import uuid
import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import Reader
from apps.library import services
from apps.library.models import Book, ShelfEntry
from tests.conftest import PASSWORD, make_child, make_guardian

pytestmark = pytest.mark.django_db
HX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def test_setup(guardian, child):
    book = Book.objects.create(title="Carte Povești Test", author="Ion Creangă", page_count=100, genre="fairy_tale")
    child_entry, _ = services.add_to_shelf(child.reader, book)
    adult_entry, _ = services.add_to_shelf(guardian.reader, book)
    return {
        "book": book,
        "guardian": guardian,
        "child": child,
        "child_entry": child_entry,
        "adult_entry": adult_entry,
    }


def enter_child_mode(client, setup):
    client.force_login(setup["guardian"])
    client.post(reverse("child_mode_start", args=[setup["child"].public_id]))


def test_unfinished_book_does_not_show_rating_ui(test_setup, client):
    """An unfinished book must not render the 5-star rating form."""
    enter_child_mode(client, test_setup)
    entry = test_setup["child_entry"]

    response = client.get(reverse("shelf_entry", args=[entry.public_id]))
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'role="radiogroup"' not in html
    assert 'name="rating"' not in html
    assert "Salvează evaluarea" not in html
    assert "Cum ți s-a părut această carte?" not in html


def test_child_finished_book_renders_accessible_rating_form(test_setup, client):
    """A finished book renders an accessible 1-5 star radiogroup and submit button."""
    enter_child_mode(client, test_setup)
    entry = test_setup["child_entry"]

    # Finish book
    services.finish_book(entry.reader, entry, uuid.uuid4())

    response = client.get(reverse("shelf_entry", args=[entry.public_id]))
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Accessible rating control
    assert 'role="radiogroup"' in html
    assert 'class="child-stars-group"' in html
    assert 'name="rating"' in html
    assert 'value="5"' in html
    assert 'value="1"' in html
    assert 'Salvează evaluarea' in html
    assert "Cum ți s-a părut această carte?" in html

    # CSRF and action URL
    assert reverse("rate_book", args=[entry.public_id]) in html
    assert "csrfmiddlewaretoken" in html


def test_child_save_and_update_rating_flow(test_setup, client):
    """Rating flow: rate 4 stars -> verify checked state and badge -> update to 5 stars."""
    enter_child_mode(client, test_setup)
    entry = test_setup["child_entry"]
    services.finish_book(entry.reader, entry, uuid.uuid4())

    rate_url = reverse("rate_book", args=[entry.public_id])

    # 1. POST rating = 4
    resp = client.post(rate_url, {"rating": 4}, follow=True)
    assert resp.status_code == 200
    html = resp.content.decode("utf-8")

    # Shows personal rating badge and update button
    assert "Ai evaluat cartea:" in html
    assert "4/5" in html
    assert "Actualizează evaluarea" in html
    assert 'id="star-4" name="rating" value="4" class="child-star-input" checked' in html

    # 2. Update rating = 5
    resp2 = client.post(rate_url, {"rating": 5}, follow=True)
    assert resp2.status_code == 200
    html2 = resp2.content.decode("utf-8")
    assert "5/5" in html2
    assert 'id="star-5" name="rating" value="5" class="child-star-input" checked' in html2


def test_child_htmx_rating_success_and_redirect_flow(test_setup, client):
    """With finished own book and HTTP_HX_REQUEST='true', POST rating=4 -> 204 with HX-Redirect to own entry.
    Following that redirect as GET restores personal_rating=4, checked star and visible badge.
    """
    enter_child_mode(client, test_setup)
    entry = test_setup["child_entry"]
    services.finish_book(entry.reader, entry, uuid.uuid4())

    rate_url = reverse("rate_book", args=[entry.public_id])
    expected_redirect = reverse("shelf_entry", args=[entry.public_id])

    # 1. POST via HTMX
    resp = client.post(rate_url, {"rating": "4"}, **HX)
    assert resp.status_code == 204
    assert resp.headers.get("HX-Redirect") == expected_redirect
    assert resp.headers.get("HX-Trigger") == "saved"
    assert resp.content == b""

    # 2. Follow the HX-Redirect via GET
    get_resp = client.get(resp.headers["HX-Redirect"])
    assert get_resp.status_code == 200
    html = get_resp.content.decode("utf-8")

    assert "Ai evaluat cartea:" in html
    assert "4/5" in html
    assert 'id="star-4" name="rating" value="4" class="child-star-input" checked' in html
    assert "Actualizează evaluarea" in html


def test_child_htmx_invalid_rating_422_preserves_state(test_setup, client):
    """Invalid rating=6 via HTMX -> 422, content type text/plain, no HX-Redirect or saved trigger.
    Persisted previous rating is unchanged, and the UI shows a safe human-readable inline error,
    not a misleading success state and not a progress-form swap.
    """
    enter_child_mode(client, test_setup)
    entry = test_setup["child_entry"]
    services.finish_book(entry.reader, entry, uuid.uuid4())

    # Pre-rate with rating 3
    services.rate_book(entry.reader, entry, 3)
    entry.refresh_from_db()
    assert entry.rating == 3

    rate_url = reverse("rate_book", args=[entry.public_id])

    # Attempt invalid rating=6 via HTMX
    resp = client.post(rate_url, {"rating": "6"}, **HX)
    assert resp.status_code == 422
    assert "text/plain" in resp.headers["Content-Type"]
    assert "HX-Redirect" not in resp.headers
    assert "HX-Trigger" not in resp.headers
    error_msg = resp.content.decode("utf-8")
    assert "Alege o evaluare între 1 și 5." in error_msg

    # Persisted previous rating is unchanged
    entry.refresh_from_db()
    assert entry.rating == 3

    # On reload/re-render, state remains 3/5, no progress-form swap or misleading success
    page_resp = client.get(reverse("shelf_entry", args=[entry.public_id]))
    assert page_resp.status_code == 200
    html = page_resp.content.decode("utf-8")
    assert "3/5" in html
    assert 'id="star-3" name="rating" value="3" class="child-star-input" checked' in html


def test_adult_finished_book_rating_ui(test_setup, adult_client):
    """Adult finished entry renders understated rating card with accessible inputs."""
    entry = test_setup["adult_entry"]
    services.finish_book(entry.reader, entry, uuid.uuid4())

    response = adult_client.get(reverse("shelf_entry", args=[entry.public_id]))
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'class="adult-stars-group"' in html
    assert 'class="adult-rating-card"' in html
    assert 'name="rating"' in html
    assert "Salvează evaluarea" in html


def test_adult_htmx_rating_success_and_invalid_error_flow(test_setup, adult_client):
    """Adult HTMX rating flow: 204 + HX-Redirect on success, 422 plain text on invalid rating."""
    entry = test_setup["adult_entry"]
    services.finish_book(entry.reader, entry, uuid.uuid4())
    rate_url = reverse("rate_book", args=[entry.public_id])
    expected_redirect = reverse("shelf_entry", args=[entry.public_id])

    # Success rating 5
    resp = adult_client.post(rate_url, {"rating": "5"}, **HX)
    assert resp.status_code == 204
    assert resp.headers.get("HX-Redirect") == expected_redirect
    assert resp.headers.get("HX-Trigger") == "saved"

    follow_resp = adult_client.get(expected_redirect)
    assert follow_resp.status_code == 200
    html = follow_resp.content.decode("utf-8")
    assert "5/5" in html
    assert 'id="adult-star-5" name="rating" value="5" class="adult-star-input" checked' in html

    # Invalid rating
    bad_resp = adult_client.post(rate_url, {"rating": "99"}, **HX)
    assert bad_resp.status_code == 422
    assert "text/plain" in bad_resp.headers["Content-Type"]
    assert "HX-Redirect" not in bad_resp.headers
    assert "HX-Trigger" not in bad_resp.headers
    assert "Alege o evaluare între 1 și 5." in bad_resp.content.decode("utf-8")


def test_child_no_id_clashes_and_accessible_markup(test_setup, client):
    """Verify child shelf_entry page has no duplicate HTML IDs, accessible radiogroup, and dual POST/HTMX support."""
    enter_child_mode(client, test_setup)
    child_entry = test_setup["child_entry"]
    services.finish_book(child_entry.reader, child_entry, uuid.uuid4())
    services.rate_book(child_entry.reader, child_entry, 4)

    resp = client.get(reverse("shelf_entry", args=[child_entry.public_id]))
    assert resp.status_code == 200
    html = resp.content.decode("utf-8")

    ids = re.findall(r'\bid=["\']([^"\']+)["\']', html)
    assert len(ids) == len(set(ids)), f"Duplicate IDs in child view: {[x for x in ids if ids.count(x) > 1]}"

    # Verify form has action, method, and hx-post
    assert f'action="/raft/{child_entry.public_id}/evaluare/"' in html
    assert f'hx-post="/raft/{child_entry.public_id}/evaluare/"' in html
    assert 'hx-target="#rating-error-box"' in html
    assert 'id="rating-error-box"' in html
    assert 'role="radiogroup"' in html


def test_adult_no_id_clashes_and_accessible_markup(test_setup, adult_client):
    """Verify adult shelf_entry page has no duplicate HTML IDs, accessible radiogroup, and dual POST/HTMX support."""
    adult_entry = test_setup["adult_entry"]
    services.finish_book(adult_entry.reader, adult_entry, uuid.uuid4())
    services.rate_book(adult_entry.reader, adult_entry, 5)

    resp = adult_client.get(reverse("shelf_entry", args=[adult_entry.public_id]))
    assert resp.status_code == 200
    html = resp.content.decode("utf-8")

    ids = re.findall(r'\bid=["\']([^"\']+)["\']', html)
    assert len(ids) == len(set(ids)), f"Duplicate IDs in adult view: {[x for x in ids if ids.count(x) > 1]}"
    assert f'action="/raft/{adult_entry.public_id}/evaluare/"' in html
    assert f'hx-post="/raft/{adult_entry.public_id}/evaluare/"' in html
    assert 'id="adult-rating-error-box"' in html


def test_htmx_unfinished_book_and_pin_session_integrity(test_setup, client):
    """HTMX rating on unfinished book returns 422 without modifying state;
    rating actions never compromise child-mode session or bypass PIN gates.
    """
    enter_child_mode(client, test_setup)
    entry = test_setup["child_entry"]
    assert entry.status != ShelfEntry.FINISHED

    rate_url = reverse("rate_book", args=[entry.public_id])
    resp = client.post(rate_url, {"rating": "4"}, **HX)
    assert resp.status_code == 422
    assert "Poți evalua doar o carte terminată." in resp.content.decode("utf-8")
    assert "HX-Redirect" not in resp.headers

    # Session remains in child mode
    session = client.session
    assert session.get("mode") == "child"

    # Adult URLs still redirect to pin gate (no auth bypass)
    resp_adult = client.get(reverse("adult_dashboard"))
    assert resp_adult.status_code == 302
    assert "pin" in resp_adult.url.lower() or reverse("pin_gate") in resp_adult.url


def test_catalog_and_detail_privacy_threshold_empty_state(test_setup, client):
    """Under 3 ratings, catalog and detail show clean empty state without fake stars."""
    book = test_setup["book"]

    # 0 ratings
    resp = client.get(reverse("catalog"))
    assert resp.status_code == 200
    html = resp.content.decode("utf-8")
    assert "Fără evaluări" in html
    assert "★ 5.0" not in html

    detail_resp = client.get(reverse("book_detail", args=[book.public_id]))
    assert detail_resp.status_code == 200
    detail_html = detail_resp.content.decode("utf-8")
    assert "Fără evaluări" in detail_html


def test_catalog_and_detail_displays_verified_average(test_setup, client):
    """With >= 3 ratings, catalog and detail display true average and count."""
    book = test_setup["book"]
    g1 = test_setup["guardian"]
    g2 = make_guardian("g2-rating@demo.local")
    g3 = make_guardian("g3-rating@demo.local")

    e1, _ = services.add_to_shelf(g1.reader, book)
    e2, _ = services.add_to_shelf(g2.reader, book)
    e3, _ = services.add_to_shelf(g3.reader, book)

    services.finish_book(g1.reader, e1, uuid.uuid4())
    services.finish_book(g2.reader, e2, uuid.uuid4())
    services.finish_book(g3.reader, e3, uuid.uuid4())

    # Ratings: 5, 4, 3 -> avg = 4.0, count = 3
    services.rate_book(g1.reader, e1, 5)
    services.rate_book(g2.reader, e2, 4)
    services.rate_book(g3.reader, e3, 3)

    resp = client.get(reverse("catalog"))
    html = resp.content.decode("utf-8")
    assert "4.0" in html
    assert "(3)" in html

    detail_resp = client.get(reverse("book_detail", args=[book.public_id]))
    detail_html = detail_resp.content.decode("utf-8")
    assert "4.0" in detail_html
    assert "(3" in detail_html
