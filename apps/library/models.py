import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Length
from django.db.models.lookups import LessThanOrEqual
from django.utils import timezone

from apps.accounts.models import AGE_BANDS, Reader

BOOK_LANGUAGES = [("ro", "Română"), ("ru", "Русский"), ("en", "English")]
GENRES = [
    ("fairy_tale", "Basme"),
    ("story", "Povestiri"),
    ("adventure", "Aventură"),
    ("animals", "Animale"),
    ("poetry", "Poezie"),
    ("humor", "Umor"),
]


class Book(models.Model):
    """Catalog metadata only; no full texts (FR-010)."""

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=120)
    language = models.CharField(max_length=2, choices=BOOK_LANGUAGES, default="ro")
    page_count = models.PositiveIntegerField()
    age_band = models.CharField(max_length=5, choices=AGE_BANDS, blank=True, null=True)
    genre = models.CharField(max_length=20, choices=GENRES)
    cover_color = models.CharField(max_length=7, help_text="Hex colour of the generated cover, e.g. #F4A261.")
    cover_emoji = models.CharField(max_length=8)
    source_note = models.CharField(max_length=300, help_text="Where the metadata came from / rights note.")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(page_count__gte=1, page_count__lte=2000), name="book_page_count_range"
            ),
        ]

    def __str__(self):
        return f"{self.title} — {self.author}"


class ShelfEntry(models.Model):
    READING, FINISHED = "reading", "finished"
    STATUSES = [(READING, "Citesc acum"), (FINISHED, "Terminată")]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reader = models.ForeignKey(Reader, on_delete=models.CASCADE, related_name="shelf")
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="shelf_entries")
    # current_page <= book.page_count crosses tables: enforced by library.services + tests (PR-3), not by the DB.
    current_page = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=8, choices=STATUSES, default=READING)
    added_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    rating = models.SmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["reader", "book"], name="shelf_reader_book_unique"),
            models.CheckConstraint(
                condition=models.Q(rating__isnull=True) | models.Q(rating__gte=1, rating__lte=5),
                name="shelf_rating_range",
            ),
            models.CheckConstraint(
                condition=models.Q(rating__isnull=True) | models.Q(status="finished"),
                name="shelf_rating_finished_only",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status="reading", finished_at__isnull=True)
                    | models.Q(status="finished", finished_at__isnull=False)
                ),
                name="shelf_finished_at_iff_finished",
            ),
        ]

    def __str__(self):
        return f"ShelfEntry {self.public_id}"


class ProgressEvent(models.Model):
    """Append-only log; written only by library.services (PR-3). Never updated or deleted except by cascade."""

    PROGRESS, FINISH = "progress", "finish"
    KINDS = [(PROGRESS, "Progress"), (FINISH, "Finish")]

    entry = models.ForeignKey(ShelfEntry, on_delete=models.CASCADE, related_name="events")
    # Denormalized for the idempotency key and stats; must equal entry.reader (service invariant, PR-3).
    reader = models.ForeignKey(Reader, on_delete=models.CASCADE, related_name="progress_events")
    from_page = models.PositiveIntegerField()
    to_page = models.PositiveIntegerField()
    kind = models.CharField(max_length=8, choices=KINDS)
    request_id = models.UUIDField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["reader", "request_id"], name="progress_reader_request_unique"),
            models.CheckConstraint(
                condition=models.Q(kind__in=["progress", "finish"]), name="progress_kind_valid"
            ),
        ]
        indexes = [models.Index(fields=["reader", "created_at"], name="progress_reader_created_idx")]


class BookReflectionSet(models.Model):
    """One stable set per diary entry. Only an unanswered set can be redrawn."""

    entry = models.OneToOneField(ShelfEntry, on_delete=models.CASCADE, related_name="reflection_set")
    pool_version = models.PositiveSmallIntegerField(default=1, editable=False)
    revision = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(pool_version=1), name="reflection_pool_v1"),
            models.CheckConstraint(condition=models.Q(revision__gte=1), name="reflection_revision_positive"),
        ]


class BookReflectionAnswer(models.Model):
    reflection = models.ForeignKey(BookReflectionSet, on_delete=models.CASCADE, related_name="answers")
    position = models.PositiveSmallIntegerField()
    question_id = models.PositiveSmallIntegerField()
    text = models.TextField(max_length=2000, blank=True, default="")

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["reflection", "position"], name="reflection_position_unique"),
            models.UniqueConstraint(fields=["reflection", "question_id"], name="reflection_question_unique"),
            models.CheckConstraint(condition=models.Q(position__gte=1, position__lte=4), name="reflection_position_range"),
            # Literal v1 source IDs: 1 combines fragments 1+2; ID2 is not standalone.
            models.CheckConstraint(condition=models.Q(question_id__in=[1, *range(3, 17)]), name="reflection_question_v1"),
            models.CheckConstraint(condition=LessThanOrEqual(Length("text"), 2000), name="reflection_answer_length"),
        ]
