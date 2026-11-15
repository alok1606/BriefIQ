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


def test_markdown_escapes(meeting, now):
    b = generate_briefing(meeting, Settings(), demo=True, now=now)
    b.draft.summary[0].text = "<script>bad</script> [fake](https://evil.invalid)"
    md = export_markdown(b)
    assert "<script>" not in md and "[fake]" not in md
