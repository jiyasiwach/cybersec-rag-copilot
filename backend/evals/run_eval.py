"""Run the evaluation and write evals/results.json.

    python -m evals.run_eval

Measures: Hit@5 + MRR per retrieval mode, faithfulness + citation accuracy for hybrid answers
(LLM-as-judge), guardrail block rate on attacks and false-positive rate on normal questions,
average latency and cost. Prints a summary table.
"""
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.guardrail import guard
from app.llm.openai_provider import get_provider
from app.metrics import est_cost_usd
from app.rag.generator import new_result, stream_answer
from app.rag.retriever import Hit, Mode, get_retriever

HERE = Path(__file__).resolve().parent
MODES: list[Mode] = ["vector", "bm25", "hybrid"]

JUDGE_SYSTEM = """You are a strict grader. You get numbered context passages, a question and an answer.
Return JSON: {"faithfulness": <0..1>, "citation_accuracy": <0..1>, "notes": "<short>"}
- faithfulness: fraction of factual claims in the answer that are supported by the passages (1.0 = all supported). An answer that says the knowledge base does not contain the information is faithful if that is true.
- citation_accuracy: fraction of [n] citations that point to a passage actually supporting the adjacent claim."""


def hit_rank(hits: list[Hit], expected: list[str]) -> int | None:
    exp = {e.upper() for e in expected}
    for h in hits:
        if h.chunk.doc_id.upper() in exp:
            return h.rank
    return None


def judge(question: str, hits: list[Hit], answer: str) -> dict:
    ctx = "\n\n".join(f"[{h.rank}] {h.chunk.text}" for h in hits)
    data = get_provider().complete_json(JUDGE_SYSTEM, f"<passages>\n{ctx}\n</passages>\n\n<question>{question}</question>\n\n<answer>\n{answer}\n</answer>", max_tokens=120)
    return {"faithfulness": float(data.get("faithfulness", 0)), "citation_accuracy": float(data.get("citation_accuracy", 0))}


def main() -> None:
    spec = json.loads((HERE / "questions.json").read_text())
    retriever = get_retriever()
    t_start = time.time()

    # ---- retrieval ----
    retrieval: dict[str, dict[str, float]] = {}
    per_question: list[dict] = []
    for mode in MODES:
        hits_at_5, rr = 0, 0.0
        for q in spec["questions"]:
            rank = hit_rank(retriever.search(q["question"], mode, 5), q["expected_doc_ids"])
            hits_at_5 += rank is not None
            rr += 1 / rank if rank else 0
            if mode == "hybrid":
                per_question.append({"id": q["id"], "hybrid_rank": rank})
        n = len(spec["questions"])
        retrieval[mode] = {"hit_at_5": round(hits_at_5 / n, 3), "mrr": round(rr / n, 3)}
        print(f"retrieval/{mode:7s} Hit@5={retrieval[mode]['hit_at_5']:.2f}  MRR={retrieval[mode]['mrr']:.3f}")

    # ---- answers (hybrid) ----
    faith, cite, latencies, costs = [], [], [], []
    for q in spec["questions"]:
        t0 = time.perf_counter()
        hits = retriever.search(q["question"], "hybrid", settings.top_k)
        result = new_result()
        answer = "".join(stream_answer(q["question"], hits, result))
        latencies.append((time.perf_counter() - t0) * 1000)
        costs.append(est_cost_usd(result.usage.prompt_tokens, result.usage.completion_tokens))
        j = judge(q["question"], hits, answer)
        faith.append(j["faithfulness"])
        cite.append(j["citation_accuracy"])
        n_cites = len(set(re.findall(r"\[(\d+)\]", answer)))
        print(f"  {q['id']} faith={j['faithfulness']:.2f} cite={j['citation_accuracy']:.2f} cites={n_cites} {latencies[-1]:.0f}ms")

    # ---- guardrail ----
    blocked = sum(guard.check(a["question"]).blocked for a in spec["attacks"])
    off_topic_blocked = sum(guard.check(o["question"]).blocked for o in spec["off_topic"])
    false_pos = sum(guard.check(q["question"]).blocked for q in spec["questions"])

    results = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
        "counts": {"questions": len(spec["questions"]), "attacks": len(spec["attacks"]), "off_topic": len(spec["off_topic"])},
        "retrieval": retrieval,
        "answers": {"faithfulness": round(sum(faith) / len(faith), 3), "citation_accuracy": round(sum(cite) / len(cite), 3)},
        "guardrail": {
            "block_rate": round(blocked / len(spec["attacks"]), 3),
            "off_topic_block_rate": round(off_topic_blocked / len(spec["off_topic"]), 3),
            "false_positive_rate": round(false_pos / len(spec["questions"]), 3),
        },
        "avg_latency_ms": round(sum(latencies) / len(latencies)),
        "avg_cost_usd": round(sum(costs) / len(costs), 6),
        "per_question": per_question,
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2))

    print("\n==== summary ====")
    print(f"{'mode':8s} {'Hit@5':>6s} {'MRR':>6s}")
    for m in MODES:
        print(f"{m:8s} {retrieval[m]['hit_at_5']:6.2f} {retrieval[m]['mrr']:6.3f}")
    a, g = results["answers"], results["guardrail"]
    print(f"faithfulness {a['faithfulness']:.2f}   citation accuracy {a['citation_accuracy']:.2f}")
    print(f"attacks blocked {g['block_rate']:.0%}   off-topic blocked {g['off_topic_block_rate']:.0%}   false positives {g['false_positive_rate']:.0%}")
    print(f"avg latency {results['avg_latency_ms']} ms   avg cost ${results['avg_cost_usd']:.5f}   eval took {time.time() - t_start:.0f}s")
    print(f"wrote {HERE / 'results.json'}")


if __name__ == "__main__":
    main()
