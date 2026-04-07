from __future__ import annotations

from dataclasses import dataclass, field

from fars.models import EvidencePack, GraphNeighborhood, PaperEdge, PaperRecord
from fars.services.normalize import merge_identifiers, normalize_identifiers, normalize_title


@dataclass
class InMemoryKnowledgeBase:
    papers: dict[str, PaperRecord] = field(default_factory=dict)
    edges: dict[str, PaperEdge] = field(default_factory=dict)
    identifier_index: dict[tuple[str, str], str] = field(default_factory=dict)
    title_index: dict[str, str] = field(default_factory=dict)

    def upsert_paper(self, paper: PaperRecord) -> PaperRecord:
        normalized_identifiers = normalize_identifiers(paper.identifiers)
        normalized_title = normalize_title(paper.normalized_title or paper.title)
        existing_id = self._find_existing_id(normalized_identifiers, normalized_title)

        if existing_id:
            merged = self._merge_papers(self.papers[existing_id], paper, normalized_identifiers, normalized_title)
            self.papers[existing_id] = merged
            self._index_paper(merged)
            return merged

        created = paper.model_copy(
            update={
                "identifiers": normalized_identifiers,
                "normalized_title": normalized_title,
            }
        )
        self.papers[created.id] = created
        self._index_paper(created)
        return created

    def list_papers(self) -> list[PaperRecord]:
        return list(self.papers.values())

    def get_paper(self, paper_id: str) -> PaperRecord | None:
        return self.papers.get(paper_id)

    def add_edge(self, edge: PaperEdge) -> PaperEdge:
        self.edges[edge.id] = edge
        return edge

    def get_neighbors(self, paper_id: str) -> GraphNeighborhood:
        edges = [edge for edge in self.edges.values() if edge.src_paper_id == paper_id or edge.dst_paper_id == paper_id]
        related_ids = {paper_id}
        for edge in edges:
            related_ids.add(edge.src_paper_id)
            related_ids.add(edge.dst_paper_id)
        papers = [self.papers[p_id] for p_id in related_ids if p_id in self.papers]
        return GraphNeighborhood(paper_id=paper_id, papers=papers, edges=edges)

    def build_evidence_pack(self, paper_id: str, topic: str | None = None) -> EvidencePack:
        center = self.papers[paper_id]
        neighborhood = self.get_neighbors(paper_id)
        related = [paper for paper in neighborhood.papers if paper.id != paper_id]
        return EvidencePack(
            paper_id=paper_id,
            topic=topic,
            center_paper=center,
            related_papers=related,
            edges=neighborhood.edges,
        )

    def _find_existing_id(self, identifiers, normalized_title: str | None) -> str | None:
        for key in identifiers.keys():
            if key in self.identifier_index:
                return self.identifier_index[key]
        if normalized_title and normalized_title in self.title_index:
            return self.title_index[normalized_title]
        return None

    def _merge_papers(
        self,
        current: PaperRecord,
        incoming: PaperRecord,
        normalized_identifiers,
        normalized_title: str | None,
    ) -> PaperRecord:
        authors = list(dict.fromkeys([*current.authors, *incoming.authors]))
        topics = list(dict.fromkeys([*current.topics, *incoming.topics]))
        versions = [*current.versions]
        current_version_ids = {version.id for version in versions}
        for version in incoming.versions:
            if version.id not in current_version_ids:
                versions.append(version)

        return current.model_copy(
            update={
                "title": incoming.title or current.title,
                "abstract": incoming.abstract or current.abstract,
                "normalized_title": normalized_title or current.normalized_title,
                "year": incoming.year or current.year,
                "venue": incoming.venue or current.venue,
                "authors": authors,
                "topics": topics,
                "identifiers": merge_identifiers(current.identifiers, normalized_identifiers),
                "versions": versions,
                "parsed": incoming.parsed or current.parsed,
            }
        )

    def _index_paper(self, paper: PaperRecord) -> None:
        for key in paper.identifiers.keys():
            self.identifier_index[key] = paper.id
        if paper.normalized_title:
            self.title_index[paper.normalized_title] = paper.id
