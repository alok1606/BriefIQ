import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx


class BriefIQError(Exception):
    """Safe, user-facing error. Never includes raw API bodies or secrets."""


def canonical_url(value):
    try:
        if any(c.isspace() or c in '<>"' or ord(c) < 32 for c in str(value)):
            return None
        u = urlsplit(str(value))
        if u.scheme not in ("https", "http") or not u.hostname or u.username or u.password:
            return None
        if u.hostname in ("localhost", "127.0.0.1", "::1"):
            return None
        query = [(k, v) for k, v in parse_qsl(u.query) if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid")]
        return urlunsplit((u.scheme.lower(), u.netloc.lower(), u.path.rstrip("/") or "/", urlencode(sorted(query)), ""))
    except ValueError:
        return None


def request_json(client, method, url, service, **kwargs):
    for attempt in range(3):
        try:
            response = client.request(method, url, **kwargs)
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < 2:
                    time.sleep(0.5 * 2**attempt)
                    continue
            if response.status_code >= 400:
                hint = {401: "Check authentication.", 403: "Check permissions.", 429: "Rate limit reached; retry later.",
                        432: "Usage allowance exhausted.", 433: "Spending limit reached."}.get(response.status_code, "Check service configuration and retry.")
                raise BriefIQError(f"{service} returned HTTP {response.status_code}. {hint}")
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError()
            return data
        except (httpx.TimeoutException, httpx.NetworkError):
            if attempt == 2:
                raise BriefIQError(f"{service} could not be reached after 3 attempts. Check connectivity and retry.") from None
            time.sleep(0.5 * 2**attempt)
        except (ValueError, httpx.HTTPError):
            raise BriefIQError(f"{service} returned an invalid response. Retry or check configuration.") from None
