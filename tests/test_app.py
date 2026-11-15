from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_demo_ui():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    assert not app.exception
    app.button(key="FormSubmitter:meeting-✦ Generate Briefing").click().run()
    assert not app.exception
    assert app.session_state["active"].demo
    assert len(app.session_state["active"].draft.developments) == 3
