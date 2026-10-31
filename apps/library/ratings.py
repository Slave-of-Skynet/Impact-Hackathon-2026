"""Batched, privacy-thresholded template data; never expose individual voters."""

from django.db.models import Avg, Count
from django.utils.translation import gettext as _

from apps.library.models import ShelfEntry


def rating_context(books, reader):
    """UUID-keyed maps, independent of frozen BookVM/ShelfEntryVM contracts.

    Both mean and count are suppressed below three distinct readers. The
    existing unique(reader, book) constraint guarantees one vote per reader.
    Query count is independent of catalog size (one aggregate + one owner query).
    """
    book_ids = {book.public_id for book in books}
    public = {book_id: {"average": None, "count": None, "message": _("Nu sunt suficiente evaluări")}
              for book_id in book_ids}
    votes = ShelfEntry.objects.filter(
        book__public_id__in=book_ids, status=ShelfEntry.FINISHED, rating__isnull=False,
    ).values("book__public_id").annotate(average=Avg("rating"), count=Count("rating"))
    for vote in votes:
        if vote["count"] >= 3:
            public[vote["book__public_id"]] = {
                "average": float(vote["average"]), "count": vote["count"], "message": "",
            }
    personal = {}
    if reader is not None:
        personal = dict(ShelfEntry.objects.filter(
            reader=reader, book__public_id__in=book_ids, rating__isnull=False,
        ).values_list("book__public_id", "rating"))
    return {"book_ratings": public, "personal_ratings": personal}
