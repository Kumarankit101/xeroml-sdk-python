"""Session classes for multi-turn conversations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from .types import DriftReport, IntentGraph

if TYPE_CHECKING:
    from .async_client import AsyncXeroML
    from .client import XeroML


class Session:
    """Sync session for multi-turn intent tracking."""

    def __init__(self, client: XeroML, session_id: str):
        self._client = client
        self.session_id = session_id

    def _request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        return self._client._request(method, path, **kwargs)

    def parse(self, message: str, provider: str | None = None) -> IntentGraph:
        body: dict[str, object] = {"message": message}
        if provider is not None:
            body["provider"] = provider
        res = self._request("POST", f"/v1/sessions/{self.session_id}/parse", json=body)
        data = res.json()
        return IntentGraph(**data.get("graph", data))

    def update(self, response: str, role: str = "assistant") -> None:
        self._request(
            "POST",
            f"/v1/sessions/{self.session_id}/update",
            json={"response": response, "role": role},
        )

    def check_drift(self) -> DriftReport:
        res = self._request("GET", f"/v1/sessions/{self.session_id}/drift")
        return DriftReport(**res.json())

    def get_graph(self) -> IntentGraph:
        res = self._request("GET", f"/v1/sessions/{self.session_id}/graph")
        data = res.json()
        return IntentGraph(**data.get("graph", data))

    def end(self) -> None:
        self._request("POST", f"/v1/sessions/{self.session_id}/end", json={})


class AsyncSession:
    """Async session for multi-turn intent tracking."""

    def __init__(self, client: AsyncXeroML, session_id: str):
        self._client = client
        self.session_id = session_id

    async def _request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        return await self._client._request(method, path, **kwargs)

    async def parse(self, message: str, provider: str | None = None) -> IntentGraph:
        body: dict[str, object] = {"message": message}
        if provider is not None:
            body["provider"] = provider
        res = await self._request("POST", f"/v1/sessions/{self.session_id}/parse", json=body)
        data = res.json()
        return IntentGraph(**data.get("graph", data))

    async def update(self, response: str, role: str = "assistant") -> None:
        await self._request(
            "POST",
            f"/v1/sessions/{self.session_id}/update",
            json={"response": response, "role": role},
        )

    async def check_drift(self) -> DriftReport:
        res = await self._request("GET", f"/v1/sessions/{self.session_id}/drift")
        return DriftReport(**res.json())

    async def get_graph(self) -> IntentGraph:
        res = await self._request("GET", f"/v1/sessions/{self.session_id}/graph")
        data = res.json()
        return IntentGraph(**data.get("graph", data))

    async def end(self) -> None:
        await self._request("POST", f"/v1/sessions/{self.session_id}/end", json={})
