"""Start a localhost-only Bifrost gateway configured for Gemini Flash-Lite.

Run with the project's virtual-environment Python. Never prints or writes keys.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from dotenv import dotenv_values


def main():
    root = Path(__file__).resolve().parents[1]
    values = dotenv_values(root / ".env")
    key = os.environ.get("GEMINI_API_KEY") or values.get("GEMINI_API_KEY")
    if not key or key.strip() in ("YOUR_GEMINI_KEY", "your-key-here"):
        print("Save your Google AI Studio free-tier key as GEMINI_API_KEY in .env, then run this command again.")
        print("Create the key at https://aistudio.google.com/api-keys. Do not paste it into chat.")
        return 2
    npx = shutil.which("npx.cmd" if os.name == "nt" else "npx")
    if not npx:
        print("Node.js/npm is required to launch Bifrost. Install Node.js for your user account and retry.")
        return 2
    data = root / ".bifrost-free"
    data.mkdir(exist_ok=True)
    config = {"$schema": "https://www.getbifrost.ai/schema", "config_store": {"enabled": False},
              "providers": {"gemini": {"keys": [{"name": "briefiq-free-gemini",
                            "value": "env.GEMINI_API_KEY", "models": ["gemini-2.5-flash-lite"], "weight": 1.0}]}}}
    (data / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    env = os.environ.copy()
    env["GEMINI_API_KEY"] = key.strip()
    print("Starting Bifrost at http://127.0.0.1:8080 for Gemini 2.5 Flash-Lite.")
    print("Use a Google project on the free tier. Quotas apply; this launcher cannot verify billing status.")
    print("Keep this terminal open. Provider credentials remain in the child process environment.")
    try:
        return subprocess.call([npx, "-y", "@maximhq/bifrost@1.6.3", "--transport-version", "v2.4.0",
                                "-host", "127.0.0.1", "-port", "8080", "-app-dir", str(data)],
                               cwd=root, env=env)
    except KeyboardInterrupt:
        return 0
    except OSError:
        print("Could not launch Bifrost. Check Node.js/npm and network access.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
