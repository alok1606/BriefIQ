from pathlib import Path

from streamlit.testing.v1 import AppTest
from src.utils import BriefIQError


def test_demo_ui(monkeypatch):
    monkeypatch.setenv("BRIEFIQ_MODE", "demo")
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    assert not app.exception
    app.button(key="FormSubmitter:meeting-✦ Generate Briefing").click().run()
    assert not app.exception
    assert app.session_state["active"].demo
    assert len(app.session_state["active"].draft.developments) == 3


def test_complete_pdf_offered_when_one_page_overflows(monkeypatch):
    from src import pdf_export
    original = pdf_export.export_pdf
    def export(brief, *, one_page=True):
        if one_page:
            raise BriefIQError("One-page capacity exceeded")
        return original(brief, one_page=False)
    monkeypatch.setenv("BRIEFIQ_MODE", "demo")
    monkeypatch.setattr(pdf_export, "export_pdf", export)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    app.button(key="FormSubmitter:meeting-✦ Generate Briefing").click().run()
    assert not app.exception
    assert any("Download complete PDF" in button.proto.label for button in app.get("download_button"))
