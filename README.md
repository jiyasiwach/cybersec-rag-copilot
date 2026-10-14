# CyberSec RAG Copilot

**A cybersecurity chat assistant that answers only from a curated knowledge base — MITRE ATT&CK, OWASP Top 10 (2021) and CISA KEV — with streamed answers, clickable citations, a two-layer prompt-injection guardrail and a built-in eval dashboard.**

🔗 **Live demo:** https://cybersec-rag-copilot-tan.vercel.app · 🎬 Demo GIF: _coming soon_

## What it does

- **Grounded answers, streamed token by token.** Every factual claim carries a `[n]` citation; clicking it opens the exact retrieved chunk and a link to the original source. If the knowledge base doesn't cover the question, the assistant says so instead of guessing.
- **Hybrid retrieval.** Vector search (ChromaDB, cosine) + BM25 keyword search fused with Reciprocal Rank Fusion, plus an exact-ID boost for `T1059.001`, `CVE-2015-5477`, `A03:2021`. Switchable per request: `hybrid | vector | bm25`.
- **Guardrail before retrieval.** Free regex heuristics block obvious injections; ambiguous inputs go to a small LLM classifier returning strict JSON. Retrieved context is delimited and declared as data, never instructions. Blocked requests show the verdict, reason and layer.
- **Metrics on every answer:** retrieval / generation / total latency, tokens, estimated cost.
- **Eval dashboard:** Hit@5 and MRR for all three retrieval modes, LLM-judged faithfulness and citation accuracy, guardrail block / false-positive rates.

## Architecture

```
question ──▶ guardrail ──▶ hybrid retrieval ──▶ prompt ──▶ LLM ──▶ streamed answer + [n] citations
             heuristics      vector (Chroma)      numbered,   OpenAI    SSE: guardrail → sources → token* → done
             → classifier    + BM25, RRF k=60     delimited
                 │
                 └─ blocked → verdict + reason (no retrieval, no LLM answer)
```

Knowledge base: 948 chunks — 706 ATT&CK Enterprise techniques, 10 OWASP categories, 200 most recent KEV entries — stored in `data/processed/chunks.jsonl` (committed) and indexed into ChromaDB + a BM25 pickle at build time.

## Eval results

20 questions (MITRE / OWASP / KEV, mix of exact-ID and conceptual), 5 prompt-injection attacks, 2 off-topic questions. `python -m evals.run_eval`, 14 Oct 2026, `openai/gpt-4.1-mini` + `text-embedding-3-small`.

| Mode | Hit@5 | MRR |
|---|---|---|
| **hybrid** | **100%** | **1.000** |
| vector | 100% | 0.975 |
| bm25 | 100% | 0.867 |

Faithfulness **1.00** · Citation accuracy **1.00** (LLM-as-judge on hybrid answers) · Attacks blocked **5/5** · Off-topic refused **2/2** · False positives **0/20** · Avg latency **3.3 s** · Avg cost **$0.001 / query**

Hybrid beats either engine alone: BM25 misranks a few conceptual questions, vector search slips on exact IDs; RRF plus the ID boost puts the right document first on every question in the set.

## Design decisions

- **One natural unit per chunk** (a technique / an OWASP category / a CVE), split only when over ~500 tokens, with 60-token overlap and the title repeated. Citations point at something a human recognises.
- **Hybrid + RRF rather than weighted scores.** Embeddings blur exact identifiers; BM25 nails them. RRF (k=60) merges rankings without tuning weights across two incomparable score scales.
- **Guardrail threshold 0.6.** One strong rule (ignore-instructions, jailbreak, chat-template markers) blocks outright with no LLM call; weaker signals and clean-looking text go to the classifier, which also catches off-topic questions. Classifier failures fail open but are labelled.
- **Index built in the Docker image** from the committed `chunks.jsonl`, so the backend runs on hosts with no persistent disk.
- **SSE over one POST** so the UI shows the verdict and source chips before the first token.

## Local setup

Prerequisites: Python 3.11+, Node 22+, an OpenAI API key.

```bash
# backend
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # put OPENAI_API_KEY in .env
python -m ingest.fetch_sources
python -m ingest.process
python -m ingest.build_index   # ~220k tokens ≈ $0.005
uvicorn app.main:app --reload --port 8000

# frontend (new terminal)
cd frontend
npm install
cp .env.example .env           # VITE_API_URL=http://localhost:8000
npm run dev                    # http://localhost:5173
```

Tests: `cd backend && pytest`. Evals: `python -m evals.run_eval` (≈ 50 LLM calls, well under $0.10).

Docker: `export OPENAI_API_KEY=sk-... && docker compose up --build`.

## Deploy

- **Backend → Render** (Docker): `render.yaml` is included. Set `OPENAI_API_KEY` as a secret and `FRONTEND_ORIGIN` to your Vercel URL. The image build runs `ingest.build_index`, so the key must also be available at build time.
- **Frontend → Vercel**: import `frontend/`, set `VITE_API_URL` to the Render URL. `vercel.json` handles SPA routing.

## Tech stack

Python 3.11 · FastAPI · Uvicorn · ChromaDB · rank_bm25 · OpenAI SDK · Pydantic v2 · slowapi · tiktoken · pytest — React 18 · Vite · TypeScript · Tailwind CSS v4 · React Router · react-markdown — Docker.

## Project layout

```
backend/app/{api,rag,guardrail,llm}   FastAPI routers, retrieval, guardrail layers, LLM provider
backend/ingest                        fetch_sources → process → build_index
backend/evals                         questions.json, run_eval.py → results.json
frontend/src/{pages,components,api}   Chat, Eval, Architecture
data/processed/chunks.jsonl           the knowledge base (committed); data/raw is gitignored
```
