from datetime import date, datetime, time, timedelta, timezone

import pytest

from src.utils import BriefIQError
from src.validation import validate_meeting, research_window


@pytest.mark.parametrize("name", ["", "x", "123", "x" * 121])
def test_invalid_names(name):
    with pytest.raises(BriefIQError):
        validate_meeting("Company", name, date(2026, 11, 15), time(12), "UTC")


def test_timezone_and_window(meeting, window, now):
    assert meeting.when.astimezone(timezone.utc).hour == 10
    assert window.end == now
    assert meeting.when.astimezone(timezone.utc) - window.start == timedelta(days=30)
    assert "Future" in window.notes[0]


@pytest.mark.parametrize("day,clock", [(date(2026, 3, 8), time(2, 30)), (date(2026, 11, 1), time(1, 30))])
def test_dst_rejected(day, clock):
    with pytest.raises(BriefIQError):
        validate_meeting("Person", "Public Professional", day, clock, "America/New_York")


def test_bad_zone():
    with pytest.raises(BriefIQError):
        validate_meeting("Company", "Acme", date(2026, 11, 15), time(12), "Invalid/Zone")


def test_historical(meeting):
    w = research_window(meeting, datetime(2026, 12, 1, tzinfo=timezone.utc))
    assert w.end == meeting.when
    assert "Historical" in w.notes[0]


def test_far_future(meeting, now):
    m = meeting.model_copy(update={"when": meeting.when + timedelta(days=90)})
    assert research_window(m, now).start > now
