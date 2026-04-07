import pytest

from fars.domain.models import Citation, Paper, PaperEdge, PaperIdentifiers, PaperVersion
from fars.domain.types import PaperEdgeType, PaperVersionType


def test_paper_model_accepts_canonical_identifier_bundle() -> None:
    paper = Paper(
        id="paper-1",
        canonical_title="A Structured Paper Model",
        identifiers=PaperIdentifiers(
            doi="10.1000/example",
            openalex_id="W123",
        ),
        publication_year=2026,
        is_open_access=True,
    )

    assert paper.identifiers.doi == "10.1000/example"
    assert paper.identifiers.openalex_id == "W123"
    assert paper.is_open_access is True


def test_paper_version_defaults_to_unknown_type() -> None:
    version = PaperVersion(id="v1", paper_id="paper-1")

    assert version.version_type == PaperVersionType.UNKNOWN


def test_paper_edge_requires_valid_confidence_range() -> None:
    with pytest.raises(Exception):
        PaperEdge(
            id="edge-1",
            src_paper_id="paper-1",
            dst_paper_id="paper-2",
            edge_type=PaperEdgeType.CITES,
            confidence=1.5,
        )


def test_citation_resolution_confidence_is_bounded() -> None:
    citation = Citation(
        id="citation-1",
        source_paper_version_id="v1",
        raw_reference="Smith et al. 2024",
        resolution_confidence=0.75,
    )

    assert citation.resolution_confidence == 0.75
