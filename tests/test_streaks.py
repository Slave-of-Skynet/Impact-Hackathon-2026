import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.accounts.models import Account, Reader
from apps.library.models import Book, ProgressEvent
from apps.library.services import add_to_shelf, finish_book, record_progress
from apps.library.streaks import CARRIED, NONE, TODAY, compute_streak, reading_streak, reading_streaks

from .conftest import make_child

CHISINAU = ZoneInfo("Europe/Chisinau")
MON = date(2026, 10, 26)  # a Monday, the day after the autumn DST change in Chisinau


def at(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm, tzinfo=CHISINAU)


# Pure rule


def test_no_reading_is_zero_with_empty_week():
    s = compute_streak(set(), MON)
    assert (s.days, s.status) == (0, NONE)
    assert [d.read for d in s.week] == [False] * 7
    assert [d.label for d in s.week] == ["L", "Ma", "Mi", "J", "V", "S", "D"]
    assert s.week[0].is_today and all(d.is_future for d in s.week[1:])


def test_today_yesterday_and_gaps():
    d = lambda n: MON + timedelta(days=n)  # noqa: E731
    assert (compute_streak({d(0)}, d(0)).days, compute_streak({d(0)}, d(0)).status) == (1, TODAY)
    assert compute_streak({d(-1), d(0)}, d(0)).days == 2
    assert compute_streak({d(-2), d(-1), d(0)}, d(0)).days == 3
    carried = compute_streak({d(-2), d(-1)}, d(0))
    assert (carried.days, carried.status) == (2, CARRIED)  # kept, can still be extended today
    broken = compute_streak({d(-3), d(-2)}, d(0))  # gap of more than one day
    assert (broken.days, broken.status) == (0, NONE)
    assert compute_streak({d(-5), d(-1), d(0)}, d(0)).days == 2  # older run does not join


def test_week_strip_is_monday_to_sunday_of_today():
    wed = MON + timedelta(days=2)
    s = compute_streak({MON, wed, MON - timedelta(days=1)}, wed)
    assert [d.read for d in s.week] == [True, False, True, False, False, False, False]
    assert [d.is_today for d in s.week].index(True) == 2


@pytest.mark.parametrize("days, label", [
    (1, "1 zi consecutivă"), (2, "2 zile consecutive"), (19, "19 zile consecutive"),
    (20, "20 de zile consecutive"), (101, "101 zile consecutive"), (120, "120 de zile consecutive"),
])
def test_romanian_label(days, label):
    read = {MON - timedelta(days=n) for n in range(days)}
    assert compute_streak(read, MON).label == label


# From committed events


@pytest.fixture
def reader(db):
    return Reader.objects.create(kind="adult", account=Account.objects.create_user("streak@demo.local"))


def book(pages=120, title="Synthetic"):
    return Book.objects.create(title=title, author="Demo", page_count=pages, genre="story")


def stamp_last(created_at):
    event = ProgressEvent.objects.latest("pk")
    ProgressEvent.objects.filter(pk=event.pk).update(created_at=created_at)


def test_only_real_page_advances_count_once_per_day(reader):
    now = at(2026, 10, 26, 18, 0)
    entry, _ = add_to_shelf(reader, book())
    assert reading_streak(reader, now).days == 0  # shelving is not reading
    key = uuid.uuid4()
    record_progress(reader, entry, 10, key)
    stamp_last(at(2026, 10, 26, 9, 0))
    record_progress(reader, entry, 10, key)  # idempotent replay: no new event
    record_progress(reader, entry, 10, uuid.uuid4())  # same page
    stamp_last(at(2026, 10, 25, 9, 0))
    record_progress(reader, entry, 4, uuid.uuid4())  # backward correction
    stamp_last(at(2026, 10, 24, 9, 0))
    other, _ = add_to_shelf(reader, book(title="Second"))
    record_progress(reader, other, 5, uuid.uuid4())  # second book, same day
    stamp_last(at(2026, 10, 26, 10, 0))
    s = reading_streak(reader, now)
    assert (s.days, s.status) == (1, TODAY)  # 25th (same page) and 24th (backward) do not count


def test_finish_counts_only_when_pages_advance(reader):
    now = at(2026, 10, 26, 18, 0)
    entry, _ = add_to_shelf(reader, book(pages=40))
    record_progress(reader, entry, 40, uuid.uuid4())  # reaching the end finishes the book
    stamp_last(at(2026, 10, 25, 20, 0))
    assert reading_streak(reader, now).status == CARRIED
    entry2, _ = add_to_shelf(reader, book(title="B2"))
    record_progress(reader, entry2, 50, uuid.uuid4())
    stamp_last(at(2026, 10, 24, 20, 0))
    finish_book(reader, entry2, uuid.uuid4())  # 50 -> 120 advances
    stamp_last(at(2026, 10, 26, 8, 0))
    assert reading_streak(reader, now).days == 3


def test_midnight_and_dst_use_chisinau_calendar_days(reader):
    entry, _ = add_to_shelf(reader, book())
    for page, when in [
        (5, at(2026, 10, 24, 23, 59)),  # EEST, UTC+3
        (6, at(2026, 10, 25, 0, 1)),    # two minutes later, next local day
        (7, at(2026, 10, 25, 23, 30)),  # after the 03:00 -> 02:00 change, EET UTC+2
        (8, at(2026, 10, 26, 0, 10)),
    ]:
        record_progress(reader, entry, page, uuid.uuid4())
        stamp_last(when)
    # 23:59 on the 24th and 00:01 on the 25th share a UTC date (20:59Z/21:01Z) but are two local days.
    assert reading_streak(reader, at(2026, 10, 26, 12, 0)).days == 3
    assert reading_streak(reader, at(2026, 10, 27, 23, 59)).status == CARRIED
    assert reading_streak(reader, at(2026, 10, 28, 0, 0)).days == 0
    assert reading_streak(reader, at(2026, 10, 24, 23, 59)).days == 1  # future events are ignored


def test_readers_are_isolated_and_batched_in_one_query(guardian):
    kids = [make_child(guardian, f"K{i}") for i in range(3)]
    adult = Reader.objects.get(account=guardian)
    entry, _ = add_to_shelf(kids[0].reader, book())
    record_progress(kids[0].reader, entry, 9, uuid.uuid4())
    stamp_last(at(2026, 10, 26, 9, 0))
    readers = [adult] + [k.reader for k in kids]
    with CaptureQueriesContext(connection) as queries:
        streaks = reading_streaks(readers, at(2026, 10, 26, 12, 0))
    assert len(queries) == 1
    assert [streaks[r.pk].days for r in readers] == [0, 1, 0, 0]


# Pages


def test_child_home_shows_active_child_streak_after_real_save(child_client, child):
    assert "Începe seria ta de lectură!" in child_client.get("/copil/").content.decode()
    entry, _ = add_to_shelf(child.reader, book())
    record_progress(child.reader, entry, 12, uuid.uuid4())
    body = child_client.get("/copil/").content.decode()
    assert "1 zi consecutivă" in body and "css/streak" in body
    assert body.count('<li class="streak-day') == 7


def test_dashboard_and_report_show_owned_streaks(adult_client, guardian, child):
    sibling = make_child(guardian, "Alex")
    entry, _ = add_to_shelf(child.reader, book())
    record_progress(child.reader, entry, 12, uuid.uuid4())
    dash = adult_client.get("/panou/").content.decode()
    assert dash.count("1 zi consecutivă") == 1  # Mia only; Alex and the adult start fresh
    assert dash.count("Începe seria ta de lectură!") == 2
    report = adult_client.get(f"/familie/{child.public_id}/").content.decode()
    assert "1 zi consecutivă" in report
    assert "Începe seria ta de lectură!" in adult_client.get(f"/familie/{sibling.public_id}/").content.decode()


def test_public_catalog_has_no_streak(client, db):
    assert 'class="streak' not in client.get("/carti/").content.decode()
