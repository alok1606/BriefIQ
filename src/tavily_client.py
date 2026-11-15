from datetime import timedelta

import httpx

from .utils import BriefIQError, request_json


class TavilyClient:
    def __init__(self, settings, client=None):
        self.settings = settings
        self.client = client

    def search(self, query, window):
        payload = dict(query=query, topic="news", search_depth="advanced", max_results=6,
                       start_date=window.start.date().isoformat(),
                       end_date=(window.end.date() + timedelta(days=1)).isoformat(),
                       include_published_date=True, include_answer=False, include_raw_content=False)
        def run(client):
            data = request_json(client, "POST", "https://api.tavily.com/search", "Tavily",
                                headers={"Authorization": f"Bearer {self.settings.tavily_key}"}, json=payload)
            results = data.get("results")
            if not isinstance(results, list) or not all(isinstance(r, dict) for r in results):
                raise BriefIQError("Tavily returned malformed search results.")
            return results
        if self.client:
            return run(self.client)
        with httpx.Client(timeout=self.settings.timeout) as client:
            return run(client)
