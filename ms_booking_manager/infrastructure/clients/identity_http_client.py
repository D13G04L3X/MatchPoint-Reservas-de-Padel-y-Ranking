from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from domain.ports.identity_client import IdentityClient


class IdentityServiceUnavailable(Exception):
    """Raised when MS-Identity is unavailable or returns unexpected responses."""


class IdentityHttpClient(IdentityClient):
    """HTTP client for MS-Identity endpoints."""

    def __init__(self, base_url: str | None = None) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url or settings.IDENTITY_SERVICE_URL,
            timeout=httpx.Timeout(3.0),
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""

        await self._client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.2, max=1.0))
    async def _get(self, path: str) -> dict[str, Any]:
        try:
            response = await self._client.get(path)
        except (httpx.RequestError, httpx.TimeoutException) as exc:
            raise IdentityServiceUnavailable("MS-Identity request failed.") from exc

        if response.status_code != 200:
            raise IdentityServiceUnavailable(
                f"MS-Identity returned status {response.status_code}."
            )

        try:
            return response.json()
        except ValueError as exc:
            raise IdentityServiceUnavailable("MS-Identity returned invalid JSON.") from exc

    async def validate_membership(self, player_id: UUID) -> bool:
        data = await self._get(f"/internal/membership/{player_id}/validate")
        return bool(data.get("is_valid", data.get("is_active", False)))

    async def get_player_restriction(self, player_id: UUID) -> bool:
        try:
            response = await self._client.get(f"/internal/restriction/{player_id}")
        except (httpx.RequestError, httpx.TimeoutException) as exc:
            raise IdentityServiceUnavailable("MS-Identity request failed.") from exc

        if response.status_code == 404:
            return False
        if response.status_code != 200:
            raise IdentityServiceUnavailable(
                f"MS-Identity returned status {response.status_code}."
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise IdentityServiceUnavailable("MS-Identity returned invalid JSON.") from exc

        return bool(
            data.get(
                "has_restriction",
                data.get("restriction_active", data.get("is_restricted", False)),
            )
        )

