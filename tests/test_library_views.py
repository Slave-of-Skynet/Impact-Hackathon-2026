"""Route/context tests with explicit test-only authz and template contracts.

These mocks do not prove the pending accounts middleware or real UI integration.
They let the library owner verify the routes without copying either workstream.
"""

import sys
import types
import uuid
from unittest.mock import Mock

import pytest
from django.conf import settings
from django.db import connection
from django.shortcuts import get_object_or_404
from django.test import Client
from django.urls import reverse

from apps.accounts.models import Account, ChildProfile, Reader
from apps.club.models import Achievement, AchievementGrant
from apps.core.viewmodels import BookVM, GrantVM, MascotLine, ShelfEntryVM, StatsVM
from apps.library import services, views
from apps.library.models import Book, ProgressEvent, ShelfEntry

pytestmark = pytest.mark.django_db


@pytest.fixture
def ui_contract(settings):
    """Deliberately tiny fixtures; no adult/child template files are created."""
    catalog = "{% csrf_token %}{% for book in books %}{{ book.title }} {{ book.public_id }}{% endfor %}"
    progress = ('{% csrf_token %}<input name="request_id" value="{{ request_id }}">'
                '{{ entry.current_page }}/{{ entry.page_count }}'
                '{% for error in errors %}{{ error }}{% endfor %}'
                '{% for grant in new_grants %}{{ grant.title }}{% endfor %}{{ mascot.text }}')
    shelf = "{% for entry in entries %}{{ entry.book.title }} {{ entry.current_page }}{% endfor %} {{ stats.pages_total }}"
    templates = {}
    for mode in ("adult", "child"):
        templates.update({f"{mode}/catalog.html": catalog, f"{mode}/shelf.html": shelf,
                          f"{mode}/shelf_entry.html": progress, f"{mode}/_progress.html": progress})
    engine = settings.TEMPLATES[0]
    settings.TEMPLATES = [{**engine, "APP_DIRS": False, "OPTIONS": {
        **engine["OPTIONS"], "loaders": [("django.template.loaders.locmem.Loader", templates)],
    }}]


@pytest.fixture
def diary(client, monkeypatch, ui_contract):
    account = Account.objects.create_user("views@demo.local", display_name="Demo")
    reader = Reader.objects.create(kind="adult", account=account)
    child = ChildProfile.objects.create(guardian=account, nickname="Mia", age_band="9-11", avatar="fox")
    child_reader = Reader.objects.create(kind="child", child=child)
    book = Book.objects.create(title="Synthetic 120", author="Demo", page_count=120, genre="story",
                               age_band="9-11", cover_color="#123456", cover_emoji="📚")
    entry, _ = services.add_to_shelf(reader, book)
    authz = types.ModuleType("apps.accounts.authz")
    authz.current_reader = Mock(return_value=reader)
    authz.get_entry_for_reader = Mock(side_effect=lambda owner, public_id: get_object_or_404(
        ShelfEntry.objects.select_related("book"), reader=owner, public_id=public_id,
    ))
    monkeypatch.setitem(sys.modules, "apps.accounts.authz", authz)
    client.force_login(account)
    return types.SimpleNamespace(account=account, reader=reader, child_reader=child_reader,
                                 book=book, entry=entry, authz=authz)


def progress_url(entry):
    return reverse("record_progress", kwargs={"entry": entry.public_id})


def assert_unsaved(response, status):
    assert response.status_code == status
    assert "HX-Trigger" not in response


def test_anonymous_catalog_filters_detail_and_inactive(client, ui_contract):
    first = Book.objects.create(title="Public story", author="Demo", page_count=120, genre="story", age_band="9-11")
    Book.objects.create(title="Public poem", author="Demo", page_count=20, genre="poetry", age_band="7-8")
    inactive = Book.objects.create(title="Hidden", author="Demo", page_count=120, genre="story", is_active=False)
    response = client.get(reverse("catalog"), {"age_band": "9-11", "genre": "story"})
    assert response.status_code == 200
    assert response.templates[0].name == "adult/catalog.html"
    assert response.context["books"] == [views._book_vm(first)]
    assert isinstance(response.context["books"][0], BookVM)
    assert response.context["filters"] == {"age_band": "9-11", "genre": "story"}
    assert response.context["shelf_book_ids"] == set()
    detail = client.get(reverse("book_detail", args=[first.public_id]))
    assert detail.status_code == 200 and detail.context["books"] == [views._book_vm(first)]
    assert client.get(reverse("book_detail", args=[inactive.public_id])).status_code == 404
    assert client.get(reverse("book_detail", args=[uuid.uuid4()])).status_code == 404


def test_adult_shelf_context_and_render_uuid(diary, client):
    shelf = client.get(reverse("my_shelf"))
    assert shelf.status_code == 200 and shelf.templates[0].name == "adult/shelf.html"
    assert isinstance(shelf.context["entries"][0], ShelfEntryVM)
    assert shelf.context["stats"] == StatsVM(1, 0, 0, 0)
    page = client.get(reverse("shelf_entry", args=[diary.entry.public_id]))
    assert page.status_code == 200 and page.templates[0].name == "adult/shelf_entry.html"
    uuid.UUID(str(page.context["request_id"]))
    assert page.context["new_grants"] == [] and page.context["errors"] == []
    assert "mascot" not in page.context
    assert "HX-Trigger" not in page
    catalog = client.get(reverse("catalog"))
    assert catalog.context["shelf_book_ids"] == {diary.book.public_id}
    diary.authz.current_reader.assert_called()


def test_plain_form_post_redirects_then_shows_stored_35(diary, client):
    before = client.get(reverse("shelf_entry", args=[diary.entry.public_id]))
    key = before.context["request_id"]
    response = client.post(progress_url(diary.entry), {"page": 35, "request_id": key})
    assert response.status_code == 302
    assert response["Location"] == reverse("shelf_entry", args=[diary.entry.public_id])
    after = client.get(response["Location"])
    assert after.status_code == 200 and b"35/120" in after.content
    assert after.context["request_id"] != key
    assert client.get(reverse("my_shelf")).context["stats"].pages_total == 35


def test_htmx_save_replay_conflict_and_request_id_rotation(diary, client):
    key = uuid.uuid4()
    response = client.post(progress_url(diary.entry), {"page": 35, "request_id": key}, HTTP_HX_REQUEST="true")
    assert response.status_code == 200 and response["HX-Trigger"] == "saved"
    assert response.templates[0].name == "adult/_progress.html"
    assert response.context["entry"].current_page == 35 and response.context["request_id"] != key
    replay = client.post(progress_url(diary.entry), {"page": 35, "request_id": key}, HTTP_HX_REQUEST="true")
    assert replay.status_code == 200 and replay["HX-Trigger"] == "saved"
    assert replay.context["new_grants"] == [] and ProgressEvent.objects.count() == 1
    conflict = client.post(progress_url(diary.entry), {"page": 36, "request_id": key}, HTTP_HX_REQUEST="true")
    assert_unsaved(conflict, 409)
    assert b"request_id" not in conflict.content
    diary.entry.refresh_from_db()
    assert diary.entry.current_page == 35 and ProgressEvent.objects.count() == 1


@pytest.mark.parametrize("page", [-1, 121, "NaN", "35.5", ""])
@pytest.mark.parametrize("htmx", [False, True])
def test_422_keeps_request_id_and_does_not_write(diary, client, page, htmx):
    key = str(uuid.uuid4())
    headers = {"HTTP_HX_REQUEST": "true"} if htmx else {}
    response = client.post(progress_url(diary.entry), {"page": page, "request_id": key}, **headers)
    assert_unsaved(response, 422)
    assert response.context["request_id"] == key and response.context["errors"]
    assert response.context["entry"].current_page == 0
    assert response.templates[0].name == ("adult/_progress.html" if htmx else "adult/shelf_entry.html")
    assert ProgressEvent.objects.count() == 0


@pytest.mark.parametrize("payload", [{"page": 35}, {"page": 35, "request_id": "bad"}])
def test_invalid_request_uuid_is_422(diary, client, payload):
    response = client.post(progress_url(diary.entry), payload, HTTP_HX_REQUEST="true")
    assert_unsaved(response, 422)
    assert response.context["request_id"] == payload.get("request_id", "")
    assert not ProgressEvent.objects.exists()


@pytest.mark.parametrize("page", [0, 120])
def test_page_boundaries_and_terminal_progress(diary, client, page):
    key = uuid.uuid4()
    response = client.post(progress_url(diary.entry), {"page": page, "request_id": key}, HTTP_HX_REQUEST="true")
    assert response.status_code == 200 and response.context["entry"].current_page == page
    if page == 120:
        assert response.context["entry"].status == "finished"
        rejected = client.post(progress_url(diary.entry), {"page": 35, "request_id": uuid.uuid4()}, HTTP_HX_REQUEST="true")
        assert_unsaved(rejected, 422)


def test_finish_once_replay_and_new_id_rejected(diary, client):
    key = uuid.uuid4()
    url = reverse("finish_book", args=[diary.entry.public_id])
    for _ in range(2):
        response = client.post(url, {"request_id": key}, HTTP_HX_REQUEST="true")
        assert response.status_code == 200 and response["HX-Trigger"] == "saved"
        assert response.context["entry"].current_page == 120
    rejected = client.post(url, {"request_id": uuid.uuid4()}, HTTP_HX_REQUEST="true")
    assert_unsaved(rejected, 422)
    assert ProgressEvent.objects.filter(kind="finish").count() == 1


def test_add_duplicate_inactive_and_server_reader(diary, client):
    url = reverse("add_to_shelf", args=[diary.book.public_id])
    for _ in range(2):
        response = client.post(url, {"reader": diary.child_reader.public_id}, HTTP_HX_REQUEST="true")
        assert response.status_code == 200 and response["HX-Trigger"] == "saved"
    assert ShelfEntry.objects.count() == 1 and not ProgressEvent.objects.exists()
    assert not ShelfEntry.objects.filter(reader=diary.child_reader).exists()
    Book.objects.filter(pk=diary.book.pk).update(is_active=False)
    assert_unsaved(client.post(url, HTTP_HX_REQUEST="true"), 404)


def test_child_templates_use_current_reader_and_documented_mascot(diary, client):
    diary.authz.current_reader.return_value = diary.child_reader
    session = client.session
    session["mode"] = "child"
    session["active_child"] = str(diary.child_reader.public_id)
    session.save()
    add = client.post(reverse("add_to_shelf", args=[diary.book.public_id]), HTTP_HX_REQUEST="true")
    assert add.status_code == 200 and add.templates[0].name == "child/_progress.html"
    entry = ShelfEntry.objects.get(reader=diary.child_reader)
    assert client.get(reverse("catalog")).templates[0].name == "child/catalog.html"
    assert client.get(reverse("my_shelf")).templates[0].name == "child/shelf.html"
    page = client.get(reverse("shelf_entry", args=[entry.public_id]))
    assert page.templates[0].name == "child/shelf_entry.html"
    assert isinstance(page.context["mascot"], MascotLine)
    response = client.post(progress_url(entry), {"page": 35, "request_id": uuid.uuid4()}, HTTP_HX_REQUEST="true")
    assert response.status_code == 200 and response.context["mascot"].key == "progress_saved"
    invalid = client.post(progress_url(entry), {"page": -1, "request_id": uuid.uuid4()}, HTTP_HX_REQUEST="true")
    assert_unsaved(invalid, 422)
    assert invalid.context["mascot"].key == "error"
    finish = client.post(reverse("finish_book", args=[entry.public_id]), {"request_id": uuid.uuid4()}, HTTP_HX_REQUEST="true")
    assert finish.status_code == 200 and finish.context["mascot"].key == "book_finished"
    foreign = client.post(progress_url(diary.entry), {"page": 35, "request_id": uuid.uuid4()}, HTTP_HX_REQUEST="true")
    assert_unsaved(foreign, 404)
    diary.entry.refresh_from_db()
    assert diary.entry.current_page == 0


@pytest.mark.parametrize("child_mode", [False, True])
def test_new_grants_are_view_models_and_replay_does_not_regrant(diary, client, monkeypatch, child_mode):
    entry = diary.entry
    reader = diary.reader
    if child_mode:
        reader = diary.child_reader
        diary.authz.current_reader.return_value = reader
        entry, _ = services.add_to_shelf(reader, diary.book)
        session = client.session
        session["mode"] = "child"
        session["active_child"] = str(reader.public_id)
        session.save()
    achievement = Achievement.objects.create(code="demo-award", title="Synthetic award", description="Demo",
                                             rule="pages_total_gte", threshold=35, icon="demo.svg")
    def evaluate(reader):
        grant = AchievementGrant.objects.create(reader=reader, achievement=achievement)
        return [grant]
    spy = Mock(side_effect=evaluate)
    monkeypatch.setattr(services.club_services, "evaluate_achievements", spy)
    key = uuid.uuid4()
    response = client.post(progress_url(entry), {"page": 35, "request_id": key}, HTTP_HX_REQUEST="true")
    assert isinstance(response.context["new_grants"][0], GrantVM)
    assert response.context["new_grants"][0].code == achievement.code
    if child_mode:
        assert response.context["mascot"].key == "achievement"
    replay = client.post(progress_url(entry), {"page": 35, "request_id": key}, HTTP_HX_REQUEST="true")
    assert replay.context["new_grants"] == []
    assert AchievementGrant.objects.count() == 1
    spy.assert_called_once_with(reader)


def test_foreign_entry_and_unknown_ids_are_404(diary, client):
    foreign_reader = Reader.objects.create(kind="adult", account=Account.objects.create_user("foreign@demo.local"))
    foreign, _ = services.add_to_shelf(foreign_reader, diary.book)
    for entry_id in [foreign.public_id, uuid.uuid4()]:
        assert_unsaved(client.get(reverse("shelf_entry", args=[entry_id])), 404)
        for route in ("record_progress", "finish_book"):
            response = client.post(reverse(route, args=[entry_id]), {"page": 35, "request_id": uuid.uuid4()}, HTTP_HX_REQUEST="true")
            assert_unsaved(response, 404)
            diary.authz.get_entry_for_reader.assert_called_with(diary.reader, entry_id)
    assert not ProgressEvent.objects.exists()


@pytest.mark.parametrize("route", ["record_progress", "finish_book", "add_to_shelf"])
def test_expired_session_htmx_is_401_and_normal_post_goes_to_login(diary, client, route):
    client.logout()
    value = diary.book.public_id if route == "add_to_shelf" else diary.entry.public_id
    url = reverse(route, args=[value])
    response = client.post(url, {"page": 35, "request_id": uuid.uuid4()}, HTTP_HX_REQUEST="true")
    assert_unsaved(response, 401)
    assert response.content == b"" and response["HX-Redirect"].startswith("/cont/intrare/?next=")
    assert "/progres/" not in response["HX-Redirect"]
    assert "/terminat/" not in response["HX-Redirect"]
    normal = client.post(url, {"page": 35, "request_id": uuid.uuid4()})
    assert normal.status_code == 302 and normal["Location"].startswith("/cont/intrare/?next=")
    assert not ProgressEvent.objects.exists()
    diary.authz.current_reader.assert_not_called()


@pytest.mark.parametrize("route", ["record_progress", "finish_book", "add_to_shelf"])
def test_mutations_are_post_only_and_enforce_csrf(diary, client, route):
    value = diary.book.public_id if route == "add_to_shelf" else diary.entry.public_id
    url = reverse(route, args=[value])
    assert_unsaved(client.get(url), 405)
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(diary.account)
    assert_unsaved(strict.post(url, {"page": 35, "request_id": uuid.uuid4()}, HTTP_HX_REQUEST="true"), 403)
    strict.get(reverse("shelf_entry", args=[diary.entry.public_id]))
    csrf_token = strict.cookies[settings.CSRF_COOKIE_NAME].value
    response = strict.post(url, {"page": 35, "request_id": uuid.uuid4(), "csrfmiddlewaretoken": csrf_token}, HTTP_HX_REQUEST="true")
    assert response.status_code == 200 and response["HX-Trigger"] == "saved"


@pytest.mark.parametrize("route", ["record_progress", "finish_book", "add_to_shelf"])
def test_lock_exception_is_503_without_save(diary, client, monkeypatch, route):
    monkeypatch.setattr(services, route, Mock(side_effect=services.LockTimeout))
    value = diary.book.public_id if route == "add_to_shelf" else diary.entry.public_id
    response = client.post(reverse(route, args=[value]), {"page": 35, "request_id": uuid.uuid4()}, HTTP_HX_REQUEST="true")
    assert_unsaved(response, 503)
    assert response["Retry-After"] == "1" and not ProgressEvent.objects.exists()


def test_missing_authz_fails_closed(diary, client, monkeypatch):
    monkeypatch.setitem(sys.modules, "apps.accounts.authz", None)
    response = client.post(progress_url(diary.entry), {"page": 35, "request_id": uuid.uuid4()}, HTTP_HX_REQUEST="true")
    assert_unsaved(response, 503)
    assert not ProgressEvent.objects.exists()


def real_lock_response():
    # Executed in test_concurrency's isolated, migrated file database, with
    # two independent thread-local connections and no in-memory fallback.
    import sys
    import types
    from unittest.mock import Mock
    from django.test import Client
    from django.shortcuts import get_object_or_404

    settings.ALLOWED_HOSTS = ["testserver"]
    authz = types.ModuleType("apps.accounts.authz")
    authz.current_reader = Mock(return_value=reader)
    authz.get_entry_for_reader = Mock(side_effect=lambda owner, public_id: get_object_or_404(
        ShelfEntry, reader=owner, public_id=public_id,
    ))
    sys.modules["apps.accounts.authz"] = authz
    browser = Client()
    browser.force_login(reader.account)
    connection.close()
    settings.DATABASES["default"]["OPTIONS"]["timeout"] = 0.15
    key = uuid.uuid4()
    def attempt():
        close_old_connections()
        try:
            before = time.monotonic()
            response = browser.post(f"/raft/{entry.public_id}/progres/",
                                    {"page": 35, "request_id": key}, HTTP_HX_REQUEST="true")
            return response, time.monotonic() - before
        finally:
            connection.close()
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            response, elapsed = pool.submit(attempt).result(timeout=5)
            assert 0.10 <= elapsed < 3
            assert response.status_code == 503 and "HX-Trigger" not in response
            assert not ProgressEvent.objects.exists()
            assert ShelfEntry.objects.get(pk=entry.pk).current_page == 0
    assert not record_progress(reader, entry, 35, key).replayed
    assert record_progress(reader, entry, 35, key).replayed


def test_real_file_database_lock_returns_503_with_no_partial_write(tmp_path):
    from test_concurrency import run_scenario

    run_scenario(tmp_path, real_lock_response)


@pytest.mark.django_db(transaction=True)
def test_saved_partial_is_rendered_after_real_commit(diary, client, monkeypatch):
    original_render = views.render
    commits = []
    def evaluate(reader):
        from django.db import transaction
        transaction.on_commit(lambda: commits.append("committed"))
        return []
    def render_after_commit(*args, **kwargs):
        assert commits == ["committed"]
        assert not connection.in_atomic_block
        assert ProgressEvent.objects.count() == 1
        return original_render(*args, **kwargs)
    monkeypatch.setattr(services.club_services, "evaluate_achievements", evaluate)
    monkeypatch.setattr(views, "render", render_after_commit)
    response = client.post(progress_url(diary.entry), {"page": 35, "request_id": uuid.uuid4()}, HTTP_HX_REQUEST="true")
    assert response.status_code == 200 and response["HX-Trigger"] == "saved"
