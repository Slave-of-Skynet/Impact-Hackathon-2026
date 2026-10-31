"""Private book reflection acceptance; real authz, middleware and templates."""

import random
import uuid
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models.signals import post_save
from django.http import QueryDict
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.library import reflections, services
from apps.library.models import Book, BookReflectionAnswer, BookReflectionSet, ProgressEvent, ShelfEntry
from apps.library.reflection_questions import POOL_VERSION, QUESTION_BANK, SOURCE_FRAGMENTS
from tests.conftest import PASSWORD, make_child, make_guardian

pytestmark = pytest.mark.django_db
HX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def diary(guardian, child):
    book = Book.objects.create(title="Cartea gândurilor", author="Autor Demo", page_count=120, genre="story")
    adult_entry, _ = services.add_to_shelf(guardian.reader, book)
    child_entry, _ = services.add_to_shelf(child.reader, book)
    return SimpleNamespace(guardian=guardian, child=child, book=book, adult_entry=adult_entry, child_entry=child_entry)


def url(entry, name="book_reflection"):
    return reverse(name, args=[entry.public_id])


def finished(entry):
    return services.finish_book(entry.reader, entry, uuid.uuid4()).entry


def payload(reflection, text="Un gând păstrat din carte"):
    data = {"revision": reflection.revision}
    for row in reflection.answers.all():
        data[f"question_{row.position}"] = row.question_id
        data[f"answer_{row.position}"] = f"{text} {row.position}" if text else ""
    return data


def stored():
    return (list(BookReflectionSet.objects.order_by("pk").values()),
            list(BookReflectionAnswer.objects.order_by("pk").values()))


def unsaved(response, status):
    assert response.status_code == status
    assert "HX-Trigger" not in response


def enter_child(client, diary):
    client.force_login(diary.guardian)
    assert client.post(reverse("child_mode_start", args=[diary.child.public_id])).status_code == 302


def test_source_fidelity_and_controlled_random_order(diary):
    source = (Path(settings.BASE_DIR) / "docs/contracts/issue-63-question-source.txt").read_text(encoding="utf-8").splitlines()
    assert tuple(source) == SOURCE_FRAGMENTS and len(source) == 16
    assert POOL_VERSION == 1 and len(QUESTION_BANK) == 15
    assert list(QUESTION_BANK.values()) == [" ".join(source[:2]), *source[2:]]
    class ControlledRng:
        def sample(self, population, count):
            assert len(population) == 15 and count == 4
            return [1, 16, 7, 11]
        def shuffle(self, values):
            values.reverse()
    entry = finished(diary.child_entry)
    reflection = reflections.start_set(entry.reader, entry, 0, rng=ControlledRng())
    assert list(reflection.answers.values_list("question_id", flat=True)) == [11, 7, 16, 1]
    assert list(reflection.answers.values_list("position", flat=True)) == [1, 2, 3, 4]
    initial = stored()
    expected = random.Random(13).sample(tuple(QUESTION_BANK), 4)
    generator = random.Random(13)
    generator.sample(tuple(QUESTION_BANK), 4)
    generator.shuffle(expected)
    next_set = reflections.start_set(entry.reader, entry, 1, rng=random.Random(13))
    assert list(next_set.answers.values_list("question_id", flat=True)) == expected
    assert next_set.revision == 2 and BookReflectionSet.objects.count() == 1
    assert len(set(expected)) == 4
    assert initial != stored()  # explicit redraw changes revision, not a flaky RNG inequality


@pytest.mark.parametrize("is_child", [False, True])
@pytest.mark.parametrize("htmx", [False, True])
def test_real_finish_start_save_edit_refresh_and_report(diary, client, is_child, htmx):
    if is_child:
        enter_child(client, diary)
    else:
        client.force_login(diary.guardian)
    entry = diary.child_entry if is_child else diary.adult_entry
    page = client.get(url(entry))
    assert page.status_code == 200 and not BookReflectionSet.objects.exists()
    assert "Alege patru".encode() not in page.content
    assert client.post(reverse("finish_book", args=[entry.public_id]), {"request_id": uuid.uuid4()}).status_code == 302
    entry_page = client.get(reverse("shelf_entry", args=[entry.public_id]))
    assert url(entry).encode() in entry_page.content  # reachable even after HTMX finish
    headers = HX if htmx else {}
    created = client.post(url(entry, "start_reflection"), {"revision": 0}, **headers)
    assert created.status_code == (204 if htmx else 302)
    reflection = BookReflectionSet.objects.get(entry=entry)
    ids = list(reflection.answers.values_list("question_id", flat=True))
    assert len(ids) == len(set(ids)) == 4
    before = stored()
    for _ in range(3):
        assert client.get(url(entry)).status_code == 200
    assert stored() == before
    for prefix in ("Primul răspuns", "Răspuns editat"):
        reflection.refresh_from_db()
        response = client.post(url(entry, "save_reflection"), payload(reflection, prefix), **headers)
        assert response.status_code == (204 if htmx else 302)
        if htmx:
            assert response["HX-Trigger"] == "saved" and response.content == b""
            assert response["HX-Redirect"] == url(entry)
        else:
            assert response["Location"] == url(entry)
        refreshed = client.get(url(entry))
        assert prefix.encode() in refreshed.content
        assert "Răspunsurile au fost salvate.".encode() in refreshed.content
        assert "private" in refreshed["Cache-Control"] and "no-store" in refreshed["Cache-Control"]
        assert list(reflection.answers.values_list("question_id", flat=True)) == ids
    other = Client()
    assert other.post(reverse("login"), {"username": diary.guardian.email, "password": PASSWORD}).status_code == 302
    if is_child:
        assert other.post(reverse("child_mode_start", args=[diary.child.public_id])).status_code == 302
    assert "Răspuns editat".encode() in other.get(url(entry)).content
    if is_child:
        parent = Client()
        parent.force_login(diary.guardian)
        report = parent.get(reverse("child_report", args=[diary.child.public_id]))
        assert "Răspuns editat".encode() in report.content
        assert b"book_reflections" not in report.content
        assert b"textarea" not in report.content and b"ganduri/salveaza" not in report.content
        unsaved(parent.post(url(entry, "save_reflection"), payload(reflection)), 404)
    assert BookReflectionSet.objects.count() == 1 and BookReflectionAnswer.objects.count() == 4
    assert ProgressEvent.objects.filter(entry=entry).count() == 1


@pytest.mark.parametrize("mutation", ["long", "missing", "empty", "wrong_id", "other_valid_id", "duplicate_id", "extra", "missing_answer", "fifth", "nested", "bad_revision", "duplicate_field"])
def test_invalid_form_retains_text_without_partial_write(diary, adult_client, mutation):
    entry = finished(diary.adult_entry)
    reflection = reflections.start_set(entry.reader, entry, 0, rng=random.Random(5))
    fields = payload(reflection, "Păstrează acest text")
    if mutation == "long":
        fields["answer_2"] = "L" * 2001
    elif mutation == "missing":
        fields = {}
    elif mutation == "empty":
        fields = payload(reflection, "")
    elif mutation == "wrong_id":
        fields["question_2"] = 999
    elif mutation == "other_valid_id":
        fields["question_2"] = next(question for question in QUESTION_BANK if question not in {
            fields[f"question_{i}"] for i in range(1, 5)
        })
    elif mutation == "duplicate_id":
        fields["question_2"] = fields["question_1"]
    elif mutation == "extra":
        fields["reader_id"] = diary.child.reader.pk
    elif mutation == "missing_answer":
        del fields["answer_3"]
    elif mutation == "fifth":
        fields["answer_5"] = "A fifth answer"
    elif mutation == "nested":
        fields["answers[2]"] = "No nested fields"
    elif mutation == "bad_revision":
        fields["revision"] = "oops"
    before = stored()
    if mutation == "duplicate_field":
        data = QueryDict("", mutable=True)
        data.update(fields)
        data.appendlist("answer_1", "duplicate")
        response = adult_client.post(url(entry, "save_reflection"), data.urlencode(),
                                     content_type="application/x-www-form-urlencoded", **HX)
    else:
        response = adult_client.post(url(entry, "save_reflection"), fields, **HX)
    unsaved(response, 422)
    assert stored() == before and b'id="reflection-region"' in response.content
    if mutation not in ("missing", "empty", "duplicate_field"):
        assert "Păstrează acest text".encode() in response.content
    assert "Răspunsurile au fost salvate.".encode() not in response.content


def test_2000_limit_partial_answers_and_xss_escaping(diary, adult_client):
    entry = finished(diary.adult_entry)
    reflection = reflections.start_set(entry.reader, entry, 0)
    fields = payload(reflection, "")
    fields["answer_1"] = "x" * 2000
    fields["answer_2"] = '<script>alert("private")</script>'
    assert adult_client.post(url(entry, "save_reflection"), fields).status_code == 302
    content = adult_client.get(url(entry)).content.decode()
    assert "x" * 2000 in content and "&lt;script&gt;" in content
    assert '<script>alert("private")</script>' not in content
    assert BookReflectionAnswer.objects.filter(text="").count() == 2


def test_native_422_retains_text_and_never_reuses_old_saved_message(diary, adult_client):
    entry = finished(diary.adult_entry)
    reflection = reflections.start_set(entry.reader, entry, 0)
    assert adult_client.post(url(entry, "save_reflection"), payload(reflection)).status_code == 302
    reflection.refresh_from_db()
    fields = payload(reflection, "Text nesalvat păstrat")
    fields["answer_2"] = "x" * 2001
    response = adult_client.post(url(entry, "save_reflection"), fields)
    unsaved(response, 422)
    assert "Text nesalvat păstrat".encode() in response.content
    assert "Răspunsurile au fost salvate.".encode() not in response.content


def test_five_sessions_revision_conflict_and_no_answered_reset(diary):
    entry = finished(diary.child_entry)
    reflection = reflections.start_set(entry.reader, entry, 0)
    browsers = [Client() for _ in range(5)]
    for browser in browsers:
        assert browser.post(reverse("login"), {"username": diary.guardian.email, "password": PASSWORD}).status_code == 302
        assert browser.post(reverse("child_mode_start", args=[diary.child.public_id])).status_code == 302
        assert browser.get(url(entry)).status_code == 200
    old_fields = payload(reflection, "Text vechi din altă filă")
    assert browsers[0].post(url(entry, "save_reflection"), payload(reflection, "Text deja salvat")).status_code == 302
    before = stored()
    response = browsers[1].post(url(entry, "save_reflection"), old_fields)
    unsaved(response, 409)
    assert "Text vechi din altă filă".encode() in response.content
    assert "Copiază textul tău".encode() in response.content
    assert stored() == before
    reflection.refresh_from_db()
    unsaved(browsers[2].post(url(entry, "start_reflection"), {"revision": reflection.revision}), 422)
    assert stored() == before
    for browser in browsers[2:]:
        assert "Text deja salvat".encode() in browser.get(url(entry)).content


def test_redraw_conflict_keeps_original_prompt_and_text(diary, adult_client):
    entry = finished(diary.adult_entry)
    reflection = reflections.start_set(entry.reader, entry, 0, rng=random.Random(1))
    fields = payload(reflection, "Text pentru întrebarea inițială")
    original_ids = list(reflection.answers.values_list("question_id", flat=True))
    reflections.start_set(entry.reader, entry, 1, rng=random.Random(2))
    before = stored()
    response = adult_client.post(url(entry, "save_reflection"), fields)
    unsaved(response, 409)
    form = response.context["reflection_form"]
    assert [row["question_id"] for row in form.rows] == original_ids
    assert "Text pentru întrebarea inițială".encode() in response.content
    assert stored() == before


@pytest.mark.parametrize("is_child", [False, True])
def test_real_ownership_report_isolation_and_pin_denial(diary, client, is_child):
    own = diary.child_entry if is_child else diary.adult_entry
    other = diary.adult_entry if is_child else diary.child_entry
    sibling = make_child(diary.guardian, "Alex")
    foreign = make_guardian("other-reflection@demo.local")
    foreign_child = make_child(foreign)
    entries = [own, other, ShelfEntry.objects.create(reader=sibling.reader, book=diary.book),
               ShelfEntry.objects.create(reader=foreign_child.reader, book=diary.book)]
    for entry in entries:
        finished(entry)
        reflection = reflections.start_set(entry.reader, entry, 0)
        data = payload(reflection, f"Private marker {entry.public_id}")
        reflections.save_answers(entry.reader, entry, reflection.revision,
                                 [data[f"question_{i}"] for i in range(1, 5)],
                                 [data[f"answer_{i}"] for i in range(1, 5)])
    if is_child:
        enter_child(client, diary)
    else:
        client.force_login(diary.guardian)
    before = stored()
    for entry in entries[1:]:
        unsaved(client.get(url(entry)), 404)
        for name in ("start_reflection", "save_reflection"):
            unsaved(client.post(url(entry, name), {"revision": 0}, **HX), 404)
    unsaved(client.get(reverse("book_reflection", args=[uuid.uuid4()])), 404)
    assert stored() == before
    if is_child:
        for path in ("/panou/", "/familie/", "/admin/", "/club/cod/", "/not-allowed/"):
            unsaved(client.post(path, **HX), 403)
        assert b'name="pin"' in client.get(reverse("pin_gate")).content
        assert client.session["mode"] == "child"
        diary.child.delete()
        unsaved(client.post(url(own, "start_reflection"), {"revision": 0}, **HX), 403)
    else:
        unsaved(client.get(reverse("child_report", args=[foreign_child.public_id])), 404)
        # Sibling's report contains only sibling text; not active child or adult data.
        report = client.get(reverse("child_report", args=[sibling.public_id]))
        assert str(entries[2].public_id).encode() in report.content
        assert str(entries[0].public_id).encode() not in report.content
        for route in (reverse("catalog"), reverse("book_detail", args=[diary.book.public_id])):
            assert b"Private marker" not in client.get(route).content


@pytest.mark.parametrize("is_child", [False, True])
def test_csrf_get_anonymous_and_real_session_expiry(diary, is_child):
    entry = finished(diary.child_entry if is_child else diary.adult_entry)
    browser = Client(enforce_csrf_checks=True)
    browser.force_login(diary.guardian)
    browser.get(reverse("family"))
    token = browser.cookies[settings.CSRF_COOKIE_NAME].value
    if is_child:
        assert browser.post(reverse("child_mode_start", args=[diary.child.public_id]), {"csrfmiddlewaretoken": token}).status_code == 302
    for name in ("start_reflection", "save_reflection"):
        unsaved(browser.get(url(entry, name)), 405)
        unsaved(browser.post(url(entry, name), {"revision": 0}, **HX), 403)
    assert not BookReflectionSet.objects.exists()
    assert browser.post(url(entry, "start_reflection"), {"revision": 0, "csrfmiddlewaretoken": token}).status_code == 302
    reflection = BookReflectionSet.objects.get(entry=entry)
    data = {**payload(reflection), "csrfmiddlewaretoken": token}
    unsaved(browser.post(url(entry, "save_reflection"), payload(reflection), **HX), 403)
    Session.objects.filter(session_key=browser.session.session_key).update(expire_date=timezone.now() - timedelta(seconds=1))
    before = stored()
    unsaved(browser.post(url(entry, "save_reflection"), data, **HX), 401)
    unsaved(browser.get(url(entry)), 302)
    anonymous = Client()
    for name in ("start_reflection", "save_reflection"):
        unsaved(anonymous.post(url(entry, name), {}, **HX), 401)
    assert stored() == before


def test_no_start_before_finish_and_no_stale_service_bypass(diary, adult_client):
    before = stored()
    unsaved(adult_client.post(url(diary.adult_entry, "start_reflection"), {"revision": 0}), 422)
    assert stored() == before
    entry = finished(diary.adult_entry)
    reflection = reflections.start_set(entry.reader, entry, 0)
    data = payload(reflection)
    with pytest.raises(ShelfEntry.DoesNotExist):
        reflections.save_answers(diary.child.reader, entry, reflection.revision,
                                 [data[f"question_{i}"] for i in range(1, 5)], ["a"] * 4)
    ShelfEntry.objects.filter(pk=entry.pk).update(status="reading", finished_at=None)
    with pytest.raises(ValidationError):
        reflections.start_set(entry.reader, entry, reflection.revision)


@pytest.mark.parametrize("is_child", [False, True])
def test_integrated_ratings_and_reading_remain_independent(diary, client, is_child):
    if is_child:
        enter_child(client, diary)
    else:
        client.force_login(diary.guardian)
    entry = diary.child_entry if is_child else diary.adult_entry
    key = uuid.uuid4()
    finish_url = reverse("finish_book", args=[entry.public_id])
    assert client.post(finish_url, {"request_id": key}, **HX).status_code == 200
    rating_url = reverse("rate_book", args=[entry.public_id])
    assert client.post(rating_url, {"rating": 3}).status_code == 302
    assert client.post(url(entry, "start_reflection"), {"revision": 0}).status_code == 302
    reflection = BookReflectionSet.objects.get(entry=entry)
    assert client.post(url(entry, "save_reflection"), payload(reflection, "Private integration answer")).status_code == 302
    before = stored()
    assert client.post(rating_url, {"rating": 5}, **HX).status_code == 204
    assert client.post(finish_url, {"request_id": key}, **HX).status_code == 200  # exact replay
    assert stored() == before
    entry.refresh_from_db()
    assert entry.rating == 5 and entry.status == "finished" and entry.current_page == 120
    assert ProgressEvent.objects.filter(entry=entry).count() == 1
    catalog = client.get(reverse("catalog"))
    assert catalog.context["personal_ratings"] == {entry.book.public_id: 5}
    assert catalog.context["book_ratings"][entry.book.public_id]["average"] is None
    assert b"Private integration answer" not in catalog.content


def test_batched_parent_report_queries(diary):
    entry = finished(diary.child_entry)
    reflections.start_set(entry.reader, entry, 0)
    with CaptureQueriesContext(connection) as first:
        assert len(reflections.reader_reflections(entry.reader)) == 1
    for i in range(6):
        book = Book.objects.create(title=f"Other {i}", author="Demo", page_count=120, genre="story")
        another = finished(ShelfEntry.objects.create(reader=entry.reader, book=book))
        reflections.start_set(another.reader, another, 0)
    with CaptureQueriesContext(connection) as more:
        assert len(reflections.reader_reflections(entry.reader)) == 7
    assert len(first) == len(more) == 2


@pytest.mark.parametrize("change", [{"position": 5}, {"question_id": 2}, {"text": "x" * 2001}])
def test_database_checks_bypass(diary, change):
    entry = finished(diary.adult_entry)
    reflection = reflections.start_set(entry.reader, entry, 0)
    row = reflection.answers.first()
    with pytest.raises(IntegrityError), transaction.atomic():
        BookReflectionAnswer.objects.filter(pk=row.pk).update(**change)


def test_unexpected_database_error_rolls_back_no_saved(diary, adult_client, monkeypatch):
    entry = finished(diary.adult_entry)
    reflection = reflections.start_set(entry.reader, entry, 0)
    before = stored()
    original = BookReflectionSet.save
    def fail_after_save(self, *args, **kwargs):
        original(self, *args, **kwargs)
        raise IntegrityError("Injected failure, no private text in error")
    monkeypatch.setattr(BookReflectionSet, "save", fail_after_save)
    adult_client.raise_request_exception = False
    unsaved(adult_client.post(url(entry, "save_reflection"), payload(reflection), **HX), 500)
    assert stored() == before


@pytest.mark.django_db(transaction=True)
def test_commit_acknowledgement_and_additive_migration(diary, adult_client):
    from django.db.migrations.executor import MigrationExecutor
    before_model = (diary.adult_entry.public_id, diary.adult_entry.current_page)
    executor = MigrationExecutor(connection)
    original_leaves = executor.loader.graph.leaf_nodes()
    executor.migrate([("library", "0001_initial")])
    try:
        MigrationExecutor(connection).migrate(original_leaves)
        diary.adult_entry.refresh_from_db()
        assert (diary.adult_entry.public_id, diary.adult_entry.current_page) == before_model
        assert BookReflectionSet.objects.count() == 0
    finally:
        MigrationExecutor(connection).migrate(original_leaves)
    entry = finished(diary.adult_entry)
    commits = []
    def observe(sender, instance, **kwargs):
        assert connection.in_atomic_block
        transaction.on_commit(lambda: commits.append(instance.revision))
    post_save.connect(observe, sender=BookReflectionSet)
    try:
        response = adult_client.post(url(entry, "start_reflection"), {"revision": 0}, **HX)
        assert response.status_code == 204 and response["HX-Trigger"] == "saved" and commits == [1]
        reflection = BookReflectionSet.objects.get(entry=entry)
        response = adult_client.post(url(entry, "save_reflection"), payload(reflection), **HX)
        assert response.status_code == 204 and response["HX-Trigger"] == "saved" and commits == [1, 2]
        assert not connection.in_atomic_block
    finally:
        post_save.disconnect(observe, sender=BookReflectionSet)


def reflection_race_and_lock():
    from apps.library import reflections
    from apps.library.models import BookReflectionSet
    finish_book(reader, entry, uuid.uuid4())
    def create():
        try:
            return reflections.start_set(reader, entry, 0)
        except reflections.RevisionConflict:
            return "conflict"
    results = concurrent([create, create])
    assert results.count("conflict") == 1 and BookReflectionSet.objects.count() == 1
    reflection = BookReflectionSet.objects.get(entry=entry)
    ids = list(reflection.answers.values_list("question_id", flat=True))
    def save(text):
        try:
            return reflections.save_answers(reader, entry, 1, ids, [text] * 4)
        except reflections.RevisionConflict:
            return "conflict"
    results = concurrent([lambda: save("a"), lambda: save("b")])
    assert results.count("conflict") == 1
    reflection.refresh_from_db()
    assert reflection.revision == 2 and len(set(reflection.answers.values_list("text", flat=True))) == 1
    connection.close()
    settings.DATABASES["default"]["OPTIONS"]["timeout"] = 0.15
    from django.test import Client
    settings.ALLOWED_HOSTS = ["testserver"]
    browser = Client()
    browser.force_login(reader.account)
    fields = {"revision": 2}
    for row in reflection.answers.all():
        fields[f"question_{row.position}"] = row.question_id
        fields[f"answer_{row.position}"] = "retry"
    def attempt():
        close_old_connections()
        try:
            return browser.post(f"/raft/{entry.public_id}/ganduri/salveaza/", fields, HTTP_HX_REQUEST="true")
        finally:
            connection.close()
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            response = pool.submit(attempt).result(timeout=5)
            assert response.status_code == 503 and "HX-Trigger" not in response
            assert BookReflectionSet.objects.get(pk=reflection.pk).revision == 2
    assert browser.post(f"/raft/{entry.public_id}/ganduri/salveaza/", fields, HTTP_HX_REQUEST="true").status_code == 204
    assert list(reflection.answers.values_list("text", flat=True)) == ["retry"] * 4


def test_file_backed_create_save_races_and_lock_timeout(tmp_path):
    from tests.test_concurrency import run_scenario
    run_scenario(tmp_path, reflection_race_and_lock)
