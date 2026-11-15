import json

import httpx
import pytest

from src.bifrost_client import BifrostClient
from src.briefing import demo_draft, validate_draft
from src.config import Settings
from src.evidence import build_evidence
from src.research import generate_briefing
from src.tavily_client import TavilyClient
from src.utils import BriefIQError


def mock_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_demo(meeting, now):
    b = generate_briefing(meeting, Settings(), demo=True, now=now)
    assert b.demo and len(b.draft.developments) == 3
    assert "fictional" in b.draft.uncertainty[0].lower()


def test_demo_other_target(meeting, now):
    with pytest.raises(BriefIQError):
        generate_briefing(meeting.model_copy(update={"name": "Real Corp"}), Settings(), demo=True, now=now)


def test_unknown_citation(rows, meeting, window):
    e = build_evidence(rows, meeting, window)
    d = demo_draft(e)
    d.developments[0].citation_ids = ["S999"]
    with pytest.raises(BriefIQError, match="not retrieved"):
        validate_draft(d, e)


def test_unsupported_claim(rows, meeting, window):
    e = build_evidence(rows, meeting, window)
    d = demo_draft(e)
    d.summary[0].citation_ids = []
    assert validate_draft(d, e).summary[0].evidence == "uncertain"
    e.sources[0].date_status = "undated"
    assert validate_draft(d, e).developments[0].evidence == "uncertain"


def test_tavily_contract(meeting, window):
    def handler(req):
        assert str(req.url) == "https://api.tavily.com/search"
        payload = json.loads(req.content)
        assert payload["include_published_date"] is True
        assert payload["end_date"] == "2026-11-16"
        assert req.headers["Authorization"] == "Bearer fake"
        return httpx.Response(200, json={"results": []})
    assert TavilyClient(Settings(tavily_key="fake"), mock_client(handler)).search("query", window) == []


@pytest.mark.parametrize("code", [401, 429, 500, 432])
def test_api_errors(code, window, monkeypatch):
    monkeypatch.setattr("src.utils.time.sleep", lambda _: None)
    attempts = []
    def handler(req):
        attempts.append(req)
        return httpx.Response(code, json={"secret": "do-not-leak"})
    with pytest.raises(BriefIQError) as exc:
        TavilyClient(Settings(), mock_client(handler)).search("test", window)
    assert "do-not-leak" not in str(exc.value)
    assert len(attempts) == (3 if code in (429, 500) else 1)


def test_timeout(window, monkeypatch):
    monkeypatch.setattr("src.utils.time.sleep", lambda _: None)
    def handler(req):
        raise httpx.ReadTimeout("secret", request=req)
    with pytest.raises(BriefIQError, match="3 attempts"):
        TavilyClient(Settings(), mock_client(handler)).search("test", window)


@pytest.mark.parametrize("body", [{}, {"choices": []}, {"choices": [{"message": {"content": "not JSON"}}]}])
def test_malformed_llm(body, meeting, window, rows):
    client = BifrostClient(Settings(), mock_client(lambda r: httpx.Response(200, json=body)))
    with pytest.raises(BriefIQError, match="malformed"):
        client.generate(meeting, window, build_evidence(rows, meeting, window))


def test_bifrost_contract(meeting, window, rows):
    evidence = build_evidence(rows, meeting, window)
    def handler(req):
        assert str(req.url) == "http://localhost:8080/v1/chat/completions"
        assert req.headers["x-bf-vk"] == "fake-vk"
        assert json.loads(req.content)["model"] == "openai/gpt-4o-mini"
        return httpx.Response(200, json={"choices": [{"message": {"content": demo_draft(evidence).model_dump_json()}}], "usage": {"total_tokens": 42, "secret": "hidden"}})
    d, meta = BifrostClient(Settings(bifrost_url="http://localhost:8080/v1", virtual_key="fake-vk"), mock_client(handler)).generate(meeting, window, evidence)
    assert len(d.developments) == 3 and meta["usage"] == {"total_tokens": 42}


def test_empty_search(meeting, now):
    search = TavilyClient(Settings(), mock_client(lambda r: httpx.Response(200, json={"results": []})))
    b = generate_briefing(meeting, Settings(tavily_key="fake"), now=now, tavily=search)
    assert not b.draft.developments and b.metadata["inference"].startswith("Skipped")


def test_all_searches_fail(meeting, now):
    search = TavilyClient(Settings(), mock_client(lambda r: httpx.Response(401)))
    with pytest.raises(BriefIQError, match="All Tavily"):
        generate_briefing(meeting, Settings(tavily_key="fake"), now=now, tavily=search)


def test_health():
    client = BifrostClient(Settings(), mock_client(lambda r: httpx.Response(200, json={"data": [{"id": "openai/gpt-4o-mini"}]})))
    assert client.health()["model_listed"]


def test_live_pipeline(meeting, now, rows):
    settings = Settings(tavily_key="fake", virtual_key="fake-vk")
    calls = []
    def search(req):
        calls.append(str(req.url))
        return httpx.Response(200, json={"results": rows})
    def inference(req):
        from src.validation import research_window
        evidence = build_evidence(rows, meeting, research_window(meeting, now))
        return httpx.Response(200, json={"choices": [{"message": {"content": demo_draft(evidence).model_dump_json()}}]})
    b = generate_briefing(meeting, settings, now=now, tavily=TavilyClient(settings, mock_client(search)), bifrost=BifrostClient(settings, mock_client(inference)))
    assert not b.demo and len(b.evidence.sources) == 3 and len(calls) == 3
    assert b.metadata["gateway"] == "Bifrost"


def test_partial_search_failure(meeting, now, rows):
    settings = Settings(tavily_key="fake")
    calls = []
    def search(req):
        calls.append(req)
        return httpx.Response(401) if len(calls) == 1 else httpx.Response(200, json={"results": rows})
    b = generate_briefing(meeting, settings, now=now, tavily=TavilyClient(settings, mock_client(search)),
                          bifrost=type("FakeGateway", (), {"generate": lambda self, m, w, e: (demo_draft(e), {})})())
    assert any("401" in n for n in b.evidence.notes)


def test_far_future_skips_network(meeting, now):
    from datetime import timedelta
    meeting = meeting.model_copy(update={"when": meeting.when + timedelta(days=90)})
    b = generate_briefing(meeting, Settings(), now=now)
    assert not b.evidence.queries and not b.evidence.sources


def test_malformed_tavily(window):
    client = TavilyClient(Settings(), mock_client(lambda r: httpx.Response(200, json={"results": "invalid"})))
    with pytest.raises(BriefIQError, match="malformed"):
        client.search("query", window)
