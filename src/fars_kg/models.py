from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fars_kg.db import Base


class TimestampMixin:
    time_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    time_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Paper(TimestampMixin, Base):
    __tablename__ = "paper"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_title: Mapped[str] = mapped_column(String(1024), nullable=False)
    doi: Mapped[str | None] = mapped_column(String(512), unique=True)
    arxiv_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    openalex_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    semantic_scholar_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    publication_year: Mapped[int | None] = mapped_column(Integer)
    venue: Mapped[str | None] = mapped_column(String(512))
    abstract: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(32))
    is_open_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    citation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retraction_status: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)
    primary_source: Mapped[str | None] = mapped_column(String(64))

    versions: Mapped[list[PaperVersion]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    method_links: Mapped[list[PaperMethodLink]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    dataset_links: Mapped[list[PaperDatasetLink]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    metric_links: Mapped[list[PaperMetricLink]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    evidence_snapshots: Mapped[list[EvidenceSnapshot]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    experiment_results: Mapped[list[ExperimentResult]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    outgoing_edges: Mapped[list[PaperEdge]] = relationship(
        back_populates="src_paper",
        cascade="all, delete-orphan",
        foreign_keys="PaperEdge.src_paper_id",
    )
    incoming_edges: Mapped[list[PaperEdge]] = relationship(
        back_populates="dst_paper",
        cascade="all, delete-orphan",
        foreign_keys="PaperEdge.dst_paper_id",
    )


class PaperVersion(TimestampMixin, Base):
    __tablename__ = "paper_version"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("paper.id", ondelete="CASCADE"), nullable=False)
    version_type: Mapped[str] = mapped_column(String(64), default="source", nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    pdf_url: Mapped[str | None] = mapped_column(String(2048))
    local_pdf_path: Mapped[str | None] = mapped_column(String(2048))
    tei_url: Mapped[str | None] = mapped_column(String(2048))
    raw_tei_xml: Mapped[str | None] = mapped_column(Text)
    parse_status: Mapped[str] = mapped_column(String(64), default="not_parsed", nullable=False)
    parse_error: Mapped[str | None] = mapped_column(Text)
    checksum: Mapped[str | None] = mapped_column(String(128))
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    paper: Mapped[Paper] = relationship(back_populates="versions")
    sections: Mapped[list[PaperSection]] = relationship(back_populates="paper_version", cascade="all, delete-orphan")
    citations: Mapped[list[Citation]] = relationship(back_populates="source_paper_version", cascade="all, delete-orphan")


class PaperSection(TimestampMixin, Base):
    __tablename__ = "paper_section"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_version_id: Mapped[int] = mapped_column(ForeignKey("paper_version.id", ondelete="CASCADE"), nullable=False)
    section_type: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)
    heading: Mapped[str | None] = mapped_column(String(512))
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_start: Mapped[int | None] = mapped_column(Integer)
    page_end: Mapped[int | None] = mapped_column(Integer)
    text: Mapped[str | None] = mapped_column(Text)

    paper_version: Mapped[PaperVersion] = relationship(back_populates="sections")
    chunks: Mapped[list[PaperChunk]] = relationship(back_populates="section", cascade="all, delete-orphan")


class PaperChunk(TimestampMixin, Base):
    __tablename__ = "paper_chunk"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("paper_section.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_start: Mapped[int | None] = mapped_column(Integer)
    page_end: Mapped[int | None] = mapped_column(Integer)
    bbox_json: Mapped[str | None] = mapped_column(Text)
    embedding_json: Mapped[str | None] = mapped_column(Text)

    section: Mapped[PaperSection] = relationship(back_populates="chunks")


class Citation(TimestampMixin, Base):
    __tablename__ = "citation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_paper_version_id: Mapped[int] = mapped_column(ForeignKey("paper_version.id", ondelete="CASCADE"), nullable=False)
    target_paper_id: Mapped[int | None] = mapped_column(ForeignKey("paper.id", ondelete="SET NULL"))
    raw_reference: Mapped[str] = mapped_column(Text, nullable=False)
    citation_key: Mapped[str | None] = mapped_column(String(256))
    resolution_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    source_paper_version: Mapped[PaperVersion] = relationship(back_populates="citations")
    target_paper: Mapped[Paper | None] = relationship()
    contexts: Mapped[list[CitationContext]] = relationship(back_populates="citation", cascade="all, delete-orphan")


class CitationContext(TimestampMixin, Base):
    __tablename__ = "citation_context"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    citation_id: Mapped[int] = mapped_column(ForeignKey("citation.id", ondelete="CASCADE"), nullable=False)
    chunk_id: Mapped[int | None] = mapped_column(ForeignKey("paper_chunk.id", ondelete="SET NULL"))
    context_text: Mapped[str] = mapped_column(Text, nullable=False)
    context_type: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)

    citation: Mapped[Citation] = relationship(back_populates="contexts")
    chunk: Mapped[PaperChunk | None] = relationship()


class PaperEdge(TimestampMixin, Base):
    __tablename__ = "paper_edge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    src_paper_id: Mapped[int] = mapped_column(ForeignKey("paper.id", ondelete="CASCADE"), nullable=False)
    dst_paper_id: Mapped[int] = mapped_column(ForeignKey("paper.id", ondelete="CASCADE"), nullable=False)
    edge_type: Mapped[str] = mapped_column(String(64), default="cites", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    evidence_chunk_id: Mapped[int | None] = mapped_column(ForeignKey("paper_chunk.id", ondelete="SET NULL"))
    source: Mapped[str] = mapped_column(String(64), default="citation", nullable=False)

    src_paper: Mapped[Paper] = relationship(back_populates="outgoing_edges", foreign_keys=[src_paper_id])
    dst_paper: Mapped[Paper] = relationship(back_populates="incoming_edges", foreign_keys=[dst_paper_id])
    evidence_chunk: Mapped[PaperChunk | None] = relationship()


class Method(TimestampMixin, Base):
    __tablename__ = "method"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    paper_links: Mapped[list[PaperMethodLink]] = relationship(back_populates="method", cascade="all, delete-orphan")
    experiment_results: Mapped[list[ExperimentResult]] = relationship(back_populates="method")


class Dataset(TimestampMixin, Base):
    __tablename__ = "dataset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    paper_links: Mapped[list[PaperDatasetLink]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
    experiment_results: Mapped[list[ExperimentResult]] = relationship(back_populates="dataset")


class Metric(TimestampMixin, Base):
    __tablename__ = "metric"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    paper_links: Mapped[list[PaperMetricLink]] = relationship(back_populates="metric", cascade="all, delete-orphan")
    experiment_results: Mapped[list[ExperimentResult]] = relationship(back_populates="metric")


class PaperMethodLink(TimestampMixin, Base):
    __tablename__ = "paper_method_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("paper.id", ondelete="CASCADE"), nullable=False)
    method_id: Mapped[int] = mapped_column(ForeignKey("method.id", ondelete="CASCADE"), nullable=False)

    paper: Mapped[Paper] = relationship(back_populates="method_links")
    method: Mapped[Method] = relationship(back_populates="paper_links")


class PaperDatasetLink(TimestampMixin, Base):
    __tablename__ = "paper_dataset_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("paper.id", ondelete="CASCADE"), nullable=False)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False)

    paper: Mapped[Paper] = relationship(back_populates="dataset_links")
    dataset: Mapped[Dataset] = relationship(back_populates="paper_links")


class PaperMetricLink(TimestampMixin, Base):
    __tablename__ = "paper_metric_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("paper.id", ondelete="CASCADE"), nullable=False)
    metric_id: Mapped[int] = mapped_column(ForeignKey("metric.id", ondelete="CASCADE"), nullable=False)

    paper: Mapped[Paper] = relationship(back_populates="metric_links")
    metric: Mapped[Metric] = relationship(back_populates="paper_links")


class EvidenceSnapshot(TimestampMixin, Base):
    __tablename__ = "evidence_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("paper.id", ondelete="CASCADE"), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(512))
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)

    paper: Mapped[Paper] = relationship(back_populates="evidence_snapshots")
    runs: Mapped[list[ResearchRun]] = relationship(back_populates="snapshot", cascade="all, delete-orphan")


class ResearchRun(TimestampMixin, Base):
    __tablename__ = "research_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("evidence_snapshot.id", ondelete="CASCADE"), nullable=False)
    branch_name: Mapped[str | None] = mapped_column(String(256))
    worktree_path: Mapped[str | None] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(64), default="created", nullable=False)
    result_summary: Mapped[str | None] = mapped_column(Text)
    result_payload_json: Mapped[str | None] = mapped_column(Text)
    report_title: Mapped[str | None] = mapped_column(String(512))
    report_markdown: Mapped[str | None] = mapped_column(Text)
    report_figure_path: Mapped[str | None] = mapped_column(String(2048))
    paper_draft_title: Mapped[str | None] = mapped_column(String(512))
    paper_draft_markdown: Mapped[str | None] = mapped_column(Text)
    artifact_dir: Mapped[str | None] = mapped_column(String(2048))

    snapshot: Mapped[EvidenceSnapshot] = relationship(back_populates="runs")
    experiment_results: Mapped[list[ExperimentResult]] = relationship(back_populates="run", cascade="all, delete-orphan")
    hypotheses: Mapped[list[ResearchHypothesis]] = relationship(back_populates="run", cascade="all, delete-orphan")
    experiment_plans: Mapped[list[ExperimentPlan]] = relationship(back_populates="run", cascade="all, delete-orphan")
    experiment_tasks: Mapped[list[ExperimentTask]] = relationship(back_populates="run", cascade="all, delete-orphan")
    iterations: Mapped[list[ResearchIteration]] = relationship(back_populates="run", cascade="all, delete-orphan")
    events: Mapped[list[ResearchRunEvent]] = relationship(back_populates="run", cascade="all, delete-orphan")


class ExperimentResult(TimestampMixin, Base):
    __tablename__ = "experiment_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("research_run.id", ondelete="CASCADE"), nullable=False)
    paper_id: Mapped[int] = mapped_column(ForeignKey("paper.id", ondelete="CASCADE"), nullable=False)
    method_id: Mapped[int | None] = mapped_column(ForeignKey("method.id", ondelete="SET NULL"))
    dataset_id: Mapped[int | None] = mapped_column(ForeignKey("dataset.id", ondelete="SET NULL"))
    metric_id: Mapped[int | None] = mapped_column(ForeignKey("metric.id", ondelete="SET NULL"))
    value: Mapped[str] = mapped_column(String(128), nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="manual", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    run: Mapped[ResearchRun] = relationship(back_populates="experiment_results")
    paper: Mapped[Paper] = relationship(back_populates="experiment_results")
    method: Mapped[Method | None] = relationship(back_populates="experiment_results")
    dataset: Mapped[Dataset | None] = relationship(back_populates="experiment_results")
    metric: Mapped[Metric | None] = relationship(back_populates="experiment_results")


class ResearchHypothesis(TimestampMixin, Base):
    __tablename__ = "research_hypothesis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("research_run.id", ondelete="CASCADE"), nullable=False)
    paper_id: Mapped[int] = mapped_column(ForeignKey("paper.id", ondelete="CASCADE"), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)

    run: Mapped[ResearchRun] = relationship(back_populates="hypotheses")
    paper: Mapped[Paper] = relationship()


class ExperimentPlan(TimestampMixin, Base):
    __tablename__ = "experiment_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("research_run.id", ondelete="CASCADE"), nullable=False)
    paper_id: Mapped[int] = mapped_column(ForeignKey("paper.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    steps_json: Mapped[str] = mapped_column(Text, nullable=False)

    run: Mapped[ResearchRun] = relationship(back_populates="experiment_plans")
    paper: Mapped[Paper] = relationship()
    tasks: Mapped[list[ExperimentTask]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class ExperimentTask(TimestampMixin, Base):
    __tablename__ = "experiment_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("research_run.id", ondelete="CASCADE"), nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("experiment_plan.id", ondelete="CASCADE"), nullable=False)
    paper_id: Mapped[int] = mapped_column(ForeignKey("paper.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), default="benchmark", nullable=False)
    config_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)

    run: Mapped[ResearchRun] = relationship(back_populates="experiment_tasks")
    plan: Mapped[ExperimentPlan] = relationship(back_populates="tasks")
    paper: Mapped[Paper] = relationship()


class ResearchIteration(TimestampMixin, Base):
    __tablename__ = "research_iteration"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("research_run.id", ondelete="CASCADE"), nullable=False)
    iteration_index: Mapped[int] = mapped_column(Integer, nullable=False)
    plan_title: Mapped[str] = mapped_column(String(512), nullable=False)
    metric_name: Mapped[str | None] = mapped_column(String(128))
    metric_value: Mapped[str | None] = mapped_column(String(128))
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)

    run: Mapped[ResearchRun] = relationship(back_populates="iterations")


class ResearchRunEvent(TimestampMixin, Base):
    __tablename__ = "research_run_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("research_run.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="info", nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="system", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[str | None] = mapped_column(Text)

    run: Mapped[ResearchRun] = relationship(back_populates="events")
