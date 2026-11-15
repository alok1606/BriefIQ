# Free-tier model setup

BriefIQ can use **Google Gemini 3.5 Flash-Lite through Bifrost**. Google currently lists free input/output tokens on its free API tier, subject to project eligibility, regional availability, and quotas. Use a free-tier Google AI Studio project; model selection alone does not make a paid project free. This setup does not enable billing or add paid fallbacks. Free-tier content may be used to improve Google's products; use public professional meeting context only.

GPT-4o-mini API usage is paid. It does not require a monthly ChatGPT subscription. Bifrost is the gateway, not a free source of provider credits. Tavily research has its own credit allowance, separate from Gemini.

## 1. Obtain your Google key

Go to https://aistudio.google.com/api-keys, sign in, and create/select a project on the free tier. Create an API key and save it locally in the project's ignored `.env` file. Do not paste it into chat, GitHub, or screenshots. Do not enable paid billing if you want to remain on the free tier.

```dotenv
GEMINI_API_KEY=your-actual-google-key
BIFROST_MODEL=gemini/gemini-3.5-flash-lite
BIFROST_BASE_URL=http://127.0.0.1:8787
```

Keep your existing `TAVILY_API_KEY` intact. Keep `BRIEFIQ_MODE=demo` until the gateway is ready.

## 2. Start the free-provider gateway

From the project folder in PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts\start_free_gateway.py
```

This loads the Google key into Bifrost's process environment, writes a secret-free provider configuration into ignored `.bifrost-free/`, and launches pinned Bifrost. An existing official Windows v2.4.0 binary is reused; otherwise npm downloads it. Node.js/npm and internet access are required for the first download. The launcher enables a local SQLite configuration store and creates/reuses a scoped virtual key in `.env`, referenced by environment variable in Bifrost's config. BriefIQ sends that key as `x-bf-vk`. The key allows only `gemini-3.5-flash-lite`, with no paid-provider fallback. This cannot establish your Google project's billing tier.

Keep the terminal open. The launcher checks whether Windows permits the configured local port and falls back to 8787, 18080, or 18787 when it is occupied/reserved. It updates `BIFROST_BASE_URL` in `.env` automatically. Restart BriefIQ afterward so it reads the updated address and virtual key. No administrator privileges or firewall changes are required. This is a dedicated local profile; do not use it to overwrite a shared or production gateway.

Alternatively, use an existing Bifrost instance: go to its Model Providers settings, select Google Gemini, add your Google API key, and restrict Allowed Models to `gemini-3.5-flash-lite`. Configure that gateway's own authentication in `.env` as required. Setting a key only in BriefIQ's `.env` does not automatically configure an already-running gateway. The supplied local profile keeps inference authentication enforced; its management API may remain locked until you separately configure a dashboard admin account. The dashboard is not needed to use BriefIQ.

## 3. Start BriefIQ and verify

In a second terminal:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501, go to Settings / About, and run the Bifrost configuration check. Discovery verifies connectivity, not successful inference or your billing tier. Select Live in the sidebar and generate a real company briefing. Model request information should show Bifrost and `gemini/gemini-3.5-flash-lite`; verify the gateway's logs too.

Quota/rate-limit errors mean you must wait for quota reset or check your free project limits. Do not switch on paid billing just to bypass a limit. A missing-key message means the gateway has not yet been configured; it is not a successful live test.

## Official references

- https://developers.openai.com/api/docs/models/gpt-4o-mini
- https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite
- https://docs.getbifrost.ai/providers/supported-providers/gemini
- https://docs.getbifrost.ai/quickstart/gateway/setting-up

Live Gemini 3.5 Flash-Lite inference was verified through Bifrost with HTTP 200 and valid JSON after a local key was supplied. Account quota and availability may differ. Google rejected 2.5 Flash-Lite for a new account, so the setup now uses 3.5 Flash-Lite. The project never presents fixture runs as live results.
