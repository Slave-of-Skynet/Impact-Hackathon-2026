"""Issue #60: real PIN→short parent window, explicit lock and device isolation."""

from copy import deepcopy
from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.sessions.backends.base import UpdateError
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts import parent_session, throttle
from apps.accounts.models import Throttle
from apps.library.models import Book, ShelfEntry
from tests.conftest import HTMX, PASSWORD, PIN, make_child, make_guardian

pytestmark = pytest.mark.django_db
GATE, RETURN, LOCK = "/parinte/", "/parinte/revino/", "/parinte/blocheaza/"
WARNING = "Blochează accesul înainte de a oferi dispozitivul copilului."


def enter(browser, child):
    response = browser.post(reverse("child_mode_start", args=[child.public_id]))
    assert response.status_code == 302 and browser.session["active_child"] == str(child.public_id)


def verify(browser, child):
    enter(browser, child)
    response = browser.post(GATE, {"pin": PIN})
    assert response.status_code == 302 and response["Location"] == "/panou/"
    assert parent_session.TRUST_KEY in browser.session


def assert_locked(browser):
    assert browser.session.get("mode") == "child"
    assert parent_session.TRUST_KEY not in browser.session
    response = browser.get("/panou/")
    assert response.status_code == 302 and response["Location"] == GATE


def test_login_first_exit_requires_pin_and_repeated_explicit_switches(django_user_model, client, guardian, child):
    assert client.post("/cont/intrare/", {"username": guardian.email, "password": PASSWORD}).status_code == 302
    assert parent_session.TRUST_KEY not in client.session
    enter(client, child)
    first_key = client.session.session_key
    assert b'name="pin"' in client.get(GATE).content
    assert client.post(RETURN).status_code == 302
    assert client.session["mode"] == "child" and parent_session.TRUST_KEY not in client.session
    response = client.post(GATE, {"pin": PIN})
    assert response.status_code == 302 and response["Location"] == "/panou/"
    assert client.session.session_key != first_key and not Session.objects.filter(session_key=first_key).exists()
    record = deepcopy(client.session[parent_session.TRUST_KEY])
    sibling = make_child(guardian, "Alex")
    for profile in (child, sibling, child):
        enter(client, profile)
        # GET gate and arbitrary adult routes never exit child mode.
        page = client.get(GATE)
        assert b'name="pin"' not in page.content
        assert b"/parinte/revino/" in page.content
        assert client.session["mode"] == "child"
        assert client.get("/panou/")["Location"] == GATE
        response = client.post(RETURN, {"next": "https://evil.example/"})
        assert response.status_code == 302 and response["Location"] == "/panou/"
        assert "mode" not in client.session and "active_child" not in client.session
        assert client.session[parent_session.TRUST_KEY] == record  # TTL never refreshed


def test_exact_absolute_ttl_and_gets_do_not_renew(adult_client, child, clock):
    verify(adult_client, child)
    record = deepcopy(adult_client.session[parent_session.TRUST_KEY])
    clock.advance(minutes=29, seconds=59)
    assert WARNING.encode() in adult_client.get("/panou/").content
    assert adult_client.session[parent_session.TRUST_KEY] == record
    enter(adult_client, child)
    assert adult_client.post(RETURN).status_code == 302
    assert "mode" not in adult_client.session
    enter(adult_client, child)
    clock.advance(seconds=1)
    response = adult_client.post(RETURN)
    assert response.status_code == 302 and response["Location"] == GATE
    assert_locked(adult_client)
    assert b'name="pin"' in adult_client.get(GATE).content


def test_five_independent_sessions_never_inherit_trust(guardian, child):
    browsers = [Client() for _ in range(5)]
    for browser in browsers:
        browser.force_login(guardian)
        enter(browser, child)
    assert browsers[0].post(GATE, {"pin": PIN}).status_code == 302
    for browser in browsers[1:]:
        assert parent_session.TRUST_KEY not in browser.session
        assert b'name="pin"' in browser.get(GATE).content
        assert browser.post(RETURN)["Location"] == GATE
        assert browser.session["mode"] == "child"


@pytest.mark.parametrize("mode", ["adult", "child"])
def test_explicit_lock_protects_device_rotates_key_and_rejects_old_writer(adult_client, child, mode):
    verify(adult_client, child)
    if mode == "child":
        enter(adult_client, child)
    old_key = adult_client.session.session_key
    stale = SessionStore(session_key=old_key)
    assert parent_session.TRUST_KEY in stale  # force-load the old in-flight snapshot
    response = adult_client.post(LOCK, {"child": child.public_id})
    assert response.status_code == 302 and response["Location"] == "/copil/"
    assert adult_client.session.session_key != old_key
    assert adult_client.session["active_child"] == str(child.public_id)
    assert not Session.objects.filter(session_key=old_key).exists()
    assert_locked(adult_client)
    stale["mode"] = "adult"
    with pytest.raises(UpdateError):
        stale.save()  # cannot recreate a revoked session from an old request
    old_tab = Client()
    old_tab.cookies[settings.SESSION_COOKIE_NAME] = old_key
    assert old_tab.post(RETURN, **HTMX).status_code == 401
    assert b'name="pin"' in adult_client.get(GATE).content
    assert adult_client.post(RETURN, **HTMX).status_code == 403


def test_lock_selects_owned_child_and_never_accepts_foreign_child(adult_client, guardian, child):
    verify(adult_client, child)
    sibling = make_child(guardian, "Alex")
    other = make_child(make_guardian("foreign-parent@demo.local"))
    before = dict(adult_client.session)
    assert adult_client.post(LOCK, {"child": other.public_id}).status_code == 404
    assert dict(adult_client.session) == before
    assert adult_client.post(LOCK, {"child": sibling.public_id}).status_code == 302
    assert adult_client.session["active_child"] == str(sibling.public_id)
    # Child-mode lock cannot switch to another submitted profile.
    assert adult_client.post(LOCK, {"child": other.public_id}).status_code == 302
    assert adult_client.session["active_child"] == str(sibling.public_id)


@pytest.mark.parametrize("case", ["no_child", "deleted_child", "missing_pin", "foreign_active_child"])
def test_lock_fails_safe_to_logout_without_a_safe_child(adult_client, guardian, child, case):
    verify(adult_client, child)
    data = {}
    if case == "deleted_child":
        enter(adult_client, child)
        child.delete()
    elif case == "missing_pin":
        guardian.pin_hash = None
        guardian.save(update_fields=["pin_hash"])
        data = {"child": child.public_id}
    elif case == "foreign_active_child":
        enter(adult_client, child)
        foreign = make_child(make_guardian("foreign-lock@demo.local"))
        session = adult_client.session
        session["active_child"] = str(foreign.public_id)
        session.save()
    response = adult_client.post(LOCK, data)
    assert response.status_code == 302 and response["Location"] == "/cont/intrare/"
    assert "_auth_user_id" not in adult_client.session and parent_session.TRUST_KEY not in adult_client.session


def test_deleted_child_never_has_quick_trusted_escape(adult_client, child):
    verify(adult_client, child)
    enter(adult_client, child)
    child.delete()
    assert adult_client.post(RETURN, **HTMX).status_code == 403
    assert adult_client.session["mode"] == "child"
    page = adult_client.get(GATE)
    assert b'name="pin"' in page.content and parent_session.TRUST_KEY not in adult_client.session


def test_pin_change_revokes_all_device_trust_without_granting_new_trust(adult_client, guardian, child):
    other = Client()
    other.force_login(guardian)
    verify(adult_client, child)
    verify(other, child)
    response = adult_client.post("/familie/pin/", {"pin": "1357", "pin_confirm": "1357", "password": PASSWORD})
    assert response.status_code == 302 and parent_session.TRUST_KEY not in adult_client.session
    enter(other, child)
    assert other.post(RETURN)["Location"] == GATE
    assert_locked(other)
    assert other.post(GATE, {"pin": PIN}).status_code == 422
    assert other.post(GATE, {"pin": "1357"}).status_code == 302


def test_password_change_logout_expiry_and_account_change_invalidate(adult_client, guardian, child):
    verify(adult_client, child)
    original = deepcopy(adult_client.session[parent_session.TRUST_KEY])
    guardian.set_password("New-test-password-60!")
    guardian.save(update_fields=["password"])
    assert adult_client.post(RETURN, **HTMX).status_code == 401
    assert parent_session.TRUST_KEY not in adult_client.session
    adult_client.force_login(guardian)
    # Even if old verification was copied into a newly authenticated session it fails.
    session = adult_client.session
    session[parent_session.TRUST_KEY] = original
    session.save()
    enter(adult_client, child)
    assert adult_client.post(RETURN)["Location"] == GATE
    verify_response = adult_client.post(GATE, {"pin": PIN})
    assert verify_response.status_code == 302
    assert adult_client.post("/cont/iesire/").status_code == 302
    assert parent_session.TRUST_KEY not in adult_client.session
    adult_client.force_login(guardian)
    verify(adult_client, child)
    Session.objects.filter(session_key=adult_client.session.session_key).update(expire_date=timezone.now()-timedelta(seconds=1))
    assert adult_client.post(RETURN, **HTMX).status_code == 401
    assert parent_session.TRUST_KEY not in adult_client.session
    other = make_guardian("different-account@demo.local")
    adult_client.force_login(other)
    session = adult_client.session
    session[parent_session.TRUST_KEY] = original
    session.save()
    assert adult_client.get("/panou/").status_code == 200
    assert parent_session.TRUST_KEY not in adult_client.session


@pytest.mark.parametrize("change", ["future", "expired", "nan", "infinite", "huge_integer", "bool", "missing_time", "bad_type", "account", "session", "credentials"])
def test_malformed_or_rebound_records_fail_closed(adult_client, child, change):
    verify(adult_client, child)
    session = adult_client.session
    record = deepcopy(session[parent_session.TRUST_KEY])
    if change == "future":
        record["issued_at"] = timezone.now().timestamp()+1
    elif change == "expired":
        record["issued_at"] = timezone.now().timestamp()-1800
    elif change == "nan":
        record["issued_at"] = float("nan")
    elif change == "infinite":
        record["issued_at"] = float("inf")
    elif change == "huge_integer":
        record["issued_at"] = 10 ** 400
    elif change == "bool":
        record["issued_at"] = True
    elif change == "missing_time":
        del record["issued_at"]
    elif change == "bad_type":
        record = True
    else:
        record[change] = "not-the-bound-value"
    session[parent_session.TRUST_KEY] = record
    session.save()
    enter(adult_client, child)
    assert adult_client.post(RETURN)["Location"] == GATE
    assert_locked(adult_client)


def test_account_wide_pin_lock_overrides_trust_and_correct_pin(adult_client, guardian, child):
    verify(adult_client, child)
    other = Client()
    other.force_login(guardian)
    enter(other, child)
    for _ in range(5):
        assert other.post(GATE, {"pin": "0000"}).status_code == 422
    enter(adult_client, child)
    assert adult_client.post(RETURN, **HTMX).status_code == 403
    assert parent_session.TRUST_KEY not in adult_client.session
    assert adult_client.post(GATE, {"pin": PIN}).status_code == 429
    assert adult_client.session["mode"] == "child"
    assert Throttle.objects.get(scope=Throttle.PIN).failures == 5
    assert adult_client.post(LOCK).status_code == 302
    assert Throttle.objects.get(scope=Throttle.PIN).failures == 5
    assert adult_client.post("/cont/iesire/").status_code == 302
    assert Throttle.objects.get(scope=Throttle.PIN).failures == 5


def test_real_pin_post_never_uses_trust_to_accept_wrong_pin(adult_client, child):
    verify(adult_client, child)
    enter(adult_client, child)
    response = adult_client.post(GATE, {"pin": "0000"})
    assert response.status_code == 422
    assert_locked(adult_client)


def test_throttle_rechecked_after_hash_and_no_trust_granted(child_client, guardian, monkeypatch):
    from apps.accounts import views
    original = views.check_password
    def lock_during_hash(pin, encoded):
        valid = original(pin, encoded)
        for _ in range(5):
            throttle.record_failure(Throttle.PIN, str(guardian.pk))
        return valid
    monkeypatch.setattr(views, "check_password", lock_during_hash)
    response = child_client.post(GATE, {"pin": PIN})
    assert response.status_code == 429
    assert_locked(child_client)


def test_trust_cannot_replay_blocked_adult_htmx_mutations(adult_client, child):
    verify(adult_client, child)
    enter(adult_client, child)
    response = adult_client.post(reverse("child_rename", args=[child.public_id]), {"nickname": "Altered"}, **HTMX)
    assert response.status_code == 403 and response.content == b"" and "HX-Trigger" not in response
    assert adult_client.session["mode"] == "child"
    response = adult_client.post(RETURN, **HTMX)
    assert response.status_code == 204 and response["HX-Redirect"] == "/panou/"
    assert "HX-Trigger" not in response
    child.refresh_from_db()
    assert child.nickname == "Mia"


def test_controls_warning_and_private_cache_even_on_public_urls(adult_client, child):
    verify(adult_client, child)
    for path in ("/panou/", "/familie/", "/", "/carti/"):
        response = adult_client.get(path)
        assert response.status_code == 200
        assert WARNING.encode() in response.content and b"/parinte/blocheaza/" in response.content
        assert "no-store" in response["Cache-Control"] and "private" in response["Cache-Control"]
    assert "no-store" not in Client().get("/").get("Cache-Control", "")
    # The service worker precaches this standalone shell even when signed in.
    offline = adult_client.get("/offline/")
    assert WARNING.encode() not in offline.content and b"Mia" not in offline.content
    assert "public" in offline["Cache-Control"]
    enter(adult_client, child)
    page = adult_client.get("/copil/")
    assert b"/parinte/revino/" in page.content
    assert WARNING.encode() in page.content


def test_switching_trust_never_mixes_adult_or_children_readers(adult_client, guardian, child):
    sibling = make_child(guardian, "Alex")
    book = Book.objects.create(title="Synthetic isolation", author="Demo", page_count=120, genre="story")
    entries = {reader.pk: ShelfEntry.objects.create(reader=reader, book=book)
               for reader in (guardian.reader, child.reader, sibling.reader)}
    verify(adult_client, child)
    for profile in (child, sibling, child):
        enter(adult_client, profile)
        page = adult_client.get("/raft/")
        assert [entry.public_id for entry in page.context["entries"]] == [entries[profile.reader.pk].public_id]
        assert adult_client.post(RETURN).status_code == 302
        page = adult_client.get("/raft/")
        assert [entry.public_id for entry in page.context["entries"]] == [entries[guardian.reader.pk].public_id]


def test_csrf_methods_and_anonymous_semantics(guardian, child):
    browser = Client(enforce_csrf_checks=True)
    browser.force_login(guardian)
    page = browser.get("/familie/")
    token = browser.cookies[settings.CSRF_COOKIE_NAME].value
    assert browser.post(reverse("child_mode_start", args=[child.public_id]), {"csrfmiddlewaretoken": token}).status_code == 302
    for path in (LOCK, RETURN):
        assert browser.get(path).status_code == 405
        assert browser.post(path, **HTMX).status_code == 403
    assert browser.post(GATE, {"pin": PIN, "csrfmiddlewaretoken": token}).status_code == 302
    assert browser.post(reverse("child_mode_start", args=[child.public_id]), {"csrfmiddlewaretoken": token}).status_code == 302
    assert browser.post(RETURN, **HTMX).status_code == 403
    assert browser.session["mode"] == "child"
    assert browser.post(RETURN, {"csrfmiddlewaretoken": token}).status_code == 302
    assert browser.post(LOCK, {"child": child.public_id, "csrfmiddlewaretoken": token}).status_code == 302
    assert_locked(browser)
    anonymous = Client()
    for path in (LOCK, RETURN):
        assert anonymous.post(path).status_code == 302
        assert anonymous.post(path, **HTMX).status_code == 401
