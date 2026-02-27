"""Sync XeroML client — thin HTTP wrapper over the XeroML API."""

from __future__ import annotations

import httpx

from .errors import raise_for_status
from .session import Session
from .types import IntentGraph, SessionInfo, UsageInfo


class XeroML:
    """Synchronous XeroML client."""

    def __init__(self, api_key: str, base_url: str = "https://api.xeroml.com"):
        self.api_key = api_key
        self.base_url = base_url
        self._http = httpx.Client(
            base_url=base_url,
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            timeout=30.0,
        )

    def _request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        res = self._http.request(method, path, **kwargs)
        if not res.is_success:
            raise_for_status(res.status_code, res.json())
        return res

    def parse(self, message: str, provider: str | None = None) -> IntentGraph:
        body: dict[str, object] = {"message": message}
        if provider is not None:
            body["provider"] = provider
        res = self._request("POST", "/v1/parse", json=body)
        data = res.json()
        return IntentGraph(**data.get("graph", data))

    def create_session(self, session_id: str | None = None) -> Session:
        body: dict[str, object] = {}
        if session_id is not None:
            body["session_id"] = session_id
        res = self._request("POST", "/v1/sessions", json=body)
        sid = res.json()["session_id"]
        return Session(self, sid)

    def list_sessions(self) -> list[SessionInfo]:
        res = self._request("GET", "/v1/sessions")
        return [SessionInfo(**s) for s in res.json().get("sessions", res.json())]

    def get_usage(self) -> UsageInfo:
        res = self._request("GET", "/v1/usage")
        return UsageInfo(**res.json())

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> XeroML:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
