from fars_kg.api.routes.console import router as console_router
from fars_kg.api.routes.loops import router as loops_router
from fars_kg.api.routes.workflows import router as workflows_router
from fars_kg.api.routes.evidence import router as evidence_router
from fars_kg.api.routes.graph import router as graph_router
from fars_kg.api.routes.health import router as health_router
from fars_kg.api.routes.papers import router as papers_router
from fars_kg.api.routes.topics import router as topics_router

__all__ = ["console_router", "evidence_router", "graph_router", "health_router", "loops_router", "papers_router", "topics_router", "workflows_router"]
