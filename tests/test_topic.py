from fars.services.topic import expand_topic


def test_expand_topic_produces_phrase_and_terms() -> None:
    expansions = expand_topic("graph neural networks for citation recommendation", max_terms=8)

    assert "graph neural networks for citation recommendation" in expansions
    assert "\"graph neural networks for citation recommendation\"" in expansions
    assert "graph" in expansions
    assert "graph neural" in expansions
