# Executed verification

Verified on Windows, Python 3.13.4, 15 November 2026.

## Current local checks

- Full automated suite: **48 passed in 6.10 seconds** in the project's clean `.venv` (`python -m pytest -q`), after the PDF overflow fix.
- `python -m pip check`: **No broken requirements found**.
- BriefIQ started at `http://127.0.0.1:8501`; its health endpoint returned **ok**.
- Bifrost v2.4.0 started at `http://127.0.0.1:8787` with SQLite configuration storage and active governance.
- Authenticated `GET /v1/models` succeeded and listed the selected model.
- A real `POST /v1/chat/completions` through Bifrost to **Gemini 3.5 Flash-Lite** returned **HTTP 200** and valid JSON.
- Full live pipeline: Microsoft meeting on 16 November 2026, Tavily's three searches, **12 retrieved sources**, **4 generated developments**, and citation-ID validation succeeded. The run was explicitly live, not fixture mode.
- Live Markdown and one-page PDF exports were generated. The PDF was rendered with Poppler and visually inspected; no clipping or missing references was observed.
- Demo mode, mocked HTTP failures/timeouts, citation rejection, uncertain dates, DST validation, PDF overflow handling, and Streamlit AppTest remain covered by automated tests.

## PDF overflow regression

The original exporter included every retrieved article, even unused evidence, and repeated long references. The revised exporter includes all cited sources, switches to compact three-column references when needed, and preserves complete destination URLs. A dense five-development report with all 12 sources cited was verified on one page; all claim text, implications, discussion points, IDs and URL annotations are checked. Poppler rendering was visually inspected. Unused research remains in the complete Markdown and evidence panel. A deliberately oversized report verifies complete multi-page export with all 1,500 repeated test phrases retained, and Streamlit AppTest verifies that its download button is offered. No narrative text or uncertainty notes are silently removed. New LLM requests target 350-400 narrative words.

## Windows gateway fixes

Windows rejected binding to port 8080 with socket error 10013. The launcher now tests local ports, falls back to a permitted port, and synchronizes `BIFROST_BASE_URL` in the private `.env`. It keeps localhost binding and inference authentication enforced. A scoped virtual key is generated/reused in `.env`; config.json references credentials through environment variables. The gateway key permits only the selected Gemini model. SQLite storage resolves the governance/auth initialization issues seen with the original file-only profile. An existing official Windows v2.4.0 binary is reused to avoid unnecessary downloads.

Google rejected Gemini 2.5 Flash-Lite with HTTP 404 because it is unavailable to new accounts. Gemini 3.5 Flash-Lite was selected after its current official free-tier pricing was checked, and actual inference succeeded. Free-tier eligibility, quotas, and billing remain controlled by the user's Google project; a model name alone does not prove billing tier. No paid-provider fallback was configured.

## Earlier CI evidence

https://github.com/alok1606/BriefIQ/actions/runs/43683100525

Both Python 3.11 and 3.13 jobs successfully performed clean installation and automated tests for the earlier application commit. CI uses mocks and never uses live credentials. Later source revisions have separate Actions runs and should be checked by commit.

## Limits

A successful live pipeline does not independently fact-check every retrieved article or establish exhaustive search coverage. Citation validation proves that referenced IDs were retrieved, not that every inference is correct. Review original pages and entity matches. Live publication dates and indexed content can be inaccurate or later edited. Browser visual/responsive auditing was not completed because Windows browser automation could not verify the browser URL; frontend checks used Streamlit AppTest, HTTP startup checks, and the user's screenshots. The Bifrost management API remains locked until a dashboard admin is separately configured; this does not block authenticated BriefIQ inference.
