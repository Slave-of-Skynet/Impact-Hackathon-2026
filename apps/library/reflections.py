"""Private reflection persistence. No public aggregates or answer logging."""

import random

from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import Reader
from apps.library.models import BookReflectionAnswer, BookReflectionSet, ShelfEntry
from apps.library.reflection_questions import POOL_VERSION, QUESTION_BANK, QUESTION_POOLS
from apps.library.services import _write_transaction


class RevisionConflict(Exception):
    """Stale device/tab: reject the complete write with HTTP409."""


def _locked_entry(reader, entry):
    # Same lock order as progress: no competing finish/reset can bypass checks.
    Reader.objects.select_for_update().get(pk=reader.pk)
    current = ShelfEntry.objects.select_for_update().get(public_id=entry.public_id, reader=reader)
    if current.status != ShelfEntry.FINISHED:
        raise ValidationError(_("Termină cartea înainte de a răspunde la întrebări."))
    return current


def _check_revision(expected, actual):
    if type(expected) is not int or expected != actual:
        raise RevisionConflict


def start_set(reader, entry, revision, *, rng=None):
    """Explicit create/redraw. Never discard an answer, even via a stale tab."""
    with _write_transaction():
        current = _locked_entry(reader, entry)
        reflection = BookReflectionSet.objects.select_for_update().filter(entry=current).first()
        _check_revision(revision, reflection.revision if reflection else 0)
        if reflection:
            if reflection.answers.exclude(text="").exists():
                raise ValidationError(_("Răspunsurile tale sunt păstrate. Nu poți schimba acest set de întrebări."))
            reflection.answers.all().delete()
            reflection.revision += 1
            reflection.updated_at = timezone.now()
            reflection.save(update_fields=["revision", "updated_at"])
        else:
            reflection = BookReflectionSet.objects.create(entry=current, pool_version=POOL_VERSION)
        generator = rng if rng is not None else random
        selected = generator.sample(tuple(QUESTION_BANK), 4)
        generator.shuffle(selected)
        BookReflectionAnswer.objects.bulk_create([
            BookReflectionAnswer(reflection=reflection, position=index, question_id=question)
            for index, question in enumerate(selected, start=1)
        ])
    return reflection


def save_answers(reader, entry, revision, question_ids, answers):
    """Compare revision and order inside the transaction; no partial saves."""
    if len(answers) != 4 or any(not isinstance(text, str) or len(text) > 2000 for text in answers):
        raise ValidationError(_("Fiecare răspuns poate avea cel mult 2000 de caractere."))
    answers = [text.strip() for text in answers]
    if not any(answers):
        raise ValidationError(_("Scrie cel puțin un răspuns înainte de salvare."))
    with _write_transaction():
        current = _locked_entry(reader, entry)
        reflection = BookReflectionSet.objects.select_for_update().get(entry=current)
        _check_revision(revision, reflection.revision)
        rows = list(reflection.answers.select_for_update().order_by("position"))
        if len(rows) != 4 or list(question_ids) != [row.question_id for row in rows]:
            raise ValidationError(_("Întrebările nu corespund setului salvat. Reîncarcă pagina."))
        for row, text in zip(rows, answers):
            row.text = text
        BookReflectionAnswer.objects.bulk_update(rows, ["text"])
        reflection.revision += 1
        reflection.updated_at = timezone.now()
        reflection.save(update_fields=["revision", "updated_at"])
    return reflection


def get_set(entry):
    return BookReflectionSet.objects.prefetch_related("answers").filter(entry=entry).first()


def questions(reflection):
    if reflection is None:
        return []
    pool = QUESTION_POOLS[reflection.pool_version]
    return [{"position": row.position, "question_id": row.question_id,
             "question": pool[row.question_id], "answer": row.text} for row in reflection.answers.all()]


def reader_reflections(reader):
    """Batched read-only report data, called only after guardian ownership check."""
    sets = BookReflectionSet.objects.filter(entry__reader=reader).select_related("entry__book").prefetch_related(
        Prefetch("answers", queryset=BookReflectionAnswer.objects.order_by("position")),
    ).order_by("-updated_at", "-pk")
    return [{"book_title": reflection.entry.book.title, "questions": questions(reflection),
             "updated_at": reflection.updated_at} for reflection in sets]
