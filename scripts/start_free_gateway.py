"""Start a localhost-only Bifrost gateway configured for Gemini Flash-Lite.

Run with the project's virtual-environment Python. Never prints or writes keys.
"""
import json
import os
import secrets
from pathlib import Path
import shutil
import socket
import subprocess
import sys
from urllib.parse import urlsplit

from dotenv import dotenv_values, set_key


def available_port(preferred=8787):
    """Probe only local listeners; Windows may reserve a port without a listener."""
    for port in dict.fromkeys([preferred, 8787, 18080, 18787]):
        if not 1024 <= port <= 65535:
            continue
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
                if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                    listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                listener.bind(("127.0.0.1", port))
            return port
        except OSError:
            continue
    return None


def main():
    root = Path(__file__).resolve().parents[1]
    values = dotenv_values(root / ".env")
    key = os.environ.get("GEMINI_API_KEY") or values.get("GEMINI_API_KEY")
    if not key or key.strip() in ("YOUR_GEMINI_KEY", "your-key-here"):
        print("Save your Google AI Studio free-tier key as GEMINI_API_KEY in .env, then run this command again.")
        print("Create the key at https://aistudio.google.com/api-keys. Do not paste it into chat.")
        return 2
    npx = shutil.which("npx.cmd" if os.name == "nt" else "npx")
    binary = None
    if os.name == "nt":
        caches = [Path(os.environ.get("LOCALAPPDATA", "")), Path.home() / "AppData/Local"]
        binary = next((p for cache in caches if (p := cache / "bifrost/v2.4.0/bin/bifrost-http.exe-0").is_file()), None)
    if not binary and not npx:
        print("Node.js/npm is required to launch Bifrost. Install Node.js for your user account and retry.")
        return 2
    try:
        existing = urlsplit(values.get("BIFROST_BASE_URL") or "http://127.0.0.1:8787")
        preferred = (existing.port or 8787) if existing.hostname in ("localhost", "127.0.0.1") else 8787
    except ValueError:
        preferred = 8787
    port = available_port(preferred)
    if port is None:
        print("No available local gateway port. Close an old local gateway and retry.")
        return 2
    virtual_key = values.get("BIFROST_VIRTUAL_KEY") or "sk-bf-" + secrets.token_urlsafe(32)
    set_key(str(root / ".env"), "BIFROST_VIRTUAL_KEY", virtual_key)
    data = root / ".bifrost-free"
    data.mkdir(exist_ok=True)
    config = {"$schema": "https://www.getbifrost.ai/schema",
              "config_store": {"enabled": True, "type": "sqlite", "config": {"path": (data / "config.db").as_posix()}},
              "client": {"enforce_auth_on_inference": True},
              "governance": {"virtual_keys": [{"id": "briefiq-free-local", "name": "BriefIQ local Gemini",
                             "value": "env.BIFROST_VIRTUAL_KEY", "is_active": True,
                             "provider_configs": [{"provider": "gemini", "allowed_models": ["gemini-3.5-flash-lite"],
                                                   "key_ids": ["*"]}]}]},
              "providers": {"gemini": {"keys": [{"name": "briefiq-free-gemini",
                            "value": "env.GEMINI_API_KEY", "models": ["gemini-3.5-flash-lite"], "weight": 1.0}]}}}
    (data / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    env = os.environ.copy()
    env["GEMINI_API_KEY"] = key.strip()
    env["BIFROST_VIRTUAL_KEY"] = virtual_key
    url = f"http://127.0.0.1:{port}"
    set_key(str(root / ".env"), "BIFROST_BASE_URL", url)
    print(f"Starting Bifrost at {url} for Gemini 3.5 Flash-Lite.")
    print("BriefIQ's .env gateway address was updated; restart BriefIQ after starting this gateway.")
    print("Use a Google project on the free tier. Quotas apply; this launcher cannot verify billing status.")
    print("Keep this terminal open. Provider credentials remain in the child process environment.")
    command = [str(binary)] if binary else [npx, "-y", "@maximhq/bifrost@1.6.3", "--transport-version", "v2.4.0"]
    command += ["-host", "127.0.0.1", "-port", str(port), "-app-dir", str(data)]
    try:
        return subprocess.call(command, cwd=root, env=env)
    except KeyboardInterrupt:
        return 0
    except OSError:
        print("Could not launch Bifrost. Check Node.js/npm and network access.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
