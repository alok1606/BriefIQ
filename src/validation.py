import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .models import Meeting, Window
from .utils import BriefIQError


def validate_meeting(target_type, name, day, clock, zone, purpose=""):
    name = " ".join(name.split())
    if not 2 <= len(name) <= 120 or not re.search(r"[^\W\d_]", name, re.UNICODE):
        raise BriefIQError("Enter a company or public professional name between 2 and 120 characters.")
    if any(ord(c) < 32 for c in name + purpose) or len(purpose) > 400:
        raise BriefIQError("Remove control characters and keep the meeting purpose under 400 characters.")
    try:
        tz = ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError):
        raise BriefIQError("Select a valid IANA timezone.") from None
    naive = datetime.combine(day, clock).replace(tzinfo=None)
    local = naive.replace(tzinfo=tz)
    if local.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) != naive:
        raise BriefIQError("This local time does not exist because of daylight saving. Choose another time.")
    if local.utcoffset() != naive.replace(tzinfo=tz, fold=1).utcoffset():
        raise BriefIQError("This local time is ambiguous because of daylight saving. Choose an unambiguous time.")
    if target_type not in ("Company", "Person"):
        raise BriefIQError("Select Company or Person.")
    return Meeting(target_type=target_type, name=name, when=local, timezone=zone, purpose=purpose.strip())


def research_window(meeting, now=None):
    now = now or datetime.now(timezone.utc)
    if meeting.when.tzinfo is None or now.tzinfo is None:
        raise BriefIQError("Meeting and research timestamps must include a timezone.")
    when = meeting.when.astimezone(timezone.utc)
    start = when - timedelta(days=30)
    end = min(when, now.astimezone(timezone.utc))
    notes = []
    if when > now:
        notes.append("Future meeting: research ends at the current research timestamp; later developments are unavailable.")
    else:
        notes.append("Historical verification limitation: today's search index may contain later edits; publication dates do not prove what was known at the meeting time.")
    if start >= end:
        notes.append("The meeting's 30-day window has not begun. No currently available developments can qualify.")
    return Window(start=start, end=end, researched_at=now, notes=notes)
