from pydantic import BaseModel, ConfigDict, Field

from fars.domain.models import Paper, PaperEdge, PaperVersion


class TopicIngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=50)


class TopicIngestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    count: int
    results: list[Paper]


class PaperVersionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str
    versions: list[PaperVersion]


class PaperGraphResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str
    neighbors: list[PaperEdge]
