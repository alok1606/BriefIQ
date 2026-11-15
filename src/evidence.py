import re
from datetime import datetime, time, timedelta, timezone
from email.utils import parsedate_to_datetime

from .models import Evidence, Source
from .utils import canonical_url


def publication(value):
    if not isinstance(value, str) or not value.strip():
        return None, False
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        precise = "T" in value or " " in value
    except ValueError:
        try:
            dt, precise = parsedate_to_datetime(value), True
        except (ValueError, TypeError, OverflowError):
            return None, False
    # Unknown timezone is not an exact instant: conservatively treat as date-only.
    precise = precise and dt.tzinfo is not None
    return dt.replace(tzinfo=dt.tzinfo or timezone.utc).astimezone(timezone.utc), precise


def build_evidence(results, meeting, window):
    sources, seen_urls, seen_titles = [], set(), set()
    notes = []
    target = re.sub(r"\W+", " ", meeting.name.casefold()).strip()
    for row in results:
        url = canonical_url(row.get("url", ""))
        title = str(row.get("title") or "Untitled source")[:180]
        content = str(row.get("content") or "")[:2200]
        title_key = re.sub(r"\W+", " ", title.casefold()).strip()
        haystack = re.sub(r"\W+", " ", (title + " " + content).casefold())
        if not url or not content or target not in haystack or url in seen_urls or title_key in seen_titles:
            continue
        dt, precise = publication(row.get("published_date"))
        status = "undated"
        if dt:
            if precise:
                if not window.start <= dt <= window.end:
                    continue
                status = "in_window"
            else:
                lo = datetime.combine(dt.date(), time.min, timezone.utc)
                hi = lo + timedelta(days=1)
                if hi <= window.start or lo > window.end:
                    continue
                status = "in_window" if window.start <= lo and hi <= window.end else "boundary_uncertain"
        seen_urls.add(url)
        seen_titles.add(title_key)
        sources.append(Source(id=f"S{len(sources)+1}", title=title, url=url, excerpt=content,
                              published=dt.isoformat() if dt else None, date_status=status))
        if len(sources) == 12:
            break
    if any(s.date_status != "in_window" for s in sources):
        notes.append("Some sources have missing or boundary-ambiguous publication dates; they are context only and cannot establish an in-window development.")
    if not sources:
        notes.append("No relevant qualifying sources found. Absence of search results does not establish absence of developments.")
    return Evidence(sources=sources, notes=notes)
