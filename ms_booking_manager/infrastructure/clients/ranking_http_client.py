from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from config import settings
from domain.ports.ranking_client import RankingClient


class RankingServiceUnavailable(Exception):
    """Raised when MS-PenaltyRank is unavailable or returns unexpected responses."""


class RankingHttpClient(RankingClient):
    """HTTP client for MS-PenaltyRank endpoints."""

    def __init__(self, base_url: str | None = None) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url or settings.PENALTY_SERVICE_URL,
            timeout=httpx.Timeout(3.0),
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""

        await self._client.aclose()

    async def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        if response.status_code != 200:
            raise RankingServiceUnavailable(
                f"MS-PenaltyRank returned status {response.status_code}."
            )
        try:
            return response.json()
        except ValueError as exc:
            raise RankingServiceUnavailable("MS-PenaltyRank returned invalid JSON.") from exc

    async def get_player_level(self, player_id: UUID) -> float:
        try:
            response = await self._client.get(f"/internal/rank/{player_id}")
        except (httpx.RequestError, httpx.TimeoutException) as exc:
            raise RankingServiceUnavailable("MS-PenaltyRank request failed.") from exc

        data = await self._handle_response(response)
        return float(data.get("level", 0.0))

    async def get_players_levels(self, player_ids: list[UUID]) -> dict[UUID, float]:
        payload = {"player_ids": [str(player_id) for player_id in player_ids]}
        try:
            response = await self._client.post("/internal/rank/batch", json=payload)
        except (httpx.RequestError, httpx.TimeoutException) as exc:
            raise RankingServiceUnavailable("MS-PenaltyRank request failed.") from exc

        data = await self._handle_response(response)
        levels = data.get("levels", data)
        return {UUID(player_id): float(level) for player_id, level in levels.items()}

