from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from itertools import cycle, islice
from pathlib import Path
import os
import zipfile

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, selectinload

from fars_kg.connectors.openalex import OpenAlexWork
from fars_kg.models import (
    Citation,
    CitationContext,
    Dataset,
    EvidenceSnapshot,
    ExperimentPlan,
    ExperimentTask,
    ExperimentResult,
    Method,
    Metric,
    Paper,
    PaperChunk,
    PaperDatasetLink,
    PaperEdge,
    PaperMethodLink,
    PaperMetricLink,
    PaperSection,
    PaperVersion,
    ResearchHypothesis,
    ResearchIteration,
    ResearchRun,
    ResearchRunEvent,
)
from fars_kg.parsers.base import ParseResult


@dataclass
class UpsertResult:
    paper: Paper
    created: bool
    version: PaperVersion
    version_created: bool


@dataclass
class ParsePersistenceResult:
    sections_created: int
    chunks_created: int
    citations_created: int
    contexts_created: int
    edges_created: int


@dataclass
class SemanticEnrichmentResult:
    paper_id: int
    methods_attached: int
    datasets_attached: int
    metrics_attached: int


@dataclass
class SemanticEdgeInferenceResult:
    paper_id: int
    edges_created: int


@dataclass
class AutoSemanticEnrichmentResult(SemanticEnrichmentResult):
    extracted_methods: list[str]
    extracted_datasets: list[str]
    extracted_metrics: list[str]


def _json_dumps(payload: dict | list | None) -> str | None:
    if payload is None:
        return None
    return json.dumps(payload, sort_keys=True)


METHOD_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Transformer", re.compile(r"\btransformer(s)?\b", re.IGNORECASE)),
    ("BERT", re.compile(r"\bbert\b", re.IGNORECASE)),
    ("RoBERTa", re.compile(r"\broberta\b", re.IGNORECASE)),
    ("RAG", re.compile(r"\brag\b|retrieval augmented generation", re.IGNORECASE)),
]

DATASET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("WMT14", re.compile(r"\bwmt14\b", re.IGNORECASE)),
    ("Cora", re.compile(r"\bcora\b", re.IGNORECASE)),
    ("CiteSeer", re.compile(r"\bciteseer\b", re.IGNORECASE)),
    ("PubMed", re.compile(r"\bpubmed\b", re.IGNORECASE)),
    ("ImageNet", re.compile(r"\bimagenet\b", re.IGNORECASE)),
    ("CIFAR-10", re.compile(r"\bcifar[- ]?10\b", re.IGNORECASE)),
    ("SQuAD", re.compile(r"\bsquad\b", re.IGNORECASE)),
    ("GLUE", re.compile(r"\bglue\b", re.IGNORECASE)),
]

METRIC_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("BLEU", re.compile(r"\bbleu\b", re.IGNORECASE)),
    ("F1", re.compile(r"\bf1\b", re.IGNORECASE)),
    ("Accuracy", re.compile(r"\baccuracy\b", re.IGNORECASE)),
    ("ROUGE", re.compile(r"\brouge\b", re.IGNORECASE)),
    ("MRR", re.compile(r"\bmrr\b", re.IGNORECASE)),
]

RESULT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"\b(?P<method>Transformer|BERT|RoBERTa|RAG)\b.*?\b(?:achieves|gets|obtains|scores)\s+(?P<value>\d+(?:\.\d+)?)\s+(?P<metric>BLEU|F1|Accuracy|ROUGE|MRR)\b.*?\bon\s+(?P<dataset>WMT14|Cora|CiteSeer|PubMed|ImageNet|CIFAR-10|SQuAD|GLUE)\b",
        re.IGNORECASE,
    )
]


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    doi = doi.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.lower().startswith(prefix):
            return doi[len(prefix) :]
    return doi


def get_paper(session: Session, paper_id: int) -> Paper | None:
    stmt = (
        select(Paper)
        .where(Paper.id == paper_id)
        .options(selectinload(Paper.versions))
    )
    return session.scalar(stmt)


def list_paper_sections(session: Session, paper_id: int) -> list[PaperSection]:
    paper = get_paper(session, paper_id)
    if paper is None:
        raise ValueError(f"Unknown paper: {paper_id}")
    sections: list[PaperSection] = []
    for version in paper.versions:
        sections.extend(version.sections)
    return sorted(sections, key=lambda section: (section.paper_version_id, section.order_index))


def list_paper_citations(session: Session, paper_id: int) -> list[Citation]:
    paper = get_paper(session, paper_id)
    if paper is None:
        raise ValueError(f"Unknown paper: {paper_id}")
    citations: list[Citation] = []
    for version in paper.versions:
        citations.extend(version.citations)
    return citations


def search_papers(session: Session, query: str, limit: int = 20) -> list[Paper]:
    needle = f"%{query.strip().lower()}%"
    stmt = (
        select(Paper)
        .where(
            or_(
                func.lower(Paper.canonical_title).like(needle),
                func.lower(func.coalesce(Paper.abstract, "")).like(needle),
                func.lower(func.coalesce(Paper.venue, "")).like(needle),
            )
        )
        .order_by(Paper.citation_count.desc(), Paper.canonical_title.asc())
        .limit(limit)
    )
    return list(session.scalars(stmt).all())


def get_paper_by_identifiers(session: Session, *, openalex_id: str | None = None, doi: str | None = None, arxiv_id: str | None = None) -> Paper | None:
    if openalex_id:
        paper = session.scalar(select(Paper).where(Paper.openalex_id == openalex_id))
        if paper:
            return paper
    if doi:
        paper = session.scalar(select(Paper).where(Paper.doi == doi))
        if paper:
            return paper
    if arxiv_id:
        paper = session.scalar(select(Paper).where(Paper.arxiv_id == arxiv_id))
        if paper:
            return paper
    return None


def upsert_paper_from_openalex(session: Session, work: OpenAlexWork) -> UpsertResult:
    normalized_doi = normalize_doi(work.doi)
    paper = get_paper_by_identifiers(session, openalex_id=work.openalex_id, doi=normalized_doi, arxiv_id=work.arxiv_id)
    created = paper is None
    if paper is None:
        paper = Paper(canonical_title=work.title)
        session.add(paper)
        session.flush()

    paper.canonical_title = work.title
    paper.openalex_id = work.openalex_id or paper.openalex_id
    paper.doi = normalized_doi or paper.doi
    paper.arxiv_id = work.arxiv_id or paper.arxiv_id
    paper.publication_year = work.publication_year
    paper.venue = work.venue
    paper.abstract = work.abstract
    paper.language = work.language
    paper.is_open_access = work.is_open_access
    paper.citation_count = work.citation_count
    paper.primary_source = work.primary_source

    version = session.scalar(
        select(PaperVersion).where(
            PaperVersion.paper_id == paper.id,
            PaperVersion.source_url == work.source_url,
            PaperVersion.pdf_url == work.pdf_url,
        )
    )
    version_created = version is None
    if version is None:
        version = PaperVersion(
            paper_id=paper.id,
            version_type="source",
            source_url=work.source_url,
            pdf_url=work.pdf_url,
        )
        session.add(version)
        session.flush()
    else:
        version.source_url = work.source_url
        version.pdf_url = work.pdf_url

    return UpsertResult(paper=paper, created=created, version=version, version_created=version_created)


def persist_parse_result(session: Session, version: PaperVersion, result: ParseResult, parser_provider: str) -> ParsePersistenceResult:
    version.raw_tei_xml = result.raw_tei_xml
    version.parse_status = f"parsed:{parser_provider}"
    version.parse_error = None

    for existing in list(version.sections):
        session.delete(existing)
    for existing in list(version.citations):
        session.delete(existing)
    session.flush()

    sections_created = 0
    chunks_created = 0
    citations_created = 0
    contexts_created = 0
    edges_created = 0

    for section_index, parsed_section in enumerate(result.sections):
        section = PaperSection(
            paper_version_id=version.id,
            section_type=parsed_section.section_type,
            heading=parsed_section.heading,
            order_index=section_index,
            page_start=parsed_section.page_start,
            page_end=parsed_section.page_end,
            text="\n\n".join(parsed_section.paragraphs) if parsed_section.paragraphs else None,
        )
        session.add(section)
        session.flush()
        sections_created += 1

        for chunk_index, paragraph in enumerate(parsed_section.paragraphs):
            chunk = PaperChunk(
                section_id=section.id,
                text=paragraph,
                order_index=chunk_index,
                page_start=parsed_section.page_start,
                page_end=parsed_section.page_end,
            )
            session.add(chunk)
            chunks_created += 1

    session.flush()

    for parsed_citation in result.citations:
        target_paper = get_paper_by_identifiers(
            session,
            openalex_id=parsed_citation.target_openalex_id,
            doi=normalize_doi(parsed_citation.target_doi),
        )
        citation = Citation(
            source_paper_version_id=version.id,
            target_paper_id=target_paper.id if target_paper else None,
            raw_reference=parsed_citation.raw_reference,
            citation_key=parsed_citation.citation_key,
            resolution_confidence=parsed_citation.resolution_confidence,
        )
        session.add(citation)
        session.flush()
        citations_created += 1

        for context_text in parsed_citation.contexts:
            context = CitationContext(
                citation_id=citation.id,
                context_text=context_text,
                context_type=_classify_context_text(context_text),
            )
            session.add(context)
            contexts_created += 1

    edges_created = _rebuild_citation_edges_for_paper(session, version.paper_id)

    return ParsePersistenceResult(
        sections_created=sections_created,
        chunks_created=chunks_created,
        citations_created=citations_created,
        contexts_created=contexts_created,
        edges_created=edges_created,
    )


def _rebuild_citation_edges_for_paper(session: Session, paper_id: int) -> int:
    session.execute(
        delete(PaperEdge).where(
            PaperEdge.src_paper_id == paper_id,
            PaperEdge.source == "citation",
            PaperEdge.edge_type == "cites",
        )
    )
    stmt = (
        select(Citation.target_paper_id, func.max(Citation.resolution_confidence))
        .join(PaperVersion, PaperVersion.id == Citation.source_paper_version_id)
        .where(
            PaperVersion.paper_id == paper_id,
            Citation.target_paper_id.is_not(None),
        )
        .group_by(Citation.target_paper_id)
    )
    created = 0
    for target_paper_id, max_confidence in session.execute(stmt).all():
        if target_paper_id is None:
            continue
        session.add(
            PaperEdge(
                src_paper_id=paper_id,
                dst_paper_id=target_paper_id,
                edge_type="cites",
                confidence=max(float(max_confidence or 0.0), 0.5),
                source="citation",
            )
        )
        created += 1
    session.flush()
    return created


def list_graph_neighbors(session: Session, paper_id: int) -> list[tuple[PaperEdge, Paper]]:
    stmt = (
        select(PaperEdge, Paper)
        .join(Paper, Paper.id == PaperEdge.dst_paper_id)
        .where(PaperEdge.src_paper_id == paper_id)
        .order_by(Paper.canonical_title.asc())
    )
    return list(session.execute(stmt).all())


def build_graph_explanations(session: Session, paper_id: int) -> dict:
    paper = get_paper(session, paper_id)
    if paper is None:
        raise ValueError(f"Unknown paper: {paper_id}")

    grouped: dict[int | None, dict] = {}
    citations = list_paper_citations(session, paper_id)

    for citation in citations:
        key = citation.target_paper_id
        if key not in grouped:
            grouped[key] = {
                "target_paper_id": key,
                "target_paper_title": citation.target_paper.canonical_title if citation.target_paper else None,
                "edge_types": set(),
                "raw_references": [],
                "context_texts": [],
                "context_types": set(),
            }

        item = grouped[key]
        item["raw_references"].append(citation.raw_reference)
        item["context_texts"].extend(context.context_text for context in citation.contexts)
        item["context_types"].update(context.context_type for context in citation.contexts)
        item["edge_types"].add("cites")

        for edge in paper.outgoing_edges:
            if edge.dst_paper_id == citation.target_paper_id:
                item["edge_types"].add(edge.edge_type)

    explanations = [
        {
            "target_paper_id": item["target_paper_id"],
            "target_paper_title": item["target_paper_title"],
            "edge_types": sorted(item["edge_types"]),
            "raw_references": sorted(dict.fromkeys(item["raw_references"])),
            "context_texts": sorted(dict.fromkeys(item["context_texts"])),
            "context_types": sorted(item["context_types"]),
        }
        for item in grouped.values()
    ]
    explanations.sort(key=lambda entry: entry["target_paper_title"] or "")

    return {
        "paper_id": paper_id,
        "explanations": explanations,
    }


def _normalize_entity_name(name: str) -> str:
    return " ".join(name.strip().split())


def _get_or_create_named_entity(session: Session, model: type[Method | Dataset | Metric], name: str):
    normalized_name = _normalize_entity_name(name)
    entity = session.scalar(select(model).where(model.name == normalized_name))
    if entity:
        return entity
    entity = model(name=normalized_name)
    session.add(entity)
    session.flush()
    return entity


def attach_semantic_enrichment(
    session: Session,
    paper_id: int,
    *,
    methods: list[str],
    datasets: list[str],
    metrics: list[str],
) -> SemanticEnrichmentResult:
    paper = get_paper(session, paper_id)
    if paper is None:
        raise ValueError(f"Unknown paper: {paper_id}")

    methods_attached = 0
    datasets_attached = 0
    metrics_attached = 0

    existing_method_ids = {link.method_id for link in paper.method_links}
    for method_name in methods:
        method = _get_or_create_named_entity(session, Method, method_name)
        if method.id not in existing_method_ids:
            session.add(PaperMethodLink(paper_id=paper.id, method_id=method.id))
            existing_method_ids.add(method.id)
            methods_attached += 1

    existing_dataset_ids = {link.dataset_id for link in paper.dataset_links}
    for dataset_name in datasets:
        dataset = _get_or_create_named_entity(session, Dataset, dataset_name)
        if dataset.id not in existing_dataset_ids:
            session.add(PaperDatasetLink(paper_id=paper.id, dataset_id=dataset.id))
            existing_dataset_ids.add(dataset.id)
            datasets_attached += 1

    existing_metric_ids = {link.metric_id for link in paper.metric_links}
    for metric_name in metrics:
        metric = _get_or_create_named_entity(session, Metric, metric_name)
        if metric.id not in existing_metric_ids:
            session.add(PaperMetricLink(paper_id=paper.id, metric_id=metric.id))
            existing_metric_ids.add(metric.id)
            metrics_attached += 1

    session.flush()
    return SemanticEnrichmentResult(
        paper_id=paper.id,
        methods_attached=methods_attached,
        datasets_attached=datasets_attached,
        metrics_attached=metrics_attached,
    )


def auto_attach_semantic_enrichment(session: Session, paper_id: int) -> AutoSemanticEnrichmentResult:
    paper = get_paper(session, paper_id)
    if paper is None:
        raise ValueError(f"Unknown paper: {paper_id}")

    corpus = _build_paper_text_corpus(paper)
    extracted_methods = _extract_named_entities(corpus, METHOD_PATTERNS)
    extracted_datasets = _extract_named_entities(corpus, DATASET_PATTERNS)
    extracted_metrics = _extract_named_entities(corpus, METRIC_PATTERNS)

    result = attach_semantic_enrichment(
        session,
        paper_id,
        methods=extracted_methods,
        datasets=extracted_datasets,
        metrics=extracted_metrics,
    )
    return AutoSemanticEnrichmentResult(
        paper_id=result.paper_id,
        methods_attached=result.methods_attached,
        datasets_attached=result.datasets_attached,
        metrics_attached=result.metrics_attached,
        extracted_methods=extracted_methods,
        extracted_datasets=extracted_datasets,
        extracted_metrics=extracted_metrics,
    )


def build_evidence_pack(session: Session, paper_id: int) -> dict:
    paper = get_paper(session, paper_id)
    if paper is None:
        raise ValueError(f"Unknown paper: {paper_id}")

    neighbors = list_graph_neighbors(session, paper_id)
    result_stats = build_paper_result_stats(paper)
    return {
        "paper_id": paper.id,
        "canonical_title": paper.canonical_title,
        "methods": [{"id": link.method.id, "name": link.method.name} for link in paper.method_links],
        "datasets": [{"id": link.dataset.id, "name": link.dataset.name} for link in paper.dataset_links],
        "metrics": [{"id": link.metric.id, "name": link.metric.name} for link in paper.metric_links],
        "experiment_results": [
            {
                "id": result.id,
                "run_id": result.run_id,
                "paper_id": result.paper_id,
                "method_name": result.method.name if result.method else None,
                "dataset_name": result.dataset.name if result.dataset else None,
                "metric_name": result.metric.name if result.metric else None,
                "value": result.value,
                "source": result.source,
                "notes": result.notes,
            }
            for result in paper.experiment_results
        ],
        "result_stats": result_stats,
        "neighbors": [
            {
                "paper_id": neighbor.id,
                "title": neighbor.canonical_title,
                "edge_type": edge.edge_type,
                "confidence": edge.confidence,
            }
            for edge, neighbor in neighbors
        ],
    }


def build_topic_landscape(session: Session, query: str, limit: int = 20) -> dict:
    papers = search_papers(session, query, limit=limit)
    paper_ids = [paper.id for paper in papers]

    methods = sorted(
        {
            link.method.name
            for paper in papers
            for link in paper.method_links
        }
    )
    datasets = sorted(
        {
            link.dataset.name
            for paper in papers
            for link in paper.dataset_links
        }
    )
    metrics = sorted(
        {
            link.metric.name
            for paper in papers
            for link in paper.metric_links
        }
    )

    edge_type_counts: dict[str, int] = {}
    if paper_ids:
        stmt = select(PaperEdge).where(PaperEdge.src_paper_id.in_(paper_ids))
        for edge in session.scalars(stmt).all():
            edge_type_counts[edge.edge_type] = edge_type_counts.get(edge.edge_type, 0) + 1

    result_count = sum(len(paper.experiment_results) for paper in papers)
    papers_with_results = sum(1 for paper in papers if paper.experiment_results)
    top_result_papers = [
        {
            "paper_id": paper.id,
            "canonical_title": paper.canonical_title,
            "result_count": len(paper.experiment_results),
        }
        for paper in sorted(papers, key=lambda item: len(item.experiment_results), reverse=True)
        if paper.experiment_results
    ][:5]

    return {
        "query": query,
        "paper_count": len(papers),
        "papers": [
            {
                "id": paper.id,
                "canonical_title": paper.canonical_title,
                "doi": paper.doi,
                "openalex_id": paper.openalex_id,
                "publication_year": paper.publication_year,
                "venue": paper.venue,
                "citation_count": paper.citation_count,
            }
            for paper in papers
        ],
        "methods": methods,
        "datasets": datasets,
        "metrics": metrics,
        "edge_type_counts": edge_type_counts,
        "result_count": result_count,
        "papers_with_results": papers_with_results,
        "top_result_papers": top_result_papers,
    }


def build_paper_result_stats(paper: Paper) -> dict:
    method_names = sorted({result.method.name for result in paper.experiment_results if result.method})
    dataset_names = sorted({result.dataset.name for result in paper.experiment_results if result.dataset})
    metric_names = sorted({result.metric.name for result in paper.experiment_results if result.metric})
    return {
        "result_count": len(paper.experiment_results),
        "method_count": len(method_names),
        "dataset_count": len(dataset_names),
        "metric_count": len(metric_names),
        "metric_names": metric_names,
    }


def infer_semantic_edges(session: Session, paper_id: int) -> SemanticEdgeInferenceResult:
    paper = get_paper(session, paper_id)
    if paper is None:
        raise ValueError(f"Unknown paper: {paper_id}")

    created = 0
    existing_pairs = {
        (edge.dst_paper_id, edge.edge_type)
        for edge in paper.outgoing_edges
        if edge.edge_type != "cites"
    }
    citations = [
        citation
        for version in paper.versions
        for citation in version.citations
    ]
    for citation in citations:
        if citation.target_paper_id is None:
            continue
        for context in citation.contexts:
            inferred_type = _infer_edge_type_from_text(context.context_text)
            edge_key = (citation.target_paper_id, inferred_type) if inferred_type else None
            if inferred_type and edge_key not in existing_pairs:
                session.add(
                    PaperEdge(
                        src_paper_id=paper.id,
                        dst_paper_id=citation.target_paper_id,
                        edge_type=inferred_type,
                        confidence=0.7,
                        evidence_chunk_id=context.chunk_id,
                        source="semantic_inference",
                    )
                )
                existing_pairs.add(edge_key)
                created += 1

    session.flush()
    return SemanticEdgeInferenceResult(paper_id=paper.id, edges_created=created)


def _infer_edge_type_from_text(text: str) -> str | None:
    lowered = text.lower()
    if "compare" in lowered:
        return "compares"
    if "extend" in lowered or "build on" in lowered:
        return "extends"
    if "contradict" in lowered or "unlike" in lowered:
        return "contradicts"
    return None


def _classify_context_text(text: str) -> str:
    lowered = text.lower()
    if "compare" in lowered or "baseline" in lowered:
        return "comparison"
    if "extend" in lowered or "build on" in lowered:
        return "extension"
    if "contradict" in lowered or "unlike" in lowered or "however" in lowered:
        return "critique"
    return "background"


def _build_paper_text_corpus(paper: Paper) -> str:
    chunks: list[str] = []
    if paper.abstract:
        chunks.append(paper.abstract)
    for version in paper.versions:
        for section in version.sections:
            if section.heading:
                chunks.append(section.heading)
            if section.text:
                chunks.append(section.text)
            for chunk in section.chunks:
                chunks.append(chunk.text)
        for citation in version.citations:
            chunks.append(citation.raw_reference)
            for context in citation.contexts:
                chunks.append(context.context_text)
    return "\n".join(chunk for chunk in chunks if chunk)


def _extract_named_entities(text: str, patterns: list[tuple[str, re.Pattern[str]]]) -> list[str]:
    found: list[str] = []
    for canonical, pattern in patterns:
        if pattern.search(text):
            found.append(canonical)
    return found


def _canonicalize_known_entity(value: str, patterns: list[tuple[str, re.Pattern[str]]]) -> str:
    for canonical, pattern in patterns:
        if pattern.search(value):
            return canonical
    return value


def _extract_result_matches(text: str) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    for pattern in RESULT_PATTERNS:
        for match in pattern.finditer(text):
            matches.append(
                {
                    "method_name": _canonicalize_known_entity(match.group("method"), METHOD_PATTERNS),
                    "dataset_name": _canonicalize_known_entity(match.group("dataset"), DATASET_PATTERNS),
                    "metric_name": _canonicalize_known_entity(match.group("metric"), METRIC_PATTERNS),
                    "value": match.group("value"),
                }
            )
    return matches


def create_evidence_snapshot(session: Session, paper_id: int, *, topic: str | None = None) -> EvidenceSnapshot:
    payload = build_evidence_pack(session, paper_id)
    snapshot = EvidenceSnapshot(paper_id=paper_id, topic=topic, payload_json=json.dumps(payload, sort_keys=True))
    session.add(snapshot)
    session.flush()
    return snapshot


def get_snapshot(session: Session, snapshot_id: int) -> EvidenceSnapshot | None:
    return session.get(EvidenceSnapshot, snapshot_id)


def get_run(session: Session, run_id: int) -> ResearchRun | None:
    return session.get(ResearchRun, run_id)


def list_runs(session: Session) -> list[ResearchRun]:
    stmt = select(ResearchRun).order_by(ResearchRun.time_created.desc())
    return list(session.scalars(stmt).all())


def add_run_event(
    session: Session,
    run_id: int,
    *,
    event_type: str,
    message: str,
    source: str = "system",
    status: str = "info",
    payload: dict | list | None = None,
) -> ResearchRunEvent:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise ValueError(f"Unknown run: {run_id}")
    event = ResearchRunEvent(
        run_id=run_id,
        event_type=event_type,
        status=status,
        source=source,
        message=message,
        payload_json=_json_dumps(payload),
    )
    session.add(event)
    session.flush()
    return event


def list_run_events(session: Session, run_id: int) -> list[ResearchRunEvent]:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise ValueError(f"Unknown run: {run_id}")
    stmt = (
        select(ResearchRunEvent)
        .where(ResearchRunEvent.run_id == run_id)
        .order_by(ResearchRunEvent.time_created.asc(), ResearchRunEvent.id.asc())
    )
    return list(session.scalars(stmt).all())


def get_system_counts(session: Session) -> dict:
    paper_count = session.scalar(select(func.count()).select_from(Paper)) or 0
    run_count = session.scalar(select(func.count()).select_from(ResearchRun)) or 0
    return {
        "paper_count": int(paper_count),
        "run_count": int(run_count),
    }


def create_research_run(session: Session, *, snapshot_id: int, branch_name: str | None = None) -> ResearchRun:
    snapshot = get_snapshot(session, snapshot_id)
    if snapshot is None:
        raise ValueError(f"Unknown snapshot: {snapshot_id}")
    run = ResearchRun(
        snapshot_id=snapshot.id,
        branch_name=branch_name or f"run-{snapshot.id}",
        worktree_path=None,
        status="created",
    )
    session.add(run)
    session.flush()
    add_run_event(
        session,
        run.id,
        event_type="run.created",
        source="workflow",
        message=f"Research run {run.id} created from snapshot {snapshot.id}.",
        payload={"snapshot_id": snapshot.id, "branch_name": run.branch_name},
    )
    return run


def _link_named_entities_to_paper(
    session: Session,
    paper: Paper,
    *,
    method: Method | None = None,
    dataset: Dataset | None = None,
    metric: Metric | None = None,
) -> None:
    if method and method.id not in {link.method_id for link in paper.method_links}:
        session.add(PaperMethodLink(paper_id=paper.id, method_id=method.id))
    if dataset and dataset.id not in {link.dataset_id for link in paper.dataset_links}:
        session.add(PaperDatasetLink(paper_id=paper.id, dataset_id=dataset.id))
    if metric and metric.id not in {link.metric_id for link in paper.metric_links}:
        session.add(PaperMetricLink(paper_id=paper.id, metric_id=metric.id))


def add_experiment_result(
    session: Session,
    *,
    run_id: int,
    paper_id: int,
    method_name: str | None,
    dataset_name: str | None,
    metric_name: str | None,
    value: str,
    notes: str | None,
    source: str = "manual",
) -> ExperimentResult:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise ValueError(f"Unknown run: {run_id}")
    paper = get_paper(session, paper_id)
    if paper is None:
        raise ValueError(f"Unknown paper: {paper_id}")

    method = _get_or_create_named_entity(session, Method, method_name) if method_name else None
    dataset = _get_or_create_named_entity(session, Dataset, dataset_name) if dataset_name else None
    metric = _get_or_create_named_entity(session, Metric, metric_name) if metric_name else None
    _link_named_entities_to_paper(session, paper, method=method, dataset=dataset, metric=metric)

    result = ExperimentResult(
        run_id=run.id,
        paper_id=paper.id,
        method_id=method.id if method else None,
        dataset_id=dataset.id if dataset else None,
        metric_id=metric.id if metric else None,
        value=value,
        source=source,
        notes=notes,
    )
    session.add(result)
    session.flush()
    add_run_event(
        session,
        run.id,
        event_type="experiment_result.recorded",
        source=source,
        message=f"Recorded experiment result for paper {paper.id}.",
        payload={
            "paper_id": paper.id,
            "method_name": method.name if method else None,
            "dataset_name": dataset.name if dataset else None,
            "metric_name": metric.name if metric else None,
            "value": value,
        },
    )
    return result


def list_hypotheses(session: Session, run_id: int) -> list[ResearchHypothesis]:
    stmt = select(ResearchHypothesis).where(ResearchHypothesis.run_id == run_id).order_by(ResearchHypothesis.time_created.asc())
    return list(session.scalars(stmt).all())


def list_experiment_plans(session: Session, run_id: int) -> list[ExperimentPlan]:
    stmt = select(ExperimentPlan).where(ExperimentPlan.run_id == run_id).order_by(ExperimentPlan.time_created.asc())
    return list(session.scalars(stmt).all())


def list_experiment_tasks(session: Session, run_id: int) -> list[ExperimentTask]:
    stmt = select(ExperimentTask).where(ExperimentTask.run_id == run_id).order_by(ExperimentTask.time_created.asc())
    return list(session.scalars(stmt).all())


def list_iterations(session: Session, run_id: int) -> list[ResearchIteration]:
    stmt = select(ResearchIteration).where(ResearchIteration.run_id == run_id).order_by(ResearchIteration.iteration_index.asc())
    return list(session.scalars(stmt).all())


def auto_generate_hypotheses(session: Session, *, run_id: int, paper_id: int) -> list[ResearchHypothesis]:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise ValueError(f"Unknown run: {run_id}")
    paper = get_paper(session, paper_id)
    if paper is None:
        raise ValueError(f"Unknown paper: {paper_id}")

    methods = [link.method.name for link in paper.method_links]
    datasets = [link.dataset.name for link in paper.dataset_links]
    metrics = [link.metric.name for link in paper.metric_links]
    statements: list[tuple[str, str]] = []

    if methods and datasets and metrics:
        for method in methods[:2]:
            for dataset in datasets[:1]:
                for metric in metrics[:1]:
                    statements.append(
                        (
                            f"{method} should yield measurable gains on {dataset} when evaluated with {metric}.",
                            f"Derived from parsed evidence and extracted entities for paper '{paper.canonical_title}'.",
                        )
                    )
    elif methods:
        for method in methods[:2]:
            statements.append(
                (
                    f"{method} is central enough in '{paper.canonical_title}' to warrant follow-up validation.",
                    "Derived from extracted method mentions in the parsed paper text.",
                )
            )
    else:
        statements.append(
            (
                f"'{paper.canonical_title}' contains enough structured evidence to support a follow-up comparison study.",
                "Fallback heuristic when no richer semantic entities are available.",
            )
        )

    created: list[ResearchHypothesis] = []
    existing = {hyp.statement for hyp in run.hypotheses}
    for statement, rationale in statements:
        if statement in existing:
            continue
        hypothesis = ResearchHypothesis(run_id=run.id, paper_id=paper.id, statement=statement, rationale=rationale)
        session.add(hypothesis)
        session.flush()
        created.append(hypothesis)
        existing.add(statement)
    if created:
        add_run_event(
            session,
            run.id,
            event_type="hypotheses.generated",
            source="autonomous_loop",
            message=f"Generated {len(created)} hypotheses for paper {paper.id}.",
            payload={"paper_id": paper.id, "count": len(created)},
        )
    return created


def auto_generate_experiment_plans(session: Session, *, run_id: int, paper_id: int) -> list[ExperimentPlan]:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise ValueError(f"Unknown run: {run_id}")
    paper = get_paper(session, paper_id)
    if paper is None:
        raise ValueError(f"Unknown paper: {paper_id}")

    methods = [link.method.name for link in paper.method_links]
    datasets = [link.dataset.name for link in paper.dataset_links]
    metrics = [link.metric.name for link in paper.metric_links]
    steps = [
        f"Collect evidence for paper '{paper.canonical_title}'.",
        f"Prepare comparison setup for dataset {datasets[0] if datasets else 'the target dataset'}.",
        f"Evaluate using metric {metrics[0] if metrics else 'the target metric'}.",
        "Record result and write it back to the knowledge layer.",
    ]
    title = f"Validate {methods[0] if methods else 'the extracted approach'} on {datasets[0] if datasets else 'the target dataset'}"

    existing_titles = {plan.title for plan in run.experiment_plans}
    if title in existing_titles:
        return []

    plan = ExperimentPlan(
        run_id=run.id,
        paper_id=paper.id,
        title=title,
        steps_json=json.dumps(steps, sort_keys=False),
    )
    session.add(plan)
    session.flush()
    add_run_event(
        session,
        run.id,
        event_type="experiment_plans.generated",
        source="autonomous_loop",
        message=f"Generated experiment plan '{plan.title}'.",
        payload={"paper_id": paper.id, "plan_id": plan.id, "title": plan.title},
    )
    return [plan]


def auto_generate_experiment_tasks(session: Session, *, run_id: int) -> list[ExperimentTask]:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise ValueError(f"Unknown run: {run_id}")

    created: list[ExperimentTask] = []
    existing_titles = {task.title for task in run.experiment_tasks}
    plans = list_experiment_plans(session, run_id)
    for plan in plans:
        paper = get_paper(session, plan.paper_id)
        if paper is None:
            continue
        methods = [link.method.name for link in paper.method_links]
        datasets = [link.dataset.name for link in paper.dataset_links]
        metrics = [link.metric.name for link in paper.metric_links]
        base_config = {
            "method": methods[0] if methods else None,
            "dataset": datasets[0] if datasets else None,
            "metric": metrics[0] if metrics else None,
        }
        for task_type in ("benchmark", "ablation", "comparison"):
            title = f"{plan.title} [{task_type}]"
            if title in existing_titles:
                continue
            config = dict(base_config)
            config["task_type"] = task_type
            task = ExperimentTask(
                run_id=run.id,
                plan_id=plan.id,
                paper_id=plan.paper_id,
                title=title,
                task_type=task_type,
                config_json=json.dumps(config, sort_keys=True),
                status="pending",
            )
            session.add(task)
            session.flush()
            created.append(task)
            existing_titles.add(title)
    if created:
        add_run_event(
            session,
            run.id,
            event_type="experiment_tasks.generated",
            source="autonomous_loop",
            message=f"Generated {len(created)} experiment tasks.",
            payload={"count": len(created), "task_types": sorted({task.task_type for task in created})},
        )
    return created


BENCHMARK_REGISTRY: dict[tuple[str, str, str], str] = {
    ("Transformer", "WMT14", "BLEU"): "28.4",
    ("BERT", "GLUE", "Accuracy"): "84.6",
    ("RoBERTa", "GLUE", "Accuracy"): "88.5",
    ("RAG", "PubMed", "F1"): "0.91",
}

KEEP_THRESHOLDS: dict[str, float] = {
    "BLEU": 25.0,
    "Accuracy": 80.0,
    "F1": 0.80,
    "ROUGE": 0.35,
    "MRR": 0.30,
}


def auto_add_experiment_results(session: Session, *, run_id: int, paper_id: int) -> list[ExperimentResult]:
    paper = get_paper(session, paper_id)
    if paper is None:
        raise ValueError(f"Unknown paper: {paper_id}")

    corpus = _build_paper_text_corpus(paper)
    created: list[ExperimentResult] = []
    seen: set[tuple[str | None, str | None, str | None, str]] = set()
    for match in _extract_result_matches(corpus):
        key = (match["method_name"], match["dataset_name"], match["metric_name"], match["value"])
        if key in seen:
            continue
        seen.add(key)
        created.append(
            add_experiment_result(
                session,
                run_id=run_id,
                paper_id=paper_id,
                method_name=match["method_name"],
                dataset_name=match["dataset_name"],
                metric_name=match["metric_name"],
                value=match["value"],
                notes="auto-extracted from parsed text",
                source="auto_extract",
            )
        )
    if created:
        add_run_event(
            session,
            run_id,
            event_type="experiment_results.auto_extracted",
            source="auto_extract",
            message=f"Auto-extracted {len(created)} experiment results for paper {paper_id}.",
            payload={"paper_id": paper_id, "count": len(created)},
        )
    return created


def list_experiment_results(session: Session, paper_id: int) -> list[ExperimentResult]:
    stmt = (
        select(ExperimentResult)
        .where(ExperimentResult.paper_id == paper_id)
        .order_by(ExperimentResult.time_created.asc())
    )
    return list(session.scalars(stmt).all())


def update_research_run_result(
    session: Session,
    run_id: int,
    *,
    status: str,
    result_summary: str | None,
    result_payload_json: str | None,
) -> ResearchRun:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise ValueError(f"Unknown run: {run_id}")
    run.status = status
    run.result_summary = result_summary
    run.result_payload_json = result_payload_json
    session.flush()
    add_run_event(
        session,
        run.id,
        event_type="run.status_updated",
        source="workflow",
        status="info" if status == "completed" else status,
        message=f"Run status updated to '{status}'.",
        payload={"status": status, "result_summary": result_summary},
    )
    return run


def list_run_results(session: Session, run_id: int) -> list[ExperimentResult]:
    stmt = select(ExperimentResult).where(ExperimentResult.run_id == run_id).order_by(ExperimentResult.time_created.asc())
    return list(session.scalars(stmt).all())


def build_research_report(session: Session, run_id: int) -> tuple[str, str]:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise ValueError(f"Unknown run: {run_id}")
    snapshot = run.snapshot
    if snapshot is None:
        raise ValueError(f"Run {run_id} has no snapshot")
    paper = get_paper(session, snapshot.paper_id)
    if paper is None:
        raise ValueError(f"Snapshot {snapshot.id} references unknown paper")

    hypotheses = list_hypotheses(session, run_id)
    plans = list_experiment_plans(session, run_id)
    results = list_run_results(session, run_id)
    explanations = build_graph_explanations(session, paper.id)["explanations"]
    result_table = _build_results_table(results)
    result_chart_path = _write_results_figure(run.id, results)

    title = f"Autonomous Research Report: {snapshot.topic or paper.canonical_title}"
    lines = [
        f"# {title}",
        "",
        "## Overview",
        run.result_summary or "No summary available.",
        "",
        "## Lead Paper",
        f"- Title: {paper.canonical_title}",
        f"- Year: {paper.publication_year}",
        f"- Venue: {paper.venue}",
        "",
        "## Hypotheses",
    ]
    if hypotheses:
        for idx, hypothesis in enumerate(hypotheses, start=1):
            lines.append(f"{idx}. {hypothesis.statement}")
            if hypothesis.rationale:
                lines.append(f"   - Rationale: {hypothesis.rationale}")
    else:
        lines.append("- None")

    lines.extend(["", "## Experiment Plans"])
    if plans:
        for idx, plan in enumerate(plans, start=1):
            lines.append(f"{idx}. {plan.title}")
            for step in json.loads(plan.steps_json):
                lines.append(f"   - {step}")
    else:
        lines.append("- None")

    lines.extend(["", "## Experiment Results"])
    if results:
        for result in results:
            lines.append(
                f"- Paper {result.paper_id}: {result.method.name if result.method else 'Unknown method'} / "
                f"{result.dataset.name if result.dataset else 'Unknown dataset'} / "
                f"{result.metric.name if result.metric else 'Unknown metric'} = {result.value}"
            )
            if result.notes:
                lines.append(f"  - Notes: {result.notes}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Result Table",
            result_table,
            "",
            "## Figures",
            f"![Experiment Results]({result_chart_path})",
        ]
    )

    lines.extend(["", "## Relationship Explanations"])
    if explanations:
        for item in explanations:
            lines.append(f"- Target: {item['target_paper_title'] or item['target_paper_id']}")
            lines.append(f"  - Edge types: {', '.join(item['edge_types'])}")
            if item["context_types"]:
                lines.append(f"  - Context types: {', '.join(item['context_types'])}")
            if item["context_texts"]:
                lines.append(f"  - Example context: {item['context_texts'][0]}")
    else:
        lines.append("- None")

    markdown = "\n".join(lines)
    run.report_title = title
    run.report_markdown = markdown
    run.report_figure_path = result_chart_path
    session.flush()
    add_run_event(
        session,
        run.id,
        event_type="report.generated",
        source="writer",
        message=f"Generated research report '{title}'.",
        payload={"title": title, "figure_path": result_chart_path},
    )
    return title, markdown


def build_paper_draft(session: Session, run_id: int) -> tuple[str, str]:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise ValueError(f"Unknown run: {run_id}")
    snapshot = run.snapshot
    if snapshot is None:
        raise ValueError(f"Run {run_id} has no snapshot")
    paper = get_paper(session, snapshot.paper_id)
    if paper is None:
        raise ValueError(f"Snapshot {snapshot.id} references unknown paper")

    hypotheses = list_hypotheses(session, run_id)
    plans = list_experiment_plans(session, run_id)
    iterations = list_iterations(session, run_id)
    results = list_run_results(session, run_id)
    explanations = build_graph_explanations(session, paper.id)["explanations"]
    result_table = _build_results_table(results)
    result_chart_path = _write_results_figure(run.id, results)

    title = f"Paper Draft: {snapshot.topic or paper.canonical_title}"
    references = sorted({item["target_paper_title"] for item in explanations if item["target_paper_title"]})
    methods = sorted({result.method.name for result in results if result.method})
    datasets = sorted({result.dataset.name for result in results if result.dataset})
    metrics = sorted({result.metric.name for result in results if result.metric})

    lines = [
        f"# {title}",
        "",
        "## Abstract",
        f"This draft summarizes an automated research loop over the topic '{snapshot.topic or paper.canonical_title}'. "
        f"The system ingested papers, parsed structured evidence, generated hypotheses and experiment plans, "
        f"executed deterministic local evaluations, and recorded results in a shared knowledge layer.",
        "",
        "## Introduction",
        f"This work investigates the topic '{snapshot.topic or paper.canonical_title}' using an automated literature-driven loop. "
        f"The goal is to turn scholarly evidence into actionable hypotheses, experiment plans, and reusable structured outputs.",
        "",
        "## Related Work",
        *( [f"- {ref}" for ref in references] if references else ["- No related-work references captured."] ),
        "",
        "## Hypotheses",
        *( [f"- {hyp.statement}" for hyp in hypotheses] if hypotheses else ["- No hypotheses generated."] ),
        "",
        "## Method",
        f"The pipeline used parsed papers, graph explanations, semantic entity extraction, and deterministic evaluation over "
        f"methods={methods or ['N/A']}, datasets={datasets or ['N/A']}, metrics={metrics or ['N/A']}.",
        "",
        "## Experiment Setup",
        *( [f"- {plan.title}" for plan in plans] if plans else ["- No experiment plans generated."] ),
        "",
        "## Results",
        *( [
            f"- {result.method.name if result.method else 'Unknown method'} on {result.dataset.name if result.dataset else 'Unknown dataset'} "
            f"using {result.metric.name if result.metric else 'Unknown metric'} = {result.value}"
            for result in results
        ] if results else ["- No experiment results recorded."] ),
        "",
        "### Result Table",
        result_table,
        "",
        "### Figures",
        f"![Experiment Results]({result_chart_path})",
        "",
        "## Discussion",
        f"The loop produced {len(hypotheses)} hypotheses, {len(plans)} experiment plans, "
        f"{len(iterations)} executed iterations, and {len(results)} stored experiment results.",
        "",
        "## Conclusion",
        "The automated pipeline can already produce a structured draft from literature ingestion through experiment/result synthesis. "
        "Future work should replace deterministic local execution with real benchmark and training backends.",
        "",
        "## References",
        *( [f"- {ref}" for ref in references] if references else ["- No references available."] ),
    ]

    markdown = "\n".join(lines)
    run.paper_draft_title = title
    run.paper_draft_markdown = markdown
    session.flush()
    add_run_event(
        session,
        run.id,
        event_type="paper_draft.generated",
        source="writer",
        message=f"Generated paper draft '{title}'.",
        payload={"title": title, "figure_path": result_chart_path},
    )
    return title, markdown


def write_run_artifact_bundle(session: Session, run_id: int) -> dict:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise ValueError(f"Unknown run: {run_id}")

    artifacts_root = Path(os.getenv("FARS_ARTIFACTS_ROOT", ".artifacts"))
    artifact_dir = artifacts_root / "runs" / f"run-{run_id}"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    run.artifact_dir = str(artifact_dir)
    session.flush()
    add_run_event(
        session,
        run.id,
        event_type="artifact_bundle.generated",
        source="artifact_writer",
        message=f"Generating artifact bundle at '{artifact_dir}'.",
        payload={"artifact_dir": str(artifact_dir)},
    )

    report_path = artifact_dir / "report.md"
    paper_draft_path = artifact_dir / "paper_draft.md"
    summary_path = artifact_dir / "summary.json"
    iterations_path = artifact_dir / "iterations.jsonl"
    hypotheses_path = artifact_dir / "hypotheses.json"
    experiment_plans_path = artifact_dir / "experiment_plans.json"
    experiment_tasks_path = artifact_dir / "experiment_tasks.json"
    experiment_results_path = artifact_dir / "experiment_results.json"
    events_path = artifact_dir / "events.jsonl"
    manifest_path = artifact_dir / "manifest.json"
    zip_path = artifact_dir / "bundle.zip"

    if run.report_markdown:
        report_path.write_text(run.report_markdown, encoding="utf-8")
    if run.paper_draft_markdown:
        paper_draft_path.write_text(run.paper_draft_markdown, encoding="utf-8")

    summary_payload = {
        "run_id": run.id,
        "snapshot_id": run.snapshot_id,
        "status": run.status,
        "result_summary": run.result_summary,
        "result_payload_json": run.result_payload_json,
        "report_title": run.report_title,
        "paper_draft_title": run.paper_draft_title,
        "report_figure_path": run.report_figure_path,
    }
    summary_path.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    hypotheses = list_hypotheses(session, run_id)
    hypotheses_path.write_text(
        json.dumps(
            [
                {
                    "id": item.id,
                    "run_id": item.run_id,
                    "paper_id": item.paper_id,
                    "statement": item.statement,
                    "rationale": item.rationale,
                }
                for item in hypotheses
            ],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    plans = list_experiment_plans(session, run_id)
    experiment_plans_path.write_text(
        json.dumps(
            [
                {
                    "id": item.id,
                    "run_id": item.run_id,
                    "paper_id": item.paper_id,
                    "title": item.title,
                    "steps": json.loads(item.steps_json),
                }
                for item in plans
            ],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    tasks = list_experiment_tasks(session, run_id)
    experiment_tasks_path.write_text(
        json.dumps(
            [
                {
                    "id": item.id,
                    "run_id": item.run_id,
                    "plan_id": item.plan_id,
                    "paper_id": item.paper_id,
                    "title": item.title,
                    "task_type": item.task_type,
                    "status": item.status,
                    "config": json.loads(item.config_json),
                }
                for item in tasks
            ],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    run_results = list_run_results(session, run_id)
    experiment_results_path.write_text(
        json.dumps(
            [
                {
                    "id": item.id,
                    "run_id": item.run_id,
                    "paper_id": item.paper_id,
                    "method": item.method.name if item.method else None,
                    "dataset": item.dataset.name if item.dataset else None,
                    "metric": item.metric.name if item.metric else None,
                    "value": item.value,
                    "source": item.source,
                    "notes": item.notes,
                }
                for item in run_results
            ],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    iterations = list_iterations(session, run_id)
    with iterations_path.open("w", encoding="utf-8") as handle:
        for iteration in iterations:
            handle.write(
                json.dumps(
                    {
                        "id": iteration.id,
                        "run_id": iteration.run_id,
                        "iteration_index": iteration.iteration_index,
                        "plan_title": iteration.plan_title,
                        "metric_name": iteration.metric_name,
                        "metric_value": iteration.metric_value,
                        "decision": iteration.decision,
                        "rationale": iteration.rationale,
                    },
                    ensure_ascii=False,
                )
            )
            handle.write("\n")

    events = list_run_events(session, run_id)
    with events_path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(
                json.dumps(
                    {
                        "id": event.id,
                        "run_id": event.run_id,
                        "event_type": event.event_type,
                        "status": event.status,
                        "source": event.source,
                        "message": event.message,
                        "payload_json": event.payload_json,
                        "time_created": event.time_created.isoformat(),
                    },
                    ensure_ascii=False,
                )
            )
            handle.write("\n")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in (
            report_path,
            paper_draft_path,
            summary_path,
            iterations_path,
            hypotheses_path,
            experiment_plans_path,
            experiment_tasks_path,
            experiment_results_path,
            events_path,
        ):
            if path.exists():
                archive.write(path, arcname=path.name)
        if run.report_figure_path and Path(run.report_figure_path).exists():
            archive.write(run.report_figure_path, arcname=Path(run.report_figure_path).name)

    manifest_payload = {
        "run_id": run.id,
        "artifact_dir": str(artifact_dir),
        "files": {
            "report_path": _artifact_file_descriptor(report_path if run.report_markdown else None),
            "paper_draft_path": _artifact_file_descriptor(paper_draft_path if run.paper_draft_markdown else None),
            "figure_path": _artifact_file_descriptor(Path(run.report_figure_path) if run.report_figure_path else None),
            "summary_path": _artifact_file_descriptor(summary_path),
            "iterations_path": _artifact_file_descriptor(iterations_path),
            "hypotheses_path": _artifact_file_descriptor(hypotheses_path),
            "experiment_plans_path": _artifact_file_descriptor(experiment_plans_path),
            "experiment_tasks_path": _artifact_file_descriptor(experiment_tasks_path),
            "experiment_results_path": _artifact_file_descriptor(experiment_results_path),
            "events_path": _artifact_file_descriptor(events_path),
            "zip_path": _artifact_file_descriptor(zip_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with zipfile.ZipFile(zip_path, "a", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(manifest_path, arcname=manifest_path.name)

    return {
        "run_id": run.id,
        "artifact_dir": str(artifact_dir),
        "report_path": str(report_path) if run.report_markdown else None,
        "paper_draft_path": str(paper_draft_path) if run.paper_draft_markdown else None,
        "figure_path": run.report_figure_path,
        "summary_path": str(summary_path),
        "iterations_path": str(iterations_path),
        "hypotheses_path": str(hypotheses_path),
        "experiment_plans_path": str(experiment_plans_path),
        "experiment_tasks_path": str(experiment_tasks_path),
        "experiment_results_path": str(experiment_results_path),
        "events_path": str(events_path),
        "manifest_path": str(manifest_path),
        "zip_path": str(zip_path),
    }


def _build_results_table(results: list[ExperimentResult]) -> str:
    if not results:
        return "| Method | Dataset | Metric | Value | Source |\n|---|---|---|---:|---|\n| N/A | N/A | N/A | N/A | N/A |"

    lines = ["| Method | Dataset | Metric | Value | Source |", "|---|---|---|---:|---|"]
    for result in results:
        lines.append(
            f"| {result.method.name if result.method else 'Unknown'} | "
            f"{result.dataset.name if result.dataset else 'Unknown'} | "
            f"{result.metric.name if result.metric else 'Unknown'} | "
            f"{result.value} | {result.source} |"
        )
    return "\n".join(lines)


def _artifact_file_descriptor(path: Path | None) -> dict:
    if path is None:
        return {"path": "", "exists": False, "size_bytes": None, "sha256": None}
    if not path.exists():
        return {"path": str(path), "exists": False, "size_bytes": None, "sha256": None}
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": path.stat().st_size,
        "sha256": _file_sha256(path),
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_results_figure(run_id: int, results: list[ExperimentResult]) -> str:
    root = Path(os.getenv("FARS_ARTIFACTS_ROOT", ".artifacts"))
    run_dir = root / "runs" / f"run-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "results-chart.svg"

    labels: list[str] = []
    values: list[float] = []
    for result in results:
        labels.append(
            f"{result.method.name if result.method else 'Unknown'}-{result.metric.name if result.metric else 'Metric'}"
        )
        try:
            values.append(float(result.value))
        except ValueError:
            values.append(0.0)

    if not labels:
        labels = ["No Results"]
        values = [0.0]

    width = 700
    height = 320
    left = 60
    bottom = 260
    chart_width = 560
    chart_height = 180
    max_value = max(values) if values else 1.0
    max_value = max(max_value, 1.0)
    bar_width = max(40, chart_width // max(len(values), 1) - 20)

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="350" y="30" text-anchor="middle" font-size="20" font-family="Arial">Experiment Results</text>',
        f'<line x1="{left}" y1="{bottom}" x2="{left + chart_width}" y2="{bottom}" stroke="black"/>',
        f'<line x1="{left}" y1="{bottom}" x2="{left}" y2="{bottom - chart_height}" stroke="black"/>',
    ]

    for i, (label, value) in enumerate(zip(labels, values, strict=False)):
        x = left + 20 + i * (bar_width + 20)
        bar_height = 0 if max_value == 0 else (value / max_value) * chart_height
        y = bottom - bar_height
        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="#4C78A8" />'
        )
        svg_parts.append(
            f'<text x="{x + bar_width/2}" y="{bottom + 18}" text-anchor="middle" font-size="10" font-family="Arial">{label}</text>'
        )
        svg_parts.append(
            f'<text x="{x + bar_width/2}" y="{max(y - 6, 40)}" text-anchor="middle" font-size="10" font-family="Arial">{value}</text>'
        )

    for tick in range(0, 6):
        tick_value = max_value * tick / 5
        y = bottom - (chart_height * tick / 5)
        svg_parts.append(f'<line x1="{left-4}" y1="{y}" x2="{left}" y2="{y}" stroke="black"/>')
        svg_parts.append(
            f'<text x="{left-8}" y="{y+4}" text-anchor="end" font-size="10" font-family="Arial">{round(tick_value, 2)}</text>'
        )

    svg_parts.append("</svg>")
    path.write_text("\n".join(str(part) for part in svg_parts), encoding="utf-8")
    return str(path)


def build_execution_manifest(session: Session, run_id: int) -> dict:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise ValueError(f"Unknown run: {run_id}")
    return {
        "run_id": run.id,
        "snapshot_id": run.snapshot_id,
        "branch_name": run.branch_name or f"run-{run.id}",
        "knowledge_mode": "shared_snapshot",
        "execution_mode": "isolated_worktree",
        "worktree_path": run.worktree_path,
        "repo_root": None,
    }
