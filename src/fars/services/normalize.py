from __future__ import annotations

import re
from typing import Any

from fars.models import IdentifierSet


DOI_PREFIX_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:)", re.IGNORECASE)
ARXIV_PREFIX_RE = re.compile(r"^(?:arxiv:)", re.IGNORECASE)
OPENALEX_PREFIX_RE = re.compile(r"^(?:https?://api\.openalex\.org/works/)", re.IGNORECASE)
SEMANTIC_SCHOLAR_PREFIX_RE = re.compile(
    r"^(?:https?://(?:www\.)?semanticscholar\.org/paper/)",
    re.IGNORECASE,
)
WHITESPACE_RE = re.compile(r"\s+")


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    value = DOI_PREFIX_RE.sub("", value.strip())
    return value.lower() or None


def normalize_arxiv_id(value: str | None) -> str | None:
    if not value:
        return None
    value = ARXIV_PREFIX_RE.sub("", value.strip())
    value = value.split("v", 1)[0]
    return value or None


def normalize_openalex_id(value: str | None) -> str | None:
    if not value:
        return None
    value = OPENALEX_PREFIX_RE.sub("", value.strip())
    return value.upper() or None


def normalize_semantic_scholar_id(value: str | None) -> str | None:
    if not value:
        return None
    value = SEMANTIC_SCHOLAR_PREFIX_RE.sub("", value.strip().rstrip("/"))
    return value.split("/")[-1] or None


def normalize_title(value: str | None) -> str | None:
    if not value:
        return None
    normalized = WHITESPACE_RE.sub(" ", value.strip().lower())
    return normalized or None


def normalize_identifiers(data: IdentifierSet | dict[str, Any] | None) -> IdentifierSet:
    if data is None:
        return IdentifierSet()
    if isinstance(data, IdentifierSet):
        source = data.model_dump()
    else:
        source = dict(data)
    return IdentifierSet(
        doi=normalize_doi(source.get("doi")),
        arxiv_id=normalize_arxiv_id(source.get("arxiv_id")),
        openalex_id=normalize_openalex_id(source.get("openalex_id")),
        semantic_scholar_id=normalize_semantic_scholar_id(source.get("semantic_scholar_id")),
    )


def merge_identifiers(current: IdentifierSet, incoming: IdentifierSet) -> IdentifierSet:
    return IdentifierSet(
        doi=incoming.doi or current.doi,
        arxiv_id=incoming.arxiv_id or current.arxiv_id,
        openalex_id=incoming.openalex_id or current.openalex_id,
        semantic_scholar_id=incoming.semantic_scholar_id or current.semantic_scholar_id,
    )
