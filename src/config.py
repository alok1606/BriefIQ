import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    mode: str = "demo"
    tavily_key: str = field(default="", repr=False)
    bifrost_url: str = "http://localhost:8080"
    model: str = "openai/gpt-4o-mini"
    virtual_key: str = field(default="", repr=False)
    api_key: str = field(default="", repr=False)
    timeout: float = 45

    @classmethod
    def load(cls):
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        return cls(os.getenv("BRIEFIQ_MODE", "demo"), os.getenv("TAVILY_API_KEY", ""),
                   os.getenv("BIFROST_BASE_URL", "http://localhost:8080").rstrip("/"),
                   os.getenv("BIFROST_MODEL", "openai/gpt-4o-mini"),
                   os.getenv("BIFROST_VIRTUAL_KEY", ""), os.getenv("BIFROST_API_KEY", ""),
                   float(os.getenv("REQUEST_TIMEOUT", "45")))

    def validate_live(self, require_tavily=True):
        from .utils import BriefIQError
        u = urlsplit(self.bifrost_url)
        if require_tavily and not self.tavily_key:
            raise BriefIQError("Set TAVILY_API_KEY in .env before using live mode.")
        if u.scheme not in ("http", "https") or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise BriefIQError("BIFROST_BASE_URL must be a gateway HTTP(S) URL without credentials or query strings.")
        if u.scheme != "https" and u.hostname not in ("localhost", "127.0.0.1", "::1"):
            raise BriefIQError("Use HTTPS for a remote Bifrost gateway.")
        if not self.model or not 1 <= self.timeout <= 120:
            raise BriefIQError("Configure a model and REQUEST_TIMEOUT between 1 and 120 seconds.")
