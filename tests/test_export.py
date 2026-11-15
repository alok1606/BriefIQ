from io import BytesIO

import pytest
from pypdf import PdfReader

from src.config import Settings
from src.markdown_export import export_markdown
from src.pdf_export import export_pdf
from src.research import generate_briefing
from src.utils import BriefIQError


def test_exports(meeting, now):
    b = generate_briefing(meeting, Settings(), demo=True, now=now)
    md = export_markdown(b)
    assert "FICTIONAL" in md and "## Open questions" in md
    assert all(s.url in md for s in b.evidence.sources)
    data = export_pdf(b)
    reader = PdfReader(BytesIO(data))
    assert len(reader.pages) == 1
    text = reader.pages[0].extract_text()
    assert "FICTIONAL" in text and "Uncertainty" in text
    assert all(f"[{s.id}]" in text for s in b.evidence.sources)
    assert len(reader.pages[0].get("/Annots", [])) == 3


def test_no_silent_truncation(meeting, now):
    b = generate_briefing(meeting, Settings(), demo=True, now=now)
    b.evidence.notes = ["Long retained content " * 50] * 30
    with pytest.raises(BriefIQError, match="Nothing was truncated"):
        export_pdf(b)
    complete = PdfReader(BytesIO(export_pdf(b, one_page=False)))
    assert len(complete.pages) > 1
    text = " ".join(" ".join(p.extract_text() for p in complete.pages).split())
    assert text.count("Long retained content") == 1500


def test_unused_research_does_not_overflow_pdf(meeting, now):
    b = generate_briefing(meeting, Settings(), demo=True, now=now)
    for i in range(4, 13):
        b.evidence.sources.append(b.evidence.sources[0].model_copy(update={
            "id": f"S{i}", "url": f"https://example.org/unused/{i}",
            "title": "Long background research title that was not used in any claim " * 3}))
    reader = PdfReader(BytesIO(export_pdf(b)))
    assert len(reader.pages) == 1
    assert len(reader.pages[0].get("/Annots", [])) == 3
    assert "S12" in export_markdown(b)


def test_missing_pdf_citation_rejected(meeting, now):
    b = generate_briefing(meeting, Settings(), demo=True, now=now)
    b.draft.summary[0].citation_ids = ["S999"]
    with pytest.raises(BriefIQError, match="missing"):
        export_pdf(b)


def test_dense_brief_keeps_all_twelve_citations_on_one_page(meeting, now):
    from src.models import Claim, Development
    from src.briefing import validate_draft
    b = generate_briefing(meeting, Settings(), demo=True, now=now)
    seed = b.evidence.sources[0]
    b.evidence.sources = [seed.model_copy(update={"id": f"S{i}", "url": f"https://example.org/source/{i}",
        "title": f"FICTIONAL research source {i}: " + "Detailed partner pilot announcement and leadership context " * 2}) for i in range(1, 13)]
    b.draft.summary = [Claim(text="Fictional Northstar Labs is evaluating partner workflow pilots and gathering operational feedback before wider delivery.",
                            citation_ids=["S1", "S2", "S3"], evidence="source_backed"),
                       Claim(text="The fictional evidence highlights coordination, technical readiness, and unanswered questions about rollout timing.",
                            citation_ids=["S4", "S5", "S6"], evidence="source_backed")]
    b.draft.developments = [Development(
        text=f"Fictional pilot {i}: Northstar Labs announced work covering partner onboarding, workflow integration, operational safeguards, and structured feedback. The team will review milestones before deciding whether to expand access. No firm launch date was given.",
        why_it_matters="This could affect partnership sequencing and readiness, so scope and delivery assumptions should be checked with the team before making commitments.",
        discussion_point="Which pilot outcomes, ownership decisions, technical dependencies, and timing assumptions should we confirm before agreeing on next steps?",
        citation_ids=[f"S{i+6}"] if i < 5 else ["S11", "S12"], evidence="source_backed") for i in range(1, 6)]
    validate_draft(b.draft, b.evidence)
    reader = PdfReader(BytesIO(export_pdf(b)))
    assert len(reader.pages) == 1
    assert len(reader.pages[0].get("/Annots", [])) == 12
    linked_urls = {a.get_object()["/A"]["/URI"] for a in reader.pages[0]["/Annots"]}
    assert linked_urls == {s.url for s in b.evidence.sources}
    text = " ".join(reader.pages[0].extract_text().split())
    for d in b.draft.developments:
        assert d.text in text and d.why_it_matters in text and d.discussion_point in text
    assert all(f"[S{i}]" in text for i in range(1, 13))


def test_markdown_escapes(meeting, now):
    b = generate_briefing(meeting, Settings(), demo=True, now=now)
    b.draft.summary[0].text = "<script>bad</script> [fake](https://evil.invalid)"
    md = export_markdown(b)
    assert "<script>" not in md and "[fake]" not in md
