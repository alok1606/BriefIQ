import json
from pathlib import Path

from .bifrost_client import BifrostClient
from .briefing import demo_draft, empty_draft, validate_draft
from .evidence import build_evidence
from .models import Briefing
from .tavily_client import TavilyClient
from .utils import BriefIQError
from .validation import research_window


def generate_briefing(meeting, settings, demo=False, progress=lambda stage: None, now=None, tavily=None, bifrost=None):
    progress("Validating context and calculating the research window")
    window = research_window(meeting, now)
    if demo and meeting.name != "Northstar Labs":
        raise BriefIQError("Demo fixtures cover fictional Northstar Labs only. Select Live to research another target.")
    results, warnings = [], []
    queries = [f'"{meeting.name}" {suffix}' for suffix in (
        "news announcements product launch", "leadership executive appointment hiring", "partnership funding strategy developments")]
    if window.start < window.end:
        if demo:
            progress("Loading explicitly fictional demo evidence")
            results = json.loads((Path(__file__).resolve().parents[1] / "tests/fixtures/sample_results.json").read_text(encoding="utf-8"))["results"]
        else:
            settings.validate_live()
            search = tavily or TavilyClient(settings)
            successes = 0
            for i, query in enumerate(queries):
                progress(f"Researching Tavily query {i + 1} of {len(queries)}")
                try:
                    results.extend(search.search(query, window))
                    successes += 1
                except BriefIQError as exc:
                    warnings.append(str(exc))
            if successes == 0:
                raise BriefIQError("All Tavily searches failed. Check your credentials, limits, and connection; retry. No report was generated.")
    progress("Deduplicating sources and checking publication dates")
    evidence = build_evidence(results, meeting, window)
    evidence.queries = queries if window.start < window.end else []
    evidence.notes.extend(warnings)
    progress("Composing fixture briefing" if demo else "Synthesizing evidence through Bifrost")
    metadata = {"mode": "fixture demo" if demo else "live"}
    if demo:
        draft = demo_draft(evidence)
    elif evidence.sources:
        draft, metadata = (bifrost or BifrostClient(settings)).generate(meeting, window, evidence)
    else:
        draft = empty_draft()
        metadata["inference"] = "Skipped: no evidence available"
    progress("Validating citations and preparing your briefing")
    draft = validate_draft(draft, evidence)
    return Briefing(meeting=meeting, window=window, evidence=evidence, draft=draft, demo=demo, metadata=metadata)
