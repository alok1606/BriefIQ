# Executed verification

Verified locally on Windows, Python 3.13.4, 15 November 2026.

- Full test suite: **41 passed in 7.21 seconds** (`python -m pytest -q`). Tests include mocked HTTP integrations and Streamlit AppTest demo generation.
- Streamlit 1.45.1 server started successfully on `http://127.0.0.1:8501`.
- HTTP checks: root page returned **200**; `/_stcore/health` returned **ok**.
- Demo PDF: generated, reopened with pypdf, confirmed exactly one A4 page and three source-link annotations, rendered using Poppler, and visually inspected. No clipped content or missing references were observed.
- Markdown export generated and tested; dangerous Markdown/HTML controls are escaped.
- Source compile check completed successfully. Git whitespace checks completed successfully.

## Boundaries

Live Tavily and Bifrost inference were **not exercised**: no live API credentials or running gateway were configured. HTTP request contracts, successful and failing responses, timeout retries, model discovery, malformed output handling, and the live pipeline were tested with mocks. Neither real search quality nor real provider behavior is claimed verified.

Browser automation ended because it could not verify the Windows browser URL. Frontend validation therefore used Streamlit AppTest and HTTP startup checks; a visual browser screenshot/responsive layout audit was not completed.

Local dependency installation encountered download timeouts. Local QA used an isolated virtual environment with access to existing host packages, verified PyPI wheels for missing UI/test dependencies, and bundled ReportLab/pypdf packages. `pip check` on the shared local QA environment reported a pre-existing TensorFlow/protobuf conflict; TensorFlow is not used by BriefIQ. Clean installation was subsequently verified by GitHub Actions, as recorded below.

The complete source was published to `https://github.com/alok1606/BriefIQ` on main, commit `31db5da6b36d748ea107d6a8ac43f3cafcee706b`, using the authenticated GitHub connector. The local checkout was synchronized and tracks origin/main.

## GitHub Actions verification

Run: https://github.com/alok1606/BriefIQ/actions/runs/43683100525

Both `test (3.11)` and `test (3.13)` completed successfully on Linux. Each job successfully executed `python -m pip install -r requirements.txt` and `python -m pytest -q`. This verifies clean dependency installation and the automated suite on both supported Python versions for the published application commit. Live credentials are not used in CI.

