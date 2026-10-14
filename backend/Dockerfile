# Backend image. Build from the REPO ROOT (it needs ../data):
#   docker build -f backend/Dockerfile -t cybersec-backend .
#
# The ChromaDB + BM25 index is built from the committed data/processed/chunks.jsonl:
#   - at image build time when a key is available (BuildKit secret `openai_key`, or a Render
#     secret file at /etc/secrets/openai_key, or OPENAI_API_KEY as a build arg), or
#   - at container start (start.sh) otherwise. Either way no persistent disk is needed.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv/backend

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY data/processed/chunks.jsonl /srv/data/processed/chunks.jsonl

# Model/gateway settings used for the build-time embedding step (runtime reads env vars).
ARG OPENAI_API_KEY=""
ARG OPENAI_BASE_URL=""
ARG EMBEDDING_MODEL="text-embedding-3-small"
ENV OPENAI_BASE_URL=$OPENAI_BASE_URL EMBEDDING_MODEL=$EMBEDDING_MODEL

# Try to build the index now; skip quietly if no key is reachable (start.sh builds it later).
RUN --mount=type=secret,id=openai_key,required=false \
    KEY="$OPENAI_API_KEY"; \
    [ -z "$KEY" ] && [ -f /run/secrets/openai_key ] && KEY="$(cat /run/secrets/openai_key)"; \
    [ -z "$KEY" ] && [ -f /etc/secrets/openai_key ] && KEY="$(cat /etc/secrets/openai_key)"; \
    if [ -n "$KEY" ]; then OPENAI_API_KEY="$KEY" python -m ingest.build_index; \
    else echo "no key at build time; index will be built on first start"; fi

EXPOSE 8000
CMD ["./start.sh"]
