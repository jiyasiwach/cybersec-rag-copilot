# Backend image. The ChromaDB + BM25 index is built at IMAGE BUILD time from the committed
# data/processed/chunks.jsonl, so production needs no persistent disk.
# Build from the REPO ROOT (needs ../data):  docker build -f backend/Dockerfile -t cybersec-backend .
# Pass the key only at build time for embeddings:  --secret id=openai_key,env=OPENAI_API_KEY
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv/backend

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY data/processed/chunks.jsonl /srv/data/processed/chunks.jsonl

# Build the index inside the image. The key is read from a BuildKit secret and never stored in a layer.
RUN --mount=type=secret,id=openai_key \
    OPENAI_API_KEY="$(cat /run/secrets/openai_key)" python -m ingest.build_index

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
