from fastapi import Request

from fars.repositories.memory import InMemoryKnowledgeBase


def get_knowledge_base(request: Request) -> InMemoryKnowledgeBase:
    return request.app.state.knowledge_base
