"""Issue #62 backend acceptance using real routes, authz and production templates."""

import uuid
from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models.signals import post_save
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Reader
from apps.library import services
from apps.library.models import Book, ProgressEvent, ShelfEntry
from apps.library.ratings import rating_context
from tests.conftest import PASSWORD, make_child, make_guardian

pytestmark = pytest.mark.django_db
HX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def diary(guardian, child):
    book = Book.objects.create(title="Synthetic rating book", author="Demo", page_count=120, genre="story")
    adult_entry, _ = services.add_to_shelf(guardian.reader, book)
    child_entry, _ = services.add_to_shelf(child.reader, book)
    return SimpleNamespace(book=book, adult=adult_entry, child=child_entry, guardian=guardian, profile=child)


def url(entry):
    return reverse("rate_book", args=[entry.public_id])


def finish(entry):
    return services.finish_book(entry.reader, entry, uuid.uuid4()).entry


def child_mode(client, diary):
    client.force_login(diary.guardian)
    assert client.post(reverse("child_mode_start", args=[diary.profile.public_id])).status_code == 302


def unsaved(response, status):
    assert response.status_code == status
    assert "HX-Trigger" not in response


@pytest.mark.parametrize("is_child", [False, True])
def test_finish_rate_replace_refresh_and_independent_login(diary, client, is_child):
    if is_child:
        child_mode(client, diary)
    else:
        client.force_login(diary.guardian)
    entry = diary.child if is_child else diary.adult
    # Finish through the existing HTTP flow before rating.
    assert client.post(reverse("finish_book", args=[entry.public_id]), {"request_id": uuid.uuid4()}).status_code == 302
    before = (ShelfEntry.objects.count(), ProgressEvent.objects.count())
    for value in (1, 2, 3, 4, 5, 5, 2):
        response = client.post(url(entry), {"rating": value}, follow=True)
        assert response.redirect_chain == [(reverse("shelf_entry", args=[entry.public_id]), 302)]
        assert response.context["personal_rating"] == value and response.context["can_rate"] is True
        assert client.get(reverse("shelf_entry", args=[entry.public_id])).context["personal_rating"] == value
    assert (ShelfEntry.objects.count(), ProgressEvent.objects.count()) == before
    other_browser = Client()
    assert other_browser.post(reverse("login"), {"username": diary.guardian.email, "password": PASSWORD}).status_code == 302
    if is_child:
        assert other_browser.post(reverse("child_mode_start", args=[diary.profile.public_id])).status_code == 302
    response = other_browser.get(reverse("shelf_entry", args=[entry.public_id]))
    assert response.context["personal_rating"] == 2
    detail = other_browser.get(reverse("book_detail", args=[diary.book.public_id]))
    assert detail.context["personal_ratings"] == {diary.book.public_id: 2}
    assert "no-store" in detail["Cache-Control"]
    entry.refresh_from_db()
    assert entry.rating == 2


@pytest.mark.parametrize("bad", ["0", "6", "1.5", "abc", "", "NaN", "-1", "+1", " 1", "1 ", "01", "１"])
def test_invalid_input_422_preserves_prior_rating(diary, adult_client, bad):
    entry = finish(diary.adult)
    services.rate_book(entry.reader, entry, 4)
    for headers in ({}, HX):
        response = adult_client.post(url(entry), {"rating": bad}, **headers)
        unsaved(response, 422)
        assert response.content.decode() == "Alege o evaluare între 1 și 5."
        assert "HX-Redirect" not in response
        assert "no-store" in response["Cache-Control"]
    entry.refresh_from_db()
    assert entry.rating == 4


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.5, None, float("nan"), {}, []])
def test_service_rejects_non_integer_values(diary, bad):
    entry = finish(diary.adult)
    with pytest.raises(ValidationError):
        services.rate_book(entry.reader, entry, bad)
    entry.refresh_from_db()
    assert entry.rating is None


def test_missing_unfinished_get_and_anonymous_are_unsaved(diary, client):
    for headers in ({}, HX):
        response = client.post(url(diary.adult), {"rating": 5}, **headers)
        unsaved(response, 401 if headers else 302)
    client.force_login(diary.guardian)
    unsaved(client.get(url(diary.adult)), 405)
    response = client.post(url(diary.adult), {"rating": 5}, **HX)
    unsaved(response, 422)
    assert response.content.decode() == "Poți evalua doar o carte terminată."
    assert not client.get(reverse("shelf_entry", args=[diary.adult.public_id])).context["can_rate"]
    finish(diary.adult)
    unsaved(client.post(url(diary.adult), **HX), 422)
    diary.adult.refresh_from_db()
    assert diary.adult.rating is None


@pytest.mark.parametrize("is_child", [False, True])
def test_ownership_tampering_and_child_deny_by_default(diary, client, is_child):
    own, other = (diary.child, diary.adult) if is_child else (diary.adult, diary.child)
    sibling = make_child(diary.guardian, "Alex")
    sibling_entry = ShelfEntry.objects.create(reader=sibling.reader, book=diary.book)
    foreign = make_guardian("foreign-rating@demo.local")
    foreign_entry = ShelfEntry.objects.create(reader=foreign.reader, book=diary.book)
    for entry in (own, other, sibling_entry, foreign_entry):
        finish(entry)
    if is_child:
        child_mode(client, diary)
    else:
        client.force_login(diary.guardian)
    for public_id in (other.public_id, sibling_entry.public_id, foreign_entry.public_id, uuid.uuid4()):
        for value in (5, "bad"):
            unsaved(client.post(reverse("rate_book", args=[public_id]), {"rating": value}, **HX), 404)
    payload = {"rating": 3, "reader_id": foreign.reader.pk, "reader": other.reader.public_id,
               "guardian": foreign.pk, "child": sibling.public_id}
    response = client.post(url(own), payload, **HX)
    assert response.status_code == 204 and response.content == b""
    assert response["HX-Trigger"] == "saved"
    assert response["HX-Redirect"] == reverse("shelf_entry", args=[own.public_id])
    assert list(ShelfEntry.objects.exclude(rating=None).values_list("reader_id", "rating")) == [(own.reader_id, 3)]
    if is_child:
        for path in ("/panou/", "/familie/", "/club/cod/", "/admin/", "/not-allowed/"):
            refused = client.post(path, **HX)
            unsaved(refused, 403)
            assert refused.content == b""
        # The PIN gate still requires the actual PIN; rating does not unlock it.
        assert b'name="pin"' in client.get(reverse("pin_gate")).content
        assert client.session["mode"] == "child"
        session = client.session
        session["active_child"] = str(foreign.reader.public_id)
        session.save()
        unsaved(client.post(url(own), {"rating": 4}, **HX), 403)


@pytest.mark.parametrize("is_child", [False, True])
def test_strict_csrf_and_expired_session(diary, is_child):
    browser = Client(enforce_csrf_checks=True)
    browser.force_login(diary.guardian)
    browser.get(reverse("family"))
    token = browser.cookies[settings.CSRF_COOKIE_NAME].value
    if is_child:
        assert browser.post(reverse("child_mode_start", args=[diary.profile.public_id]),
                            {"csrfmiddlewaretoken": token}).status_code == 302
    entry = finish(diary.child if is_child else diary.adult)
    unsaved(browser.post(url(entry), {"rating": 4}, **HX), 403)
    assert browser.post(url(entry), {"rating": 4, "csrfmiddlewaretoken": token}, **HX).status_code == 204
    Session.objects.filter(session_key=browser.session.session_key).update(
        expire_date=timezone.now() - timedelta(seconds=1),
    )
    unsaved(browser.post(url(entry), {"rating": 5, "csrfmiddlewaretoken": token}, **HX), 401)
    entry.refresh_from_db()
    assert entry.rating == 4


def test_empty_two_three_votes_update_and_owner_privacy(diary, client):
    book_id = diary.book.public_id
    empty = {"average": None, "count": None, "message": "Nu sunt suficiente evaluări"}
    entry_a = finish(diary.adult)
    entry_b = finish(diary.child)
    third = make_guardian("third-rating@demo.local")
    entry_c = finish(ShelfEntry.objects.create(reader=third.reader, book=diary.book))
    for route in (reverse("catalog"), reverse("book_detail", args=[book_id])):
        assert client.get(route).context["book_ratings"][book_id] == empty
    for entry, value in ((entry_a, 2), (entry_b, 4)):
        services.rate_book(entry.reader, entry, value)
        for route in (reverse("catalog"), reverse("book_detail", args=[book_id])):
            response = client.get(route)
            assert response.context["book_ratings"][book_id] == empty
            assert response.context["personal_ratings"] == {}
    services.rate_book(entry_c.reader, entry_c, 5)
    for route in (reverse("catalog"), reverse("book_detail", args=[book_id])):
        value = client.get(route).context["book_ratings"][book_id]
        assert value == {"average": pytest.approx(11 / 3), "count": 3, "message": ""}
    services.rate_book(entry_a.reader, entry_a, 1)
    assert client.get(reverse("catalog")).context["book_ratings"][book_id]["average"] == pytest.approx(10 / 3)
    client.force_login(diary.guardian)
    for route in (reverse("catalog"), reverse("book_detail", args=[book_id]), reverse("my_shelf")):
        response = client.get(route)
        assert response.context["personal_ratings"] == {book_id: 1}  # never the child's 4
        assert "no-store" in response["Cache-Control"]
    child_mode(client, diary)
    assert client.get(reverse("catalog")).context["personal_ratings"] == {book_id: 4}
    client.logout()
    Book.objects.filter(pk=diary.book.pk).update(is_active=False)
    assert book_id not in client.get(reverse("catalog")).context["book_ratings"]
    unsaved(client.get(reverse("book_detail", args=[book_id])), 404)


def test_batched_queries_do_not_grow_with_catalog(diary, adult_client):
    services.rate_book(diary.guardian.reader, finish(diary.adult), 3)
    with CaptureQueriesContext(connection) as small:
        small_response = adult_client.get(reverse("catalog"))
        assert len(small_response.context["books"]) == 1
    for index in range(20):
        book = Book.objects.create(title=f"Synthetic extra {index}", author="Demo", page_count=120, genre="story")
        entry = finish(ShelfEntry.objects.create(reader=diary.guardian.reader, book=book))
        services.rate_book(entry.reader, entry, 4)
    with CaptureQueriesContext(connection) as large:
        response = adult_client.get(reverse("catalog"))
        assert len(response.context["books"]) == 21
        assert len(response.context["personal_ratings"]) == 21
    assert len(large) == len(small)
    with CaptureQueriesContext(connection) as aggregate:
        result = rating_context(list(Book.objects.all()), diary.guardian.reader)
    assert len(aggregate) == 3  # books, grouped aggregate, owner-only ratings
    assert len(result["book_ratings"]) == 21


@pytest.mark.parametrize("rating,status", [(0, "finished"), (6, "finished"), (3, "reading")])
def test_database_constraints_reject_bypassing_service(diary, rating, status):
    if status == "finished":
        finish(diary.adult)
    with pytest.raises(IntegrityError), transaction.atomic():
        ShelfEntry.objects.filter(pk=diary.adult.pk).update(rating=rating)
    diary.adult.refresh_from_db()
    assert diary.adult.rating is None


def test_service_scopes_even_stale_entry(diary):
    finish(diary.child)
    with pytest.raises(ShelfEntry.DoesNotExist):
        services.rate_book(diary.guardian.reader, diary.child, 5)


def test_service_rechecks_persisted_finished_state(diary):
    stale = finish(diary.adult)
    ShelfEntry.objects.filter(pk=stale.pk).update(status="reading", finished_at=None)
    with pytest.raises(ValidationError):
        services.rate_book(diary.guardian.reader, stale, 5)
    stale.refresh_from_db()
    assert stale.rating is None


def test_deleted_active_child_cannot_rate_adult_entry(diary, client):
    finish(diary.adult)
    child_mode(client, diary)
    diary.profile.delete()
    unsaved(client.post(url(diary.adult), {"rating": 5}, **HX), 403)
    diary.adult.refresh_from_db()
    assert diary.adult.rating is None


def test_unexpected_database_error_rolls_back_without_saved(diary, adult_client, monkeypatch):
    entry = finish(diary.adult)
    original = ShelfEntry.save
    def broken_save(self, *args, **kwargs):
        original(self, *args, **kwargs)
        raise IntegrityError("injected unexpected database failure after write")
    monkeypatch.setattr(ShelfEntry, "save", broken_save)
    adult_client.raise_request_exception = False
    response = adult_client.post(url(entry), {"rating": 5}, **HX)
    unsaved(response, 500)
    entry.refresh_from_db()
    assert entry.rating is None


@pytest.mark.django_db(transaction=True)
def test_saved_acknowledgement_follows_actual_commit(diary, adult_client):
    entry = finish(diary.adult)
    commits = []
    def observe(sender, instance, **kwargs):
        assert connection.in_atomic_block
        transaction.on_commit(lambda: commits.append(instance.rating))
    post_save.connect(observe, sender=ShelfEntry)
    try:
        response = adult_client.post(url(entry), {"rating": 4}, **HX)
        assert response.status_code == 204 and response["HX-Trigger"] == "saved"
        assert commits == [4] and not connection.in_atomic_block
    finally:
        post_save.disconnect(observe, sender=ShelfEntry)


@pytest.mark.django_db(transaction=True)
def test_additive_migration_preserves_existing_entry_data(guardian):
    executor = MigrationExecutor(connection)
    before = [("library", "0001_initial")]
    after = [("library", "0002_shelfentry_rating")]
    executor.migrate(before)
    try:
        apps = executor.loader.project_state(before).apps
        OldBook = apps.get_model("library", "Book")
        OldEntry = apps.get_model("library", "ShelfEntry")
        book = OldBook.objects.create(title="Pre-rating", author="Demo", page_count=120, genre="story")
        old = OldEntry.objects.create(reader_id=guardian.reader.pk, book=book, current_page=35)
        executor = MigrationExecutor(connection)
        executor.migrate(after)
        current = ShelfEntry.objects.get(pk=old.pk)
        assert current.public_id == old.public_id
        assert current.current_page == 35 and current.status == "reading" and current.rating is None
        assert current.reader_id == guardian.reader.pk and current.book_id == book.pk
    finally:
        MigrationExecutor(connection).migrate(after)


def rating_race_and_lock():
    # Executed by test_concurrency.run_scenario in an isolated migrated disk DB.
    from apps.library.services import rate_book
    finish_book(reader, entry, uuid.uuid4())
    before = ProgressEvent.objects.count()
    results = concurrent([lambda: rate_book(reader, entry, 1), lambda: rate_book(reader, entry, 5)])
    assert sorted(result.rating for result in results) == [1, 5]
    assert ShelfEntry.objects.count() == 1 and ProgressEvent.objects.count() == before
    assert ShelfEntry.objects.get(pk=entry.pk).rating in {1, 5}
    connection.close()
    settings.DATABASES["default"]["OPTIONS"]["timeout"] = 0.15
    from django.test import Client
    settings.ALLOWED_HOSTS = ["testserver"]
    browser = Client()
    browser.force_login(reader.account)
    previous = ShelfEntry.objects.get(pk=entry.pk).rating
    def attempt():
        close_old_connections()
        try:
            return browser.post(f"/raft/{entry.public_id}/evaluare/", {"rating": 3}, HTTP_HX_REQUEST="true")
        finally:
            connection.close()
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            response = pool.submit(attempt).result(timeout=5)
            assert response.status_code == 503 and response["Retry-After"] == "1"
            assert "HX-Trigger" not in response
            assert ShelfEntry.objects.get(pk=entry.pk).rating == previous
    response = browser.post(f"/raft/{entry.public_id}/evaluare/", {"rating": 3}, HTTP_HX_REQUEST="true")
    assert response.status_code == 204 and response["HX-Trigger"] == "saved"
    assert ShelfEntry.objects.get(pk=entry.pk).rating == 3


def test_file_backed_concurrent_replacement_and_http_lock(tmp_path):
    from tests.test_concurrency import run_scenario
    run_scenario(tmp_path, rating_race_and_lock)
