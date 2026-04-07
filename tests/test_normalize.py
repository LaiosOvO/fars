from fars.models import IdentifierSet
from fars.services.normalize import (
    normalize_arxiv_id,
    normalize_doi,
    normalize_identifiers,
    normalize_openalex_id,
    normalize_semantic_scholar_id,
    normalize_title,
)


def test_identifier_normalization_strips_known_prefixes() -> None:
    identifiers = normalize_identifiers(
        IdentifierSet(
            doi="https://doi.org/10.1000/ABC-123",
            arxiv_id="arXiv:2401.12345v2",
            openalex_id="https://api.openalex.org/works/W123456789",
            semantic_scholar_id="https://www.semanticscholar.org/paper/abcdef1234567890",
        )
    )

    assert identifiers.doi == "10.1000/abc-123"
    assert identifiers.arxiv_id == "2401.12345"
    assert identifiers.openalex_id == "W123456789"
    assert identifiers.semantic_scholar_id == "abcdef1234567890"


def test_scalar_normalizers_handle_empty_values() -> None:
    assert normalize_doi(None) is None
    assert normalize_arxiv_id("") is None
    assert normalize_openalex_id(None) is None
    assert normalize_semantic_scholar_id(None) is None
    assert normalize_title("  A Useful Paper  ") == "a useful paper"
