from typing import Protocol

from fars.domain.models import (
    Citation,
    CitationContext,
    Paper,
    PaperEdge,
    PaperVersion,
    ParsedPaperDocument,
)


class PaperRepository(Protocol):
    def search(self, query: str) -> list[Paper]:
        """Search papers by a topic or keyword query."""

    def get(self, paper_id: str) -> Paper | None:
        """Fetch a paper by canonical identifier."""


class PaperVersionRepository(Protocol):
    def list_versions(self, paper_id: str) -> list[PaperVersion]:
        """List available versions for a paper."""


class CitationRepository(Protocol):
    def list_references(self, paper_version_id: str) -> list[Citation]:
        """List resolved or unresolved references for a paper version."""

    def list_contexts(self, citation_id: str) -> list[CitationContext]:
        """List citation contexts for a citation."""


class GraphRepository(Protocol):
    def neighbors(self, paper_id: str) -> list[PaperEdge]:
        """Return graph edges adjacent to the given paper."""


class MetadataConnector(Protocol):
    def search(self, query: str) -> list[Paper]:
        """Search a remote metadata source and return normalized papers."""


class PaperParser(Protocol):
    def parse_fulltext(self, paper_version: PaperVersion) -> ParsedPaperDocument:
        """Parse a paper version and return a normalized parser payload."""
