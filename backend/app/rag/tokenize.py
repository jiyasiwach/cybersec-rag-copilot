"""Tokenizer shared by BM25 indexing (ingest) and BM25 querying (retriever).

Lowercases and splits on whitespace/punctuation, but keeps identifiers intact:
T1059.001, CVE-2024-1234, A03:2021 each stay one token. Both sides MUST use this
function, otherwise the pickled index and the queries would not match.
"""
import re

# An ID token (letters/digits joined by . : - ) or a plain word.
_TOKEN = re.compile(r"[a-z0-9]+(?:[.:\-][a-z0-9]+)+|[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())
