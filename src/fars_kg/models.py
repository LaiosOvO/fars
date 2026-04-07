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
