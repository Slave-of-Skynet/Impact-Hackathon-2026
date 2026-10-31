"""Private native-form reflection flow, with explicit HTMX status semantics."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_GET, require_POST

from apps.library import reflections, services
from apps.library.models import BookReflectionSet, ShelfEntry
from apps.library.reflection_forms import ReflectionAnswersForm, StartReflectionForm
from apps.library.reflection_questions import QUESTION_POOLS
from apps.library.views import _entry_vm, _get_entry, _htmx, _mode, _unsaved, _with_reader


def _render(request, entry, *, form=None, start_form=None, error=None, status=200):
    reflection = reflections.get_set(entry)
    rows = reflections.questions(reflection)
    notices = list(messages.get_messages(request))
    context = {
        "entry": _entry_vm(entry), "reflection": reflection,
        "reflection_form": form if form is not None else ReflectionAnswersForm(
            rows=rows, initial={"revision": reflection.revision if reflection else 0},
        ),
        "start_form": start_form if start_form is not None else StartReflectionForm(
            initial={"revision": reflection.revision if reflection else 0},
        ),
        "has_answers": any(row["answer"] for row in rows), "reflection_error": error,
        "can_reflect": entry.status == ShelfEntry.FINISHED,
        "is_child_reader": _mode(request) == "child",
        "reflection_messages": notices if request.method == "GET" and status == 200 else [],
        # Adult base has a global toast include. Handle our notices only here,
        # so a previous successful POST cannot look like this rejected save.
        "messages": [notice for notice in notices if "reflection" not in notice.tags],
    }
    template = "library/_reflection_form.html" if _htmx(request) else f"{_mode(request)}/reflection.html"
    return render(request, template, context, status=status)


def _committed(request, entry, message):
    # The service has exited its transaction successfully before this point.
    messages.success(request, message, extra_tags="reflection")
    target = reverse("book_reflection", args=[entry.public_id])
    if _htmx(request):
        return HttpResponse(status=204, headers={"HX-Redirect": target, "HX-Trigger": "saved"})
    return redirect(target)


@never_cache
@require_GET
@_with_reader()
def book_reflection(request, reader, entry):
    return _render(request, _get_entry(reader, entry))


@sensitive_post_parameters("answer_1", "answer_2", "answer_3", "answer_4")
@never_cache
@require_POST
@csrf_protect
@_with_reader()
def start_reflection(request, reader, entry):
    current = _get_entry(reader, entry)
    form = StartReflectionForm(request.POST)
    if not form.is_valid():
        return _render(request, current, start_form=form, status=422)
    try:
        reflections.start_set(reader, current, form.cleaned_data["revision"])
    except ValidationError as error:
        return _render(request, current, start_form=form, error=" ".join(error.messages), status=422)
    except reflections.RevisionConflict:
        return _render(request, current, start_form=form,
                       error=_("Setul a fost modificat pe alt dispozitiv. Reîncarcă pagina."), status=409)
    except ShelfEntry.DoesNotExist:
        raise Http404 from None
    except services.LockTimeout:
        return _unsaved(503)
    return _committed(request, current, _("Întrebările sunt pregătite. Poți răspunde în ritmul tău."))


@sensitive_post_parameters("answer_1", "answer_2", "answer_3", "answer_4")
@never_cache
@require_POST
@csrf_protect
@_with_reader()
def save_reflection(request, reader, entry):
    current = _get_entry(reader, entry)
    reflection = reflections.get_set(current)
    if reflection is None:
        raise Http404
    rows = reflections.questions(reflection)
    # A different tab may have redrawn an unanswered set. Preserve the submitted
    # text under its ORIGINAL canonical prompt, never under the newly drawn one.
    # The service still checks persisted order and revision inside its locks.
    try:
        submitted_ids = [int(request.POST[f"question_{i}"]) for i in range(1, 5)]
    except (KeyError, ValueError, TypeError):
        submitted_ids = []
    pool = QUESTION_POOLS[reflection.pool_version]
    if len(set(submitted_ids)) == 4 and all(question in pool for question in submitted_ids):
        rows = [{"position": i, "question_id": question, "question": pool[question], "answer": ""}
                for i, question in enumerate(submitted_ids, start=1)]
    form = ReflectionAnswersForm(request.POST, rows=rows)
    if not form.is_valid():
        return _render(request, current, form=form, status=422)
    try:
        reflections.save_answers(
            reader, current, form.cleaned_data["revision"],
            [form.cleaned_data[f"question_{i}"] for i in range(1, 5)],
            [form.cleaned_data[f"answer_{i}"] for i in range(1, 5)],
        )
    except ValidationError as error:
        return _render(request, current, form=form, error=" ".join(error.messages), status=422)
    except reflections.RevisionConflict:
        return _render(request, current, form=form, error=_(
            "Răspunsurile au fost modificate pe alt dispozitiv. Copiază textul tău înainte de a reîncărca pagina."
        ), status=409)
    except (ShelfEntry.DoesNotExist, BookReflectionSet.DoesNotExist):
        raise Http404 from None
    except services.LockTimeout:
        return _unsaved(503)
    return _committed(request, current, _("Răspunsurile au fost salvate."))
