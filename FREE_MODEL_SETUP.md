# Free-tier model setup

BriefIQ can use **Google Gemini 2.5 Flash-Lite through Bifrost**. Google currently lists free input/output tokens on its free API tier, subject to project eligibility, regional availability, and quotas. Use a free-tier Google AI Studio project; model selection alone does not make a paid project free. This setup does not enable billing or add paid fallbacks. Free-tier content may be used to improve Google's products; use public professional meeting context only.

GPT-4o-mini API usage is paid. It does not require a monthly ChatGPT subscription. Bifrost is the gateway, not a free source of provider credits. Tavily research has its own credit allowance, separate from Gemini.

## 1. Obtain your Google key

Go to https://aistudio.google.com/api-keys, sign in, and create/select a project on the free tier. Create an API key and save it locally in the project's ignored `.env` file. Do not paste it into chat, GitHub, or screenshots. Do not enable paid billing if you want to remain on the free tier.

```dotenv
GEMINI_API_KEY=your-actual-google-key
BIFROST_MODEL=gemini/gemini-2.5-flash-lite
BIFROST_BASE_URL=http://localhost:8080
```

Keep your existing `TAVILY_API_KEY` intact. Keep `BRIEFIQ_MODE=demo` until the gateway is ready.

## 2. Start the free-provider gateway

From the project folder in PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts\start_free_gateway.py
```

This loads only the Google key from `.env` into Bifrost's process environment, writes a secret-free Gemini provider configuration into ignored `.bifrost-free/`, and launches pinned Bifrost locally via npm. It does not call Google directly. Node.js/npm and internet access for the first gateway download are required. The launcher allows only `gemini-2.5-flash-lite` in its Gemini key configuration and does not configure any paid-provider fallback. It cannot inspect your Google project's billing tier.

Keep the terminal open. If port 8080 is already occupied, stop the Bifrost instance you previously started before launching this profile. This is a separate file-configured local instance; do not use it to overwrite a shared or production gateway.

Alternatively, use an existing Bifrost instance: open http://localhost:8080, go to Models / Model Providers, select Google Gemini, add your Google API key, and restrict Allowed Models to `gemini-2.5-flash-lite`. When using the existing gateway, configure its own authentication in `.env` as required. Setting a key only in BriefIQ's `.env` does not automatically configure an already-running gateway.

## 3. Start BriefIQ and verify

In a second terminal:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501, go to Settings / About, and run the Bifrost configuration check. Discovery verifies connectivity, not successful inference or your billing tier. Select Live in the sidebar and generate a real company briefing. Model request information should show Bifrost and `gemini/gemini-2.5-flash-lite`; verify the gateway's logs too.

Quota/rate-limit errors mean you must wait for quota reset or check your free project limits. Do not switch on paid billing just to bypass a limit. A missing-key message means the gateway has not yet been configured; it is not a successful live test.

## Official references

- https://developers.openai.com/api/docs/models/gpt-4o-mini
- https://ai.google.dev/gemini-api/docs/pricing#gemini-2.5-flash-lite
- https://docs.getbifrost.ai/providers/supported-providers/gemini
- https://docs.getbifrost.ai/quickstart/gateway/setting-up

Live Gemini inference cannot be verified until you supply a valid key in your local environment. The project never claims that a mock or fixture run is a live free-tier model test.
