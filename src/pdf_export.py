from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.doctemplate import LayoutError
from pypdf import PdfReader

from .utils import BriefIQError


def export_pdf(brief):
    font = "Helvetica"
    fontpath = Path(__file__).resolve().parents[1] / "assets/DejaVuSans.ttf"
    if fontpath.exists():
        if "BriefIQ" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("BriefIQ", str(fontpath)))
        font = "BriefIQ"
    for size in (9, 8.5, 8):
        buffer = BytesIO()
        body = ParagraphStyle("body", fontName=font, fontSize=size, leading=size * 1.3,
                              textColor=colors.HexColor("#24324c"), spaceAfter=3, alignment=TA_LEFT)
        heading = ParagraphStyle("heading", parent=body, fontSize=size + 2, leading=size + 4,
                                 textColor=colors.HexColor("#146e72"), spaceBefore=7, spaceAfter=4)
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
        p("Source references (click to verify)", heading)
        for s in brief.evidence.sources:
            p(f'[{s.id}] <link href="{escape(s.url, {chr(34): "&quot;"})}" color="#146e72">{safe(s.title)}</link> | {safe(s.published or "Date unknown")} | {s.date_status}')
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
        if len(PdfReader(BytesIO(data)).pages) == 1:
            return data
    raise BriefIQError("This briefing exceeds one readable PDF page. Nothing was truncated. Download the complete Markdown or retry a shorter briefing.")
