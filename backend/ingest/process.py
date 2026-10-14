"""Clean + chunk the raw sources into data/processed/chunks.jsonl.

    python -m ingest.process

One natural unit per item (technique / OWASP category / CVE). Units over ~500 tokens are
split into ~500-token chunks with ~60-token overlap, title repeated on each sub-chunk.
chunks.jsonl IS committed to git: it is the knowledge base the index is built from.
"""
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import tiktoken

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
RAW = DATA_DIR / "raw"
OUT = DATA_DIR / "processed" / "chunks.jsonl"

CHUNK_TOKENS = 500
OVERLAP_TOKENS = 60
KEV_LIMIT = 200

enc = tiktoken.get_encoding("cl100k_base")  # tokenizer used by text-embedding-3-*


@dataclass
class Chunk:
    chunk_id: str
    source: str   # mitre | owasp | cisa_kev
    doc_id: str   # T1059.001 | A03:2021 | CVE-2024-3400
    title: str
    url: str
    text: str


# ---------- helpers ----------

def clean(text: str) -> str:
    """Strip markdown/HTML noise and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)                       # html tags
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)        # [label](url) -> label
    text = re.sub(r"\(Citation: [^)]+\)", "", text)             # MITRE citation markers
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_unit(source: str, doc_id: str, title: str, url: str, body: str) -> list[Chunk]:
    """Return one chunk, or several overlapping ones if the unit is too long."""
    header = f"{title}\n\n"
    tokens = enc.encode(body)
    budget = CHUNK_TOKENS - len(enc.encode(header))
    if len(tokens) <= budget:
        return [Chunk(f"{source}:{doc_id}:0", source, doc_id, title, url, header + body)]

    chunks: list[Chunk] = []
    start, i = 0, 0
    while start < len(tokens):
        piece = enc.decode(tokens[start : start + budget])
        chunks.append(Chunk(f"{source}:{doc_id}:{i}", source, doc_id, title, url, header + piece.strip()))
        if start + budget >= len(tokens):
            break
        start += budget - OVERLAP_TOKENS
        i += 1
    return chunks


# ---------- MITRE ATT&CK ----------

def load_mitre() -> list[Chunk]:
    bundle = json.loads((RAW / "mitre" / "enterprise-attack.json").read_text())
    chunks: list[Chunk] = []
    for obj in bundle["objects"]:
        if obj.get("type") != "attack-pattern" or obj.get("revoked") or obj.get("x_mitre_deprecated"):
            continue
        ref = next((r for r in obj.get("external_references", []) if r.get("source_name") == "mitre-attack"), None)
        if not ref:
            continue
        tid, url = ref["external_id"], ref.get("url", "")
        tactics = sorted({p["phase_name"].replace("-", " ") for p in obj.get("kill_chain_phases", []) if p.get("kill_chain_name") == "mitre-attack"})
        platforms = obj.get("x_mitre_platforms", [])
        parts = [f"Technique {tid}: {obj['name']}", clean(obj.get("description", ""))]
        if tactics:
            parts.append("Tactics: " + ", ".join(tactics))
        if platforms:
            parts.append("Platforms: " + ", ".join(platforms))
        if obj.get("x_mitre_detection"):
            parts.append("Detection: " + clean(obj["x_mitre_detection"]))
        chunks += split_unit("mitre", tid, f"{tid} {obj['name']}", url, "\n\n".join(parts))
    return chunks


# ---------- OWASP Top 10 2021 ----------

OWASP_SECTIONS = ["Description", "How to Prevent", "Example Attack Scenarios"]


def load_owasp() -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted((RAW / "owasp").glob("A*.md")):
        md = path.read_text(encoding="utf-8")
        title_m = re.search(r"^#\s+(.+)$", md, re.M)
        # heading looks like "A03:2021 – Injection    ![icon](assets/...){: style=...}" -> drop the icon
        title = clean(re.split(r"!\[", title_m.group(1))[0]) if title_m else path.stem
        doc_id = re.match(r"A\d\d", path.stem).group(0) + ":2021"
        url = f"https://owasp.org/Top10/{path.stem}/"
        # split on "## Heading" and keep only the sections we want, in order
        sections = dict(re.findall(r"^##\s+(.+?)\s*$\n(.*?)(?=^##\s|\Z)", md, re.M | re.S))
        parts = []  # split_unit() already puts the title on top
        for name in OWASP_SECTIONS:
            body = next((v for k, v in sections.items() if k.lower().startswith(name.lower())), "")
            if body.strip():
                parts.append(f"{name}: {clean(body)}")
        chunks += split_unit("owasp", doc_id, title, url, "\n\n".join(parts))
    return chunks


# ---------- CISA KEV ----------

def load_kev() -> list[Chunk]:
    cat = json.loads((RAW / "cisa_kev" / "known_exploited_vulnerabilities.json").read_text())
    vulns = sorted(cat["vulnerabilities"], key=lambda v: v["dateAdded"], reverse=True)[:KEV_LIMIT]
    chunks: list[Chunk] = []
    for v in vulns:
        cve = v["cveID"]
        body = "\n\n".join([
            f"{cve}: {v['vulnerabilityName']}",
            f"Vendor: {v['vendorProject']}. Product: {v['product']}.",
            clean(v["shortDescription"]),
            f"Date added to KEV: {v['dateAdded']}. Required action: {clean(v['requiredAction'])}",
        ])
        chunks += split_unit("cisa_kev", cve, f"{cve} {v['vulnerabilityName']}", f"https://nvd.nist.gov/vuln/detail/{cve}", body)
    return chunks


# ---------- main ----------

def main() -> None:
    all_chunks: list[Chunk] = []
    for name, loader in [("mitre", load_mitre), ("owasp", load_owasp), ("cisa_kev", load_kev)]:
        chunks = loader()
        docs = len({c.doc_id for c in chunks})
        toks = sum(len(enc.encode(c.text)) for c in chunks)
        print(f"{name:9s} {docs:5d} docs -> {len(chunks):5d} chunks  ({toks:,} tokens)")
        all_chunks += chunks

    ids = [c.chunk_id for c in all_chunks]
    assert len(ids) == len(set(ids)), "duplicate chunk_id"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
    print(f"\nwrote {len(all_chunks)} chunks -> {OUT.relative_to(DATA_DIR.parent)}  ({datetime.now():%Y-%m-%d %H:%M})")


if __name__ == "__main__":
    main()
