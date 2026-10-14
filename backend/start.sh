#!/bin/sh
# Container entrypoint. Builds the index on first start if the image was built without a key
# (e.g. on hosts that don't pass secrets at build time), then serves the API.
set -e
if [ -z "$OPENAI_API_KEY" ] && [ -f /etc/secrets/openai_key ]; then
  export OPENAI_API_KEY="$(cat /etc/secrets/openai_key)"
fi
if [ ! -f data/bm25.pkl ] || [ ! -d chroma ]; then
  echo "index missing -> building (needs OPENAI_API_KEY)"
  python -m ingest.build_index
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
