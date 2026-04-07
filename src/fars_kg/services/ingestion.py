from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from fars_kg.connectors.openalex import OpenAlexClientProtocol
from fars_kg.services.repository import upsert_paper_from_openalex


@dataclass
class TopicIngestionResult:
    topic: str
    papers_created: int
    papers_updated: int
    versions_created: int
    paper_ids: list[int]
    version_ids: list[int]


class TopicIngestionService:
    def __init__(self, openalex_client: OpenAlexClientProtocol):
        self.openalex_client = openalex_client

    def ingest_topic(self, session: Session, topic: str, limit: int = 10) -> TopicIngestionResult:
        works = self.openalex_client.search_topic(topic=topic, limit=limit)
        papers_created = 0
        papers_updated = 0
        versions_created = 0
        paper_ids: list[int] = []
        version_ids: list[int] = []

        for work in works:
            result = upsert_paper_from_openalex(session, work)
            papers_created += int(result.created)
            papers_updated += int(not result.created)
            versions_created += int(result.version_created)
            paper_ids.append(result.paper.id)
            version_ids.append(result.version.id)

        return TopicIngestionResult(
            topic=topic,
            papers_created=papers_created,
            papers_updated=papers_updated,
            versions_created=versions_created,
            paper_ids=paper_ids,
            version_ids=version_ids,
        )
