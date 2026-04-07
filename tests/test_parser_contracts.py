from fars.domain.models import PaperVersion
from fars.domain.types import PaperVersionType
from fars.parsers.grobid import GrobidParser


def test_grobid_parser_normalizes_sections_and_citations() -> None:
    parser = GrobidParser()
    version = PaperVersion(
        id="paper-bert-v1",
        paper_id="paper-bert",
        version_type=PaperVersionType.ARXIV,
    )

    document = parser.parse_fulltext(
        version,
        payload={
            "sections": [
                {
                    "id": "sec-1",
                    "section_type": "abstract",
                    "heading": "Abstract",
                    "order_index": 0,
                }
            ],
            "chunks": [
                {
                    "id": "chunk-1",
                    "section_id": "sec-1",
                    "text": "This paper introduces a bidirectional encoder representation.",
                }
            ],
            "citations": [
                {
                    "id": "cit-1",
                    "target_paper_id": "paper-attention",
                    "raw_reference": "Vaswani et al. 2017",
                    "resolution_confidence": 0.95,
                }
            ],
            "artifacts": [
                {
                    "id": "artifact-1",
                    "artifact_type": "tei",
                    "storage_uri": "s3://bucket/paper-bert-v1.tei.xml",
                    "content_type": "application/tei+xml",
                }
            ],
        },
    )

    assert document.paper_version.id == "paper-bert-v1"
    assert document.sections[0].heading == "Abstract"
    assert document.chunks[0].section_id == "sec-1"
    assert document.citations[0].target_paper_id == "paper-attention"
    assert document.artifacts[0].artifact_type == "tei"
