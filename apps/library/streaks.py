"""Daily reading streak (#65), derived read-only from committed ProgressEvents.

A calendar day (in settings.TIME_ZONE, Europe/Chisinau) counts when the reader has at least one event that
advanced pages (to_page > from_page). Replays never create a second event and rejected saves create none, so
no extra filtering is needed for them. No counter table, no write on GET.
"""

from dataclasses import dataclass
from datetime import timedelta

from django.db.models import F
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.library.models import ProgressEvent

TODAY, CARRIED, NONE = "today", "carried", "none"
WEEKDAYS = ("L", "Ma", "Mi", "J", "V", "S", "D")  # Romanian Monday..Sunday initials
WEEKDAY_NAMES = ("luni", "marți", "miercuri", "joi", "vineri", "sâmbătă", "duminică")


@dataclass(frozen=True)
class WeekDayVM:
    label: str
    name: str
    read: bool
    is_today: bool
    is_future: bool


@dataclass(frozen=True)
class StreakVM:
    days: int  # current streak; for CARRIED it ends yesterday and can still be extended today
    status: str  # TODAY | CARRIED | NONE
    week: tuple  # 7 WeekDayVM, Monday..Sunday of the current week

    @property
    def label(self):
        """Romanian count: 1 zi consecutivă / 3 zile consecutive / 20 de zile consecutive."""
        if self.days == 1:
            return "1 zi consecutivă"
        de = "de " if self.days >= 20 and not 1 <= self.days % 100 <= 19 else ""
        return f"{self.days} {de}zile consecutive"


def compute_streak(read_days, today):
    """Pure: read_days is a set of dates with real reading. Returns StreakVM for `today`."""
    yesterday = today - timedelta(days=1)
    if today in read_days:
        status, day = TODAY, today
    elif yesterday in read_days:
        status, day = CARRIED, yesterday
    else:
        status, day = NONE, None
    days = 0
    while day is not None and day in read_days:
        days += 1
        day -= timedelta(days=1)
    monday = today - timedelta(days=today.weekday())
    week = tuple(
        WeekDayVM(WEEKDAYS[i], WEEKDAY_NAMES[i], d in read_days, d == today, d > today)
        for i, d in enumerate(monday + timedelta(days=n) for n in range(7))
    )
    return StreakVM(days, status, week)


def reading_streaks(readers, now=None):
    """{reader.pk: StreakVM} for all `readers` with one query (dashboard: adult + up to six children)."""
    now = now or timezone.now()
    tz = timezone.get_default_timezone()
    today = timezone.localtime(now, tz).date()
    by_reader = {r.pk: set() for r in readers}
    rows = (
        ProgressEvent.objects.filter(reader__in=list(by_reader), to_page__gt=F("from_page"), created_at__lte=now)
        .annotate(day=TruncDate("created_at", tzinfo=tz))
        .values_list("reader_id", "day")
        .distinct()
    )
    for reader_id, day in rows:
        by_reader[reader_id].add(day)
    return {pk: compute_streak(days, today) for pk, days in by_reader.items()}


def reading_streak(reader, now=None):
    return reading_streaks([reader], now)[reader.pk]
