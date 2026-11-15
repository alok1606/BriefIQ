from dataclasses import replace
from datetime import date, datetime, time, timezone
from html import escape
from zoneinfo import ZoneInfo, available_timezones

import streamlit as st

from src.bifrost_client import BifrostClient
from src.config import Settings
from src.markdown_export import export_markdown, plain
from src.pdf_export import export_pdf
from src.research import generate_briefing
from src.utils import BriefIQError
from src.validation import validate_meeting

st.set_page_config(page_title="BriefIQ | Meeting Intelligence", page_icon="✦", layout="wide")
st.markdown("""<style>
.block-container{max-width:1200px;padding-top:2.2rem}h1{letter-spacing:-.05em;font-weight:750!important}
[data-testid="stSidebar"]{border-right:1px solid #25304a}div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px}
.eyebrow{color:#2dd4bf;font-size:.76rem;letter-spacing:.18em;font-weight:700}.hero{font-size:3rem;line-height:1.12;max-width:760px;margin:16px 0}
.muted{color:#9bacc8}.badge{display:inline-block;padding:5px 10px;border:1px solid #34506a;border-radius:20px;color:#75e7d6;font-size:.75rem}
.brand{font-size:1.9rem;font-weight:800}.brand span{color:#2dd4bf}.accent{color:#b6a0ff}
.stButton>button[kind="primary"]{background:linear-gradient(110deg,#167c79,#6952b8);color:white;border:0;min-height:3rem}
@media(max-width:640px){.hero{font-size:2rem}.block-container{padding:1rem}}
</style>""", unsafe_allow_html=True)

try:
    settings = Settings.load()
except ValueError:
    st.error("Invalid environment settings. Check REQUEST_TIMEOUT in .env.")
    st.stop()
st.session_state.setdefault("history", [])
st.session_state.setdefault("active", None)
with st.sidebar:
    st.markdown('<div class="brand">✦ Brief<span>IQ</span></div><p class="muted">Your meeting advantage.</p>', unsafe_allow_html=True)
    st.caption("WORKSPACE")
    if st.button("＋ New Briefing", use_container_width=True):
        st.session_state.active = None
        st.session_state.pop("retry", None)
        st.session_state.pop("error", None)
    section = st.radio("Navigation", ["Briefings", "Settings / About"], label_visibility="collapsed")
    st.divider()
    st.caption("RECENT BRIEFINGS · THIS SESSION")
    if not st.session_state.history:
        st.caption("Your next great conversation starts here.")
    for i, b in enumerate(st.session_state.history):
        if st.button(("DEMO · " if b.demo else "") + b.meeting.name + " · " + b.meeting.when.strftime("%d %b"), key=f"recent{i}", use_container_width=True):
            st.session_state.active = b
    st.divider()
    mode = st.radio("Research mode", ["Fixture demo", "Live"], index=0 if settings.mode != "live" else 1)
    st.caption("Tavily research + Bifrost synthesis\n\nGlobal AI Hackathon 2026 · PS05")

if section == "Settings / About":
    st.title("Built for informed conversations")
    st.write("BriefIQ turns public professional developments into concise meeting preparation, with evidence you can inspect.")
    st.info("Demo runs locally with fictional Northstar Labs fixtures and no network requests. Live mode requires Tavily and a configured Bifrost gateway.")
    st.write({"Tavily configured": bool(settings.tavily_key), "Bifrost model": settings.model,
              "Virtual key configured": bool(settings.virtual_key), "Gateway bearer configured": bool(settings.api_key)})
    if st.button("Check Bifrost configuration"):
        try:
            settings.validate_live(require_tavily=False)
            st.json(BifrostClient(settings).health())
        except BriefIQError as exc:
            st.error(str(exc))
    st.markdown("Provider keys belong in Bifrost. BriefIQ uses `x-bf-vk` for governance and an optional separate Bearer token. All inference passes through the gateway.")
    st.warning("Source attribution is not independent verification. Review identity matches, snippets, dates, and original pages. Research public professional matters only; do not enter private personal information.")
    st.stop()

st.markdown('<div class="eyebrow">MEETING INTELLIGENCE / BRIEFIQ</div><h1 class="hero">Walk Into Every Meeting <span class="accent">Prepared.</span></h1><p class="muted">The right context. The recent signals. The questions that move conversations forward.</p>', unsafe_allow_html=True)
demo = mode == "Fixture demo"
if demo:
    st.warning("FIXTURE DEMO · Fictional Northstar Labs · Fixed meeting: 15 Nov 2026, 16:00 Asia/Kolkata. No live research or LLM calls.")

with st.container(border=True):
    st.subheader("Who are you meeting?")
    with st.form("meeting"):
        c1, c2 = st.columns([1, 3])
        kind = c1.selectbox("Subject type", ["Company", "Person"], disabled=demo)
        name = c2.text_input("Company or person", value="Northstar Labs" if demo else "", placeholder="e.g. Microsoft or a public professional", disabled=demo, max_chars=120)
        c1, c2, c3 = st.columns([1, 1, 2])
        day = c1.date_input("Meeting date", value=date(2026, 11, 15) if demo else datetime.now(ZoneInfo("Asia/Kolkata")).date(), disabled=demo)
        clock = c2.time_input("Meeting time", value=time(16), disabled=demo)
        zones = sorted(available_timezones())
        zone = c3.selectbox("Timezone", zones, index=zones.index("Asia/Kolkata"), disabled=demo)
        purpose = st.text_input("Meeting purpose (optional)", placeholder="Explore a partnership, prepare for a sales call…", max_chars=400)
        submitted = st.form_submit_button("✦ Generate Briefing", type="primary", use_container_width=True)

retry = st.session_state.pop("retry", None)
if submitted or retry:
    st.session_state.active = None
    if submitted:
        st.session_state.pop("last_request", None)
    try:
        meeting = retry[0] if retry else validate_meeting(kind, name, day, clock, zone, purpose)
        run_demo = retry[1] if retry else demo
        st.session_state.last_request = (meeting, run_demo)
        # Do not leave an earlier report visible under a failed new request.
        st.session_state.active = None
        with st.status("Preparing your meeting intelligence…", expanded=True) as status:
            brief = generate_briefing(meeting, settings, demo=run_demo, progress=st.write,
                                      now=datetime(2026, 11, 15, 9, tzinfo=timezone.utc) if run_demo else None)
            status.update(label="Briefing ready · citations validated", state="complete", expanded=False)
        st.session_state.active = brief
        st.session_state.history.insert(0, brief)
        st.session_state.history = st.session_state.history[:10]
        st.session_state.pop("error", None)
    except BriefIQError as exc:
        st.session_state.error = str(exc)
    except Exception:
        st.session_state.error = "An unexpected error interrupted generation. No report was published. Check configuration and retry."

if st.session_state.get("error"):
    st.error(st.session_state.error)
    if st.button("Retry briefing"):
        if st.session_state.get("last_request"):
            st.session_state.retry = st.session_state.last_request
            st.rerun()

b = st.session_state.active
if b:
    st.divider()
    st.markdown('<span class="badge">' + ("FIXTURE DEMO · FICTIONAL" if b.demo else "LIVE RESEARCH") + '</span>', unsafe_allow_html=True)
    st.header(b.meeting.name)
    st.caption(f"{b.meeting.when.strftime('%d %b %Y · %H:%M')} {b.meeting.timezone} | Research: {b.window.start.isoformat()} → {b.window.end.isoformat()}")
    def render_claim(c):
        st.markdown(plain(c.text))
        st.caption(("🟢 Source-backed · attributed excerpt" if c.evidence == "source_backed" else "🟠 Uncertain · verify before use") + " · " + ", ".join(c.citation_ids))
    with st.container(border=True):
        st.subheader("Executive summary")
        for c in b.draft.summary:
            render_claim(c)
    st.subheader("Key developments")
    if not b.draft.developments:
        st.info("Insufficient evidence for recent developments. Use the open questions to gather context.")
    for i, d in enumerate(b.draft.developments, 1):
        with st.container(border=True):
            st.caption(f"SIGNAL {i:02}")
            render_claim(d)
            st.write("**Why it may matter · analysis**")
            st.markdown(plain(d.why_it_matters))
            st.write("**Discussion point**")
            st.markdown(plain(d.discussion_point))
    with st.container(border=True):
        st.subheader("Open questions")
        for i, q in enumerate(b.draft.questions, 1):
            st.markdown(f"{i}. {plain(q)}")
    with st.expander("Sources & evidence trail", expanded=True):
        st.caption("Source-backed means attributed to a retrieved excerpt, not independently verified. Check identity and original context.")
        for s in b.evidence.sources:
            st.link_button(f"[{s.id}] {s.title}", s.url)
            st.caption(f"{s.published or 'Date unknown'} · {s.date_status}")
            st.text(s.excerpt)
        st.caption("Search queries")
        st.write(b.evidence.queries)
    with st.expander("Uncertainty & research scope", expanded=True):
        for n in [*b.window.notes, *b.evidence.notes, *b.draft.uncertainty]:
            st.markdown("• " + plain(n))
    with st.expander("Model request information"):
        st.json(b.metadata)
    md = export_markdown(b)
    c1, c2 = st.columns(2)
    c1.download_button("↓ Download Markdown", md, "briefiq.md", "text/markdown", use_container_width=True)
    try:
        pdf = export_pdf(b)
        c2.download_button("↓ Download one-page PDF", pdf, "briefiq.pdf", "application/pdf", use_container_width=True)
    except BriefIQError as exc:
        c2.warning(str(exc))
    with st.expander("Copy briefing text"):
        st.caption("Use the copy icon at the top right of this text block.")
        st.code(md, language=None)
else:
    c1, c2, c3 = st.columns(3)
    for c, title, text in [(c1, "01 / Research", "Recent developments, across focused Tavily searches."), (c2, "02 / Synthesize", "Bifrost routes evidence to your configured model."), (c3, "03 / Walk in ready", "A concise brief, open questions, and inspectable sources.")]:
        with c.container(border=True):
            st.subheader(title)
            st.caption(text)
