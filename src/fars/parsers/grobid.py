from fars.domain.models import (
    Citation,
    PaperChunk,
    PaperSection,
    PaperVersion,
    ParsedPaperDocument,
    SourceArtifact,
)
from fars.domain.types import SectionType


class GrobidParser:
    """Minimal normalized parser adapter matching a GROBID-style contract."""

    parser_name = "grobid"

    def parse_fulltext(
        self, paper_version: PaperVersion, payload: dict | None = None
    ) -> ParsedPaperDocument:
        payload = payload or {}
        sections_payload = payload.get("sections", [])
        citations_payload = payload.get("citations", [])
        artifacts_payload = payload.get("artifacts", [])

        sections = [
            PaperSection(
                id=section.get("id", f"{paper_version.id}-section-{idx}"),
                paper_version_id=paper_version.id,
                section_type=SectionType(section.get("section_type", SectionType.OTHER)),
                heading=section.get("heading"),
                order_index=section.get("order_index", idx),
            )
            for idx, section in enumerate(sections_payload, start=1)
        ]

        chunks = [
            PaperChunk(
                id=chunk.get("id", f"{paper_version.id}-chunk-{idx}"),
                section_id=chunk["section_id"],
                text=chunk["text"],
                page_start=chunk.get("page_start"),
                page_end=chunk.get("page_end"),
                bbox_json=chunk.get("bbox_json"),
            )
            for idx, chunk in enumerate(payload.get("chunks", []), start=1)
        ]

        citations = [
            Citation(
                id=item.get("id", f"{paper_version.id}-citation-{idx}"),
                source_paper_version_id=paper_version.id,
                target_paper_id=item.get("target_paper_id"),
                raw_reference=item["raw_reference"],
                citation_key=item.get("citation_key"),
                resolution_confidence=item.get("resolution_confidence", 0.0),
            )
            for idx, item in enumerate(citations_payload, start=1)
        ]

        artifacts = [
            SourceArtifact(
                id=item.get("id", f"{paper_version.id}-artifact-{idx}"),
                paper_version_id=paper_version.id,
                artifact_type=item.get("artifact_type", "tei"),
                storage_uri=item.get("storage_uri"),
                content_type=item.get("content_type"),
                created_at=item.get("created_at"),
            )
            for idx, item in enumerate(artifacts_payload, start=1)
        ]

        return ParsedPaperDocument(
            paper_version=paper_version,
            sections=sections,
            chunks=chunks,
            citations=citations,
            citation_contexts=[],
            artifacts=artifacts,
        )
