from dataclasses import dataclass

from fars.domain.models import Citation, Paper, PaperEdge, PaperIdentifiers, PaperVersion
from fars.domain.types import PaperEdgeType, PaperVersionType


@dataclass
class InMemoryKnowledgeBase:
    papers: dict[str, Paper]
    versions: dict[str, list[PaperVersion]]
    edges: dict[str, list[PaperEdge]]
    citations: dict[str, list[Citation]]

    @classmethod
    def bootstrap(cls) -> "InMemoryKnowledgeBase":
        papers = {
            "paper-attention": Paper(
                id="paper-attention",
                canonical_title="Attention Is All You Need",
                identifiers=PaperIdentifiers(
                    doi="10.48550/arXiv.1706.03762",
                    arxiv_id="1706.03762",
                    openalex_id="W1",
                ),
                publication_year=2017,
                venue="NeurIPS",
                abstract="Transformer architecture based on attention mechanisms.",
                is_open_access=True,
                citation_count=100000,
                primary_source="openalex",
            ),
            "paper-bert": Paper(
                id="paper-bert",
                canonical_title="BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
                identifiers=PaperIdentifiers(
                    doi="10.48550/arXiv.1810.04805",
                    arxiv_id="1810.04805",
                    openalex_id="W2",
                ),
                publication_year=2018,
                venue="NAACL",
                abstract="Bidirectional language model pre-training using transformers.",
                is_open_access=True,
                citation_count=90000,
                primary_source="openalex",
            ),
            "paper-roberta": Paper(
                id="paper-roberta",
                canonical_title="RoBERTa: A Robustly Optimized BERT Pretraining Approach",
                identifiers=PaperIdentifiers(
                    doi="10.48550/arXiv.1907.11692",
                    arxiv_id="1907.11692",
                    openalex_id="W3",
                ),
                publication_year=2019,
                venue="arXiv",
                abstract="Improved BERT pretraining through optimization and scaling changes.",
                is_open_access=True,
                citation_count=50000,
                primary_source="openalex",
            ),
        }

        versions = {
            paper_id: [
                PaperVersion(
                    id=f"{paper_id}-v1",
                    paper_id=paper_id,
                    version_type=PaperVersionType.ARXIV,
                    source_url=paper.identifiers.arxiv_id,
                    pdf_url=f"https://arxiv.org/pdf/{paper.identifiers.arxiv_id}.pdf",
                )
            ]
            for paper_id, paper in papers.items()
        }

        edges = {
            "paper-roberta": [
                PaperEdge(
                    id="edge-roberta-bert",
                    src_paper_id="paper-roberta",
                    dst_paper_id="paper-bert",
                    edge_type=PaperEdgeType.EXTENDS,
                    confidence=0.95,
                    source="seed-data",
                ),
                PaperEdge(
                    id="edge-roberta-attention",
                    src_paper_id="paper-roberta",
                    dst_paper_id="paper-attention",
                    edge_type=PaperEdgeType.CITES,
                    confidence=0.99,
                    source="seed-data",
                ),
            ],
            "paper-bert": [
                PaperEdge(
                    id="edge-bert-attention",
                    src_paper_id="paper-bert",
                    dst_paper_id="paper-attention",
                    edge_type=PaperEdgeType.CITES,
                    confidence=0.99,
                    source="seed-data",
                )
            ],
            "paper-attention": [],
        }

        citations = {
            "paper-roberta-v1": [
                Citation(
                    id="citation-roberta-bert",
                    source_paper_version_id="paper-roberta-v1",
                    target_paper_id="paper-bert",
                    raw_reference="Devlin et al. 2018",
                    resolution_confidence=1.0,
                )
            ]
        }

        return cls(papers=papers, versions=versions, edges=edges, citations=citations)

    def search(self, query: str) -> list[Paper]:
        q = query.strip().lower()
        if not q:
            return []
        return [
            paper
            for paper in self.papers.values()
            if q in paper.canonical_title.lower() or (paper.abstract and q in paper.abstract.lower())
        ]

    def get(self, paper_id: str) -> Paper | None:
        return self.papers.get(paper_id)

    def list_versions(self, paper_id: str) -> list[PaperVersion]:
        return self.versions.get(paper_id, [])

    def neighbors(self, paper_id: str) -> list[PaperEdge]:
        return self.edges.get(paper_id, [])

    def list_references(self, paper_version_id: str) -> list[Citation]:
        return self.citations.get(paper_version_id, [])
