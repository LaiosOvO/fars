from fars.models import IdentifierSet, PaperEdge, PaperRecord
from fars.repository import InMemoryKnowledgeBase


def test_repository_merges_records_by_doi() -> None:
    repo = InMemoryKnowledgeBase()

    first = repo.upsert_paper(
        PaperRecord(
            title="An Excellent Paper",
            abstract="first abstract",
            identifiers=IdentifierSet(doi="10.1000/xyz"),
            authors=["Alice"],
        )
    )
    second = repo.upsert_paper(
        PaperRecord(
            title="An Excellent Paper",
            abstract="better abstract",
            identifiers=IdentifierSet(doi="https://doi.org/10.1000/xyz"),
            authors=["Bob"],
        )
    )

    assert first.id == second.id
    merged = repo.get_paper(first.id)
    assert merged is not None
    assert merged.abstract == "better abstract"
    assert set(merged.authors) == {"Alice", "Bob"}


def test_repository_neighbors_and_evidence_pack() -> None:
    repo = InMemoryKnowledgeBase()
    one = repo.upsert_paper(PaperRecord(title="Paper One"))
    two = repo.upsert_paper(PaperRecord(title="Paper Two"))

    edge = repo.add_edge(
        PaperEdge(src_paper_id=one.id, dst_paper_id=two.id, edge_type="cites", evidence_text="baseline comparison")
    )

    neighborhood = repo.get_neighbors(one.id)
    assert {paper.id for paper in neighborhood.papers} == {one.id, two.id}
    assert neighborhood.edges[0].id == edge.id

    evidence = repo.build_evidence_pack(one.id, topic="citation graphs")
    assert evidence.center_paper.id == one.id
    assert [paper.id for paper in evidence.related_papers] == [two.id]
