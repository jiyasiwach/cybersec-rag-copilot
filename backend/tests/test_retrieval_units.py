"""Pure-function tests: no index, no network."""
from app.rag.retriever import ids_in_query, rrf
from app.rag.tokenize import tokenize


def test_tokenize_keeps_ids_intact():
    assert tokenize("Abuse of T1059.001 and CVE-2024-3400, see A03:2021.") == [
        "abuse", "of", "t1059.001", "and", "cve-2024-3400", "see", "a03:2021",
    ]


def test_rrf_prefers_items_ranked_by_both_engines():
    scores = rrf([["a", "b", "c"], ["b", "d", "a"]])
    order = sorted(scores, key=scores.get, reverse=True)
    assert order[:2] == ["b", "a"]          # both appear twice; b ranks higher overall
    assert scores["d"] > scores["c"]         # d was rank 2, c rank 3; each seen by one engine


def test_ids_in_query_normalises():
    assert ids_in_query("what is t1053.005?") == ["T1053.005"]
    assert ids_in_query("CVE-2024-3400 and A03") == ["CVE-2024-3400", "A03:2021"]
    assert ids_in_query("how do attackers persist?") == []
