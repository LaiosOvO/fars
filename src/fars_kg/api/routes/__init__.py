from fars_kg.api.routes.graph import router as graph_router
from fars_kg.api.routes.health import router as health_router
from fars_kg.api.routes.papers import router as papers_router
from fars_kg.api.routes.topics import router as topics_router

__all__ = ["graph_router", "health_router", "papers_router", "topics_router"]
