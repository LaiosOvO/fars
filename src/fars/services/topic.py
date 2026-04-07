from __future__ import annotations

import re


TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-+/]*")


def expand_topic(topic: str, max_terms: int = 8) -> list[str]:
    topic = topic.strip()
    if not topic:
        return []

    tokens = [token for token in TOKEN_RE.findall(topic) if len(token) > 2]
    expansions: list[str] = []

    def add(term: str) -> None:
        cleaned = term.strip()
        if cleaned and cleaned not in expansions:
            expansions.append(cleaned)

    add(topic)
    add(f"\"{topic}\"")

    if tokens:
        add(" ".join(tokens))

    if len(tokens) >= 2:
        add(" ".join(tokens[:2]))
        add(" ".join(tokens[-2:]))

    for token in tokens:
        add(token)

    if ":" in topic:
        for part in topic.split(":"):
            add(part.strip())

    return expansions[:max_terms]
