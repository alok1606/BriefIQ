# BriefIQ

**Walk Into Every Meeting Prepared** · Global AI Hackathon 2026 · Problem Statement 05

A Python 3.11+ / Streamlit research agent for preparing a concise, source-attributed meeting brief from the 30 days preceding a company or public professional meeting. Tavily searches live public information; Maxim AI's Bifrost is the sole inference gateway. Includes a deliberately fictional, offline demo.

## Run on Windows in VS Code (no administrator rights)

Install Python 3.11+ for your user account with the Python installer, then open this folder in VS Code. Use a PowerShell terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501. No activation or execution-policy changes are required. If `py` is unavailable, use `python`. Select `.venv\Scripts\python.exe` as the VS Code interpreter. macOS/Linux equivalents: `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, `.venv/bin/python -m streamlit run app.py`.

## Demo

Leave `BRIEFIQ_MODE=demo`. Click **Generate Briefing**. Demo uses only the fictional company **Northstar Labs**, fixed meeting time **15 November 2026 16:00 Asia/Kolkata**, fixed research clock **15 November 2026 09:00 UTC**, and local fixtures. Dates and entity are locked to prevent presenting fixture events as real research about another subject. All reports and exports carry a fictional demo label; example.org references are illustrative, not verifiable news. No API key, network, gateway, or LLM is used in demo mode.

## Live configuration

**Free-tier option:** use Gemini 3.5 Flash-Lite through Bifrost. Follow [FREE_MODEL_SETUP.md](FREE_MODEL_SETUP.md) for the private key setup and the supplied gateway launcher. The example environment now selects Gemini; its free tier is quota-limited and depends on your Google project. GPT-4o-mini remains an optional paid provider choice.

1. Obtain a Tavily API key from https://app.tavily.com and set `TAVILY_API_KEY` in `.env`.
2. Run Maxim's Bifrost gateway locally or use your organization's existing authenticated gateway. An optional local evaluation command, requiring Node/npm, is `npx -y @maximhq/bifrost`. Alternatively run `docker run -p 8080:8080 maximhq/bifrost` if Docker is already installed. Neither is needed for demo. Configure a provider and its credentials in the Bifrost dashboard at http://localhost:8080; provider keys do not belong in this app.
3. Set `BIFROST_BASE_URL=http://localhost:8080`, `BIFROST_MODEL=openai/gpt-4o-mini` (or your configured provider/model), and `BRIEFIQ_MODE=live`. Select Live in the sidebar.
4. If governance is enabled, set `BIFROST_VIRTUAL_KEY` (sent as `x-bf-vk`). Set `BIFROST_API_KEY` only if your gateway additionally expects HTTP Bearer authentication. Basic authentication is not implemented. Remote gateways require HTTPS; local HTTP is permitted.
5. Open Settings / About and select **Check Bifrost configuration**. This performs authenticated `GET /v1/models`; discovery verifies reachability and model visibility, not successful inference or provider balance. Generate a briefing to test the actual inference path. Models must support OpenAI-compatible chat JSON output; malformed or oversized responses are rejected with a retry message.

Never commit `.env`. Restart Streamlit after changing environment configuration. No direct provider fallback exists. Live failures never silently become demo results.

### Documented integration contracts

Verified against official documentation during implementation:

- [Tavily Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search): Bearer-authenticated `POST https://api.tavily.com/search`, advanced news searches, `start_date`, `end_date`, `include_published_date`. Three targeted queries, six results each. Up to six search credits per generation before retries (check your plan). Day-granularity search bounds are deliberately broad; local filtering checks precise timestamps. Requesting dates does not guarantee every source has one.
- [Maxim Bifrost gateway](https://docs.getbifrost.ai/quickstart/gateway/setting-up): `POST /v1/chat/completions`, OpenAI-compatible messages, provider/model names. Base URL accepts origin or `/v1`. `GET /v1/models` is used for configuration discovery.
- [Bifrost virtual keys](https://docs.getbifrost.ai/features/governance/virtual-keys): dedicated `x-bf-vk` header, separate from HTTP authentication. Configure provider permissions and budgets at the gateway.

## Architecture and evidence policy

```text
Streamlit context form
  -> validated zoned meeting -> UTC 30-day window (end capped at now)
  -> 3 Tavily searches -> canonical URL/title deduplication + target/date filtering
  -> bounded evidence package (up to 12 excerpts, stable S1... IDs)
  -> Bifrost -> configured provider -> Pydantic JSON draft
  -> citation ID validation + uncertainty enforcement + content budget
  -> interactive briefing / Markdown / one-page ReportLab PDF
```

`src/validation.py` handles IANA zones and rejects nonexistent/ambiguous daylight-saving times. The window is exactly 30 elapsed days before the meeting in UTC, capped at the research timestamp. For meetings more than 30 days away the window has not started, so no search or inference is performed. Historical reports warn that current indexes and edited pages cannot prove past availability.

`src/evidence.py` drops unrelated results using a conservative normalized full-target match, unsafe URLs, duplicates, and definitely out-of-window dates. Missing/invalid dates remain explicitly undated; date-only or timezone-less timestamps at boundaries remain uncertain. A source-backed label means a model claim is attributed to an in-window retrieved excerpt, **not** independent fact verification. Date metadata itself can be wrong. Source text is displayed for review. Entity disambiguation is conservative text matching, not resolved identity.

Every summary/development has structured citation IDs. Unknown IDs reject the report; missing citations or any undated/boundary source force an uncertain label. The model cannot establish factual support just by attaching an ID: human review remains necessary. Implications and discussion points are labeled analysis. Open questions are prompts, not established facts. Empty evidence produces a transparent insufficient-evidence report without calling an LLM. Partial search failures appear as scope notes; all failed searches produce an error.

Retrieved excerpts and all user fields are sent as untrusted data, with system-level instructions to ignore embedded directives, use only provided evidence, and avoid private personal information. No tools or page instructions are executed. HTML is not enabled for any retrieved/model text. Source URLs are links only, not fetched by the app. This reduces prompt injection exposure but cannot eliminate model errors. Names, purposes, and public source snippets are sent to Tavily/Bifrost/provider in live mode; use public professional context only.

`src/utils.py` bounds HTTP attempts to three, retries network/timeouts/429/5xx with capped exponential backoff, and returns safe errors without raw API bodies. JSON and response structure are validated. The gateway may have its own retry policy; coordinate budgets there. Provider request ID/model, measured latency, and numeric token counts appear where available; arbitrary response metadata is not displayed.

## Exports

Reports contain subject/time, research period, executive summary, up to five developments with implications and discussion points, three to five questions, references, and uncertainty notes. PDF references are clickable full-URL annotations with readable titles/IDs. All evidence references and scope notes are preserved. The exporter retries layout at 9, 8.5, then 8 point text and checks actual page count with pypdf. If content cannot fit one A4 page, it raises a visible error and offers the complete Markdown; it never cuts content to force fit. The UI's code block includes a built-in copy button.

## Automated tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use httpx MockTransport and fixture data; no real API credits required. Covers input validation, timezones/DST, historical/future windows, URL/title duplication, missing/malformed/date-only publication dates, relevance, unsupported citations, empty results, API errors/timeouts/retry bounds, malformed LLM JSON, Bifrost/Tavily request contracts, discovery, demo, Markdown escaping, PDF page count/citations/overflow, and Streamlit demo generation. GitHub Actions runs tests on Python 3.11 and 3.13. Local executed results are recorded in `VERIFICATION.md`; CI status must be checked independently.

## Requirement mapping

| Hackathon requirement | Implementation |
| --- | --- |
| Company/person and meeting time | Context form; validated timezone-aware Meeting |
| Prior 30 days, meaningful changes | Three launch/news, leadership/hiring, partnership/strategy searches |
| Concise one-page brief | Structured Draft, content budget, verified one-page PDF |
| Verifiable attribution | Stable retrieved source IDs, clickable URLs, excerpts, citation validation |
| Discussion/open questions | Per-development discussion point plus 3-5 questions |
| Tavily + Bifrost | Live research and sole live LLM gateway; documented and mock-tested contracts |
| Uncertainty and trust | Missing-date labels, unsupported-claim demotion, historical/future notes |

## Deployment and limitations

This is a complete local hackathon application with production-oriented boundaries, not a certified production service. No user accounts, durable database, shared tenant isolation, background queue, or distributed rate limit is included. Recent briefings are current-session memory only (ten entries); refresh/session expiry can clear them. Do not expose this server to the public internet without authentication, TLS, request quotas, and a data-retention policy. Streamlit's normal server protections remain enabled. Briefing generation is synchronous and bounded, but several failed calls can take minutes at the configured timeout. No full-page extraction, independent semantic fact-checker, paywall access, or comprehensive identity resolution is claimed. Search coverage can miss events and duplicate syndications. PDF uses a bundled Unicode font when present; scripts outside its glyph coverage may require a suitable licensed font. Do not enter private details.

## Two-minute presentation script

**0:00–0:20 — Problem.** “Before an important meeting, useful information is scattered across announcements, launches, and leadership news. A fluent AI summary is not enough if we cannot trace its claims. BriefIQ helps us walk into every meeting prepared.”

**0:20–0:45 — Workflow.** “Choose a company or person, meeting time, timezone, and optional purpose. BriefIQ calculates the preceding 30 days. Tavily runs three focused searches. We deduplicate results, filter dates, and assemble an inspectable evidence package.”

**0:45–1:15 — Agent architecture.** “The evidence goes through Maxim AI's Bifrost gateway to our configured model. Bifrost centralizes model routing, authentication, budgets, and observability. The app never bypasses it. Generated JSON is schema checked, and citation IDs must correspond to retrieved sources.”

**1:15–1:40 — Demo.** “This screen is explicitly labeled fictional demo mode; it is not live research. Here are the executive summary, key developments, potential implications, and useful questions. Each finding has evidence labels and inspectable source excerpts. In live mode these links point to Tavily-retrieved pages.”

**1:40–2:00 — Trust and takeaway.** “Unknown dates are uncertain, future meetings use only currently available information, and historical meetings carry verification limits. We can export a readable one-page PDF or complete Markdown. BriefIQ gives us a concise starting point we can verify, with the right questions to ask next.”
