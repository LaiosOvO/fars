from __future__ import annotations

from typing import Protocol

import httpx
from pydantic import BaseModel, Field


class OpenAlexWork(BaseModel):
    openalex_id: str
    title: str
    doi: str | None = None
    arxiv_id: str | None = None
    publication_year: int | None = None
    venue: str | None = None
    abstract: str | None = None
    language: str | None = None
    is_open_access: bool = False
    pdf_url: str | None = None
    source_url: str | None = None
    citation_count: int = 0
    primary_source: str = Field(default="openalex")


class OpenAlexClientProtocol(Protocol):
    def search_topic(self, topic: str, limit: int = 10) -> list[OpenAlexWork]: ...


class OpenAlexHTTPClient:
    def __init__(self, base_url: str, timeout_seconds: float = 20.0, api_key: str | None = None, mailto: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.api_key = api_key
        self.mailto = mailto

    def search_topic(self, topic: str, limit: int = 10) -> list[OpenAlexWork]:
        params = {"search": topic, "per-page": limit}
        if self.api_key:
            params["api_key"] = self.api_key
        if self.mailto:
            params["mailto"] = self.mailto
        response = httpx.get(f"{self.base_url}/works", params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        return [self._to_work(item) for item in payload.get("results", [])]

    def _to_work(self, item: dict) -> OpenAlexWork:
        locations = item.get("best_oa_location") or item.get("primary_location") or {}
        source = locations.get("source") or {}
        ids = item.get("ids") or {}
        return OpenAlexWork(
            openalex_id=(item.get("id") or ids.get("openalex") or "").strip(),
            title=(item.get("title") or "Untitled").strip(),
            doi=self._normalize_doi(ids.get("doi") or item.get("doi")),
            publication_year=item.get("publication_year"),
            venue=source.get("display_name"),
            abstract=self._reconstruct_abstract(item.get("abstract_inverted_index")),
            language=item.get("language"),
            is_open_access=bool((item.get("open_access") or {}).get("is_oa", False)),
            pdf_url=locations.get("pdf_url"),
            source_url=locations.get("landing_page_url") or item.get("primary_location", {}).get("landing_page_url"),
            citation_count=item.get("cited_by_count", 0),
        )

    @staticmethod
    def _normalize_doi(doi: str | None) -> str | None:
        if not doi:
            return None
        doi = doi.strip()
        prefixes = ("https://doi.org/", "http://doi.org/", "doi:")
        for prefix in prefixes:
            if doi.lower().startswith(prefix):
                return doi[len(prefix) :]
        return doi

    @staticmethod
    def _reconstruct_abstract(inverted_index: dict | None) -> str | None:
        if not inverted_index:
            return None
        positions: dict[int, str] = {}
        for token, indexes in inverted_index.items():
            for index in indexes:
                positions[index] = token
        return " ".join(token for _, token in sorted(positions.items()))
