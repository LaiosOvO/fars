from fastapi import FastAPI

from fars.api.routes.graph import router as graph_router
from fars.api.routes.health import router as health_router
from fars.api.routes.papers import router as papers_router
from fars.config import get_settings
from fars.repositories.memory import InMemoryKnowledgeBase


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )
    app.state.knowledge_base = InMemoryKnowledgeBase.bootstrap()
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(papers_router, prefix=settings.api_prefix)
    app.include_router(graph_router, prefix=settings.api_prefix)
    return app


app = create_app()
