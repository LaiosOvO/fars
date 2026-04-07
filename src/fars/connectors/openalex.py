from __future__ import annotations

from typing import Any

import httpx

from fars.config import Settings, get_settings
from fars.models import IdentifierSet, PaperRecord
from fars.services.normalize import normalize_identifiers, normalize_title


class OpenAlexClient:
    def __init__(self, settings: Settings | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = client

    async def search_works(self, query: str, per_page: int = 10) -> list[PaperRecord]:
        params: dict[str, Any] = {"search": query, "per-page": per_page}
        if self.settings.openalex_api_key:
            params["api_key"] = self.settings.openalex_api_key

        async with self._get_client() as client:
            response = await client.get(f"{self.settings.openalex_base_url}/works", params=params)
            response.raise_for_status()
            payload = response.json()

        return [self._to_paper(work) for work in payload.get("results", [])]

    async def get_work(self, work_id: str) -> PaperRecord:
        params: dict[str, Any] = {}
        if self.settings.openalex_api_key:
            params["api_key"] = self.settings.openalex_api_key

        async with self._get_client() as client:
            response = await client.get(f"{self.settings.openalex_base_url}/works/{work_id}", params=params)
            response.raise_for_status()
            payload = response.json()

        return self._to_paper(payload)

    def _to_paper(self, work: dict[str, Any]) -> PaperRecord:
        identifiers = normalize_identifiers(
            IdentifierSet(
                doi=work.get("doi"),
                openalex_id=work.get("id", "").split("/")[-1] if work.get("id") else None,
            )
        )
        return PaperRecord(
            title=work.get("display_name") or "Untitled",
            abstract=work.get("abstract"),
            normalized_title=normalize_title(work.get("display_name")),
            year=work.get("publication_year"),
            venue=(work.get("primary_location") or {}).get("source", {}).get("display_name"),
            authors=[
                authorship.get("author", {}).get("display_name", "")
                for authorship in work.get("authorships", [])
                if authorship.get("author", {}).get("display_name")
            ],
            topics=[topic.get("display_name", "") for topic in work.get("topics", []) if topic.get("display_name")],
            identifiers=identifiers,
        )

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=20.0)
