from __future__ import annotations

from backend.rag.src.retrieval import Retriever


def test_default_index_is_independent_of_working_directory(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.chdir(tmp_path)

    results = Retriever().search("prefix caching", 2)

    assert len(results) == 2
    assert all(source.file_path.startswith("data/raw/") for source in results)


def test_search_handles_empty_query_and_non_positive_k() -> None:
    retriever = Retriever()

    assert retriever.search("", 5) == []
    assert retriever.search("prefix caching", 0) == []
