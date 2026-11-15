import sys
from pathlib import Path
from datetime import date, datetime, time, timezone

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.validation import validate_meeting, research_window


@pytest.fixture
def meeting():
    return validate_meeting("Company", "Northstar Labs", date(2026, 11, 15), time(16), "Asia/Kolkata")


@pytest.fixture
def now():
    return datetime(2026, 11, 15, 9, tzinfo=timezone.utc)


@pytest.fixture
def window(meeting, now):
    return research_window(meeting, now)


@pytest.fixture
def rows():
    import json
    return json.loads((Path(__file__).parent / "fixtures/sample_results.json").read_text())["results"]
