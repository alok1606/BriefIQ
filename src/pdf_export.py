from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.platypus.doctemplate import LayoutError
from pypdf import PdfReader

from .utils import BriefIQError


def export_pdf(brief, *, one_page=True):
    """Preserve every claim/note and every cited URL; compact references if needed.

    Uncited research remains in the evidence trail and Markdown. The complete
    multi-page option is explicit and never masquerades as a one-page export.
    """
    citation_ids = {i for c in [*brief.draft.summary, *brief.draft.developments] for i in c.citation_ids}
    sources = [s for s in brief.evidence.sources if s.id in citation_ids]
    if citation_ids - {s.id for s in sources}:
        raise BriefIQError("A cited source is missing from this briefing. PDF export was rejected.")
    font = "Helvetica"
    fontpath = Path(__file__).resolve().parents[1] / "assets/DejaVuSans.ttf"
    if fontpath.exists():
        if "BriefIQ" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("BriefIQ", str(fontpath)))
        font = "BriefIQ"
    layouts = [(9, False), (9, True), (8.5, True), (8, True)] if one_page else [(9, False)]
    for size, compact_references in layouts:
        buffer = BytesIO()
        body = ParagraphStyle("body", fontName=font, fontSize=size, leading=size * (1.2 if compact_references else 1.3),
                              textColor=colors.HexColor("#24324c"), spaceAfter=2 if compact_references else 3, alignment=TA_LEFT)
        heading = ParagraphStyle("heading", parent=body, fontSize=size + 2, leading=size + 4,
                                 textColor=colors.HexColor("#146e72"), spaceBefore=5 if compact_references else 7, spaceAfter=3 if compact_references else 4)
        story = []
        def p(text, style=body):
            story.append(Paragraph(text, style))
        def safe(text):
            return escape(str(text))
        def claim(c):
            return safe(c.text) + " " + safe(" ".join(f"[{i}]" for i in c.citation_ids)) + " [" + ("Source-backed" if c.evidence == "source_backed" else "UNCERTAIN") + "]"
        p("BriefIQ | Walk Into Every Meeting Prepared", ParagraphStyle("title", parent=heading, fontSize=18, leading=22))
        if brief.demo:
            p("FIXTURE DEMO - FICTIONAL DATA / NOT LIVE RESEARCH", heading)
        p(safe(brief.meeting.name) + " | " + safe(brief.meeting.when.isoformat()) + " (" + safe(brief.meeting.timezone) + ")")
        p("Research period (UTC): " + safe(brief.window.start.isoformat()) + " to " + safe(brief.window.end.isoformat()))
        p("Purpose: " + safe(brief.meeting.purpose or "General preparation"))
        p("Executive summary", heading)
        for c in brief.draft.summary:
            p(claim(c))
        p("Key developments", heading)
        if not brief.draft.developments:
            p("Insufficient evidence to establish recent developments.")
        for i, d in enumerate(brief.draft.developments, 1):
            p(f"{i}. " + claim(d))
            p("Why it may matter (analysis): " + safe(d.why_it_matters))
            p("Discuss: " + safe(d.discussion_point))
        p("Open questions", heading)
        for q in brief.draft.questions:
            p("- " + safe(q))
        p("Cited sources (full URLs linked)", heading)
        reference_cells = []
        for s in sources:
            # A compact citation still contains its stable ID, publisher, date,
            # uncertainty status and complete destination URL annotation.
            label = urlsplit(s.url).hostname if compact_references else s.title
            published = (s.published or "Date unknown")[:10] if s.published else "Date unknown"
            status = "" if s.date_status == "in_window" else " | " + s.date_status
            reference = f'[{s.id}] <link href="{escape(s.url, {chr(34): "&quot;"})}" color="#146e72">{safe(label)}</link> | {safe(published)}{safe(status)}'
            if compact_references:
                reference_cells.append(Paragraph(reference, body))
            else:
                p(reference)
        if reference_cells:
            rows = [reference_cells[i:i+3] for i in range(0, len(reference_cells), 3)]
            rows[-1] += [""] * (3 - len(rows[-1]))
            story.append(Table(rows, colWidths=[(A4[0] - 72) / 3] * 3, hAlign="LEFT", style=[
                ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
        if not sources:
            p("No source-backed claims available.")
        p("Uncertainty and scope", heading)
        for n in [*brief.window.notes, *brief.evidence.notes, *brief.draft.uncertainty]:
            p("- " + safe(n))
        p("Source-backed = attributed excerpt, not independent verification. Check source identity and context.")
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36,
                                topMargin=28, bottomMargin=28, title="BriefIQ meeting briefing", author="BriefIQ")
        try:
            doc.build(story)
        except LayoutError:
            continue
        data = buffer.getvalue()
        if not one_page or len(PdfReader(BytesIO(data)).pages) == 1:
            return data
    raise BriefIQError("This briefing exceeds one readable PDF page. Nothing was truncated. Use the complete PDF or Markdown export.")
