from src.evidence import build_evidence, publication


def test_dedup(rows, meeting, window):
    duplicate = dict(rows[0], url=rows[0]["url"] + "?utm_source=foo#part")
    assert len(build_evidence(rows + [duplicate], meeting, window).sources) == 3


def test_undated(rows, meeting, window):
    rows[0].pop("published_date")
    evidence = build_evidence(rows, meeting, window)
    assert evidence.sources[0].date_status == "undated"
    assert evidence.notes


def test_filter(rows, meeting, window):
    bad = [dict(rows[0], published_date="2026-09-01"), dict(rows[0], published_date="2026-11-16T01:00:00Z"),
           dict(rows[0], title="Other", content="Unrelated company"), dict(rows[0], url="javascript:alert(1)")]
    assert not build_evidence(bad, meeting, window).sources


def test_date_boundary(rows, meeting, window):
    rows[0]["published_date"] = "2026-11-15"
    assert build_evidence(rows, meeting, window).sources[0].date_status == "boundary_uncertain"


def test_rfc_date():
    d, precise = publication("Tue, 10 Nov 2026 09:00:00 GMT")
    assert d.day == 10 and precise


def test_malformed_date():
    assert publication("yesterday") == (None, False)
