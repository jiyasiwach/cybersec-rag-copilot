import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()
RESULTS = Path(__file__).resolve().parents[2] / "evals" / "results.json"


@router.get("/api/eval/results")
def eval_results() -> dict:
    if not RESULTS.is_file():
        raise HTTPException(status_code=404, detail="No eval results yet — run `python -m evals.run_eval`.")
    return json.loads(RESULTS.read_text())
