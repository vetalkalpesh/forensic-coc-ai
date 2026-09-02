"""
evaluation/evaluate.py
Main Evaluation Framework runner.
Compares Baseline A (FULLTEXT), Baseline B (VECTOR), and PROPOSED (HYBRID) RAG across
all 150-300 ground-truth questions and computes all evaluation metrics.
"""
import argparse
import json
import time
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.hybrid_retriever import HybridRetriever
from evaluation.metrics import (
    recall_at_k, precision_at_k, mean_reciprocal_rank, ndcg_at_k,
    answer_faithfulness, answer_relevance, hallucination_rate
)


def run_evaluation(questions_file: str = "evaluation/questions.json",
                   output_dir: str = "evaluation/results") -> dict:
    """Executes systematic evaluation across all 3 retrieval baselines."""

    if not os.path.exists(questions_file) or os.path.getsize(questions_file) == 0:
        from evaluation.question_generator import QuestionGenerator
        qg = QuestionGenerator()
        qg.generate_all_questions(questions_file)

    with open(questions_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    orchestrator = HybridRetriever()

    methods = ["FULLTEXT", "VECTOR", "HYBRID"]
    results = {m: [] for m in methods}

    print("=" * 65)
    print("  HYBRID RAG FORENSIC INTELLIGENCE PLATFORM — EVALUATION")
    print(f"  Total Question Set: {len(questions)} programmatically generated questions")
    print("  Retrieval Baselines: FULLTEXT (A), VECTOR (B), HYBRID (Proposed)")
    print("=" * 65)

    start_eval = time.time()

    for idx, q_obj in enumerate(questions, start=1):
        qid = q_obj["id"]
        q_text = q_obj["question"]
        gt = q_obj.get("ground_truth", "")

        print(f"\rEvaluating [{idx}/{len(questions)}] Question ID: {qid}...", end="", flush=True)

        for method in methods:
            try:
                res = orchestrator.process_query(
                    question=q_text,
                    officer_id=1,
                    user_role="Admin",
                    retrieval_method=method
                )

                ans = res.get("answer", "")
                sources = [s.get("id") for s in res.get("sources", [])]
                expected_src = q_obj.get("expected_entities", [])

                rec = recall_at_k(sources, expected_src, k=5)
                prec = precision_at_k(sources, expected_src, k=5)
                mrr = mean_reciprocal_rank(sources, expected_src)
                ndcg = ndcg_at_k(sources, expected_src, k=5)

                faith = answer_faithfulness(ans, gt)
                rel = answer_relevance(ans, q_text)
                h_flag = res.get("hallucination_flag", 0)

                results[method].append({
                    "id": qid,
                    "category": q_obj.get("category"),
                    "question": q_text,
                    "method": method,
                    "answer": ans,
                    "recall_at_5": rec,
                    "precision_at_5": prec,
                    "mrr": mrr,
                    "ndcg_at_5": ndcg,
                    "faithfulness": faith,
                    "relevance": rel,
                    "hallucination_flag": h_flag,
                    "retrieval_latency_ms": res.get("retrieval_latency_ms", 0),
                    "total_latency_ms": res.get("response_latency_ms", 0),
                })
            except Exception as e:
                print(f"\n[ERR] {method} failed on {qid}: {e}")

    print("\n\n" + "=" * 65)
    print("  EVALUATION SUMMARY RESULTS")
    print("=" * 65)

    summary_stats = {}
    category_stats = {}

    for method in methods:
        res_list = results[method]
        if not res_list:
            continue

        rec_vals = [r["recall_at_5"] for r in res_list if r["recall_at_5"] is not None]
        prec_vals = [r["precision_at_5"] for r in res_list if r["precision_at_5"] is not None]
        mrr_vals = [r["mrr"] for r in res_list if r["mrr"] is not None]
        ndcg_vals = [r["ndcg_at_5"] for r in res_list if r["ndcg_at_5"] is not None]

        avg_rec = sum(rec_vals) / len(rec_vals) if rec_vals else 0.0
        avg_prec = sum(prec_vals) / len(prec_vals) if prec_vals else 0.0
        avg_mrr = sum(mrr_vals) / len(mrr_vals) if mrr_vals else 0.0
        avg_ndcg = sum(ndcg_vals) / len(ndcg_vals) if ndcg_vals else 0.0

        avg_faith = sum(r["faithfulness"] for r in res_list) / len(res_list)
        avg_rel = sum(r["relevance"] for r in res_list) / len(res_list)
        h_rate = hallucination_rate(res_list)
        avg_lat = sum(r["total_latency_ms"] for r in res_list) / len(res_list)

        summary_stats[method] = {
            "mean_recall_at_5": round(avg_rec, 4),
            "mean_precision_at_5": round(avg_prec, 4),
            "mrr": round(avg_mrr, 4),
            "ndcg_at_5": round(avg_ndcg, 4),
            "faithfulness": round(avg_faith, 4),
            "relevance": round(avg_rel, 4),
            "hallucination_rate": round(h_rate, 4),
            "mean_latency_ms": round(avg_lat, 2),
        }

        # Category level aggregation
        cat_map = {}
        for r in res_list:
            cat = r.get("category", "general")
            if cat not in cat_map:
                cat_map[cat] = []
            cat_map[cat].append(r)

        category_stats[method] = {}
        for cat, c_items in cat_map.items():
            c_rec = [r["recall_at_5"] for r in c_items if r["recall_at_5"] is not None]
            c_prec = [r["precision_at_5"] for r in c_items if r["precision_at_5"] is not None]
            c_mrr = [r["mrr"] for r in c_items if r["mrr"] is not None]
            category_stats[method][cat] = {
                "count": len(c_items),
                "recall_at_5": round(sum(c_rec)/len(c_rec), 4) if c_rec else None,
                "precision_at_5": round(sum(c_prec)/len(c_prec), 4) if c_prec else None,
                "mrr": round(sum(c_mrr)/len(c_mrr), 4) if c_mrr else None,
                "mean_latency_ms": round(sum(r["total_latency_ms"] for r in c_items)/len(c_items), 2),
            }

        print(f"\n  Baseline Method: {method}")
        print(f"    Recall@5:           {avg_rec:.4f}  (calculated over {len(rec_vals)} target-bearing queries)")
        print(f"    Precision@5:        {avg_prec:.4f}")
        print(f"    MRR:                {avg_mrr:.4f}")
        print(f"    nDCG@5:             {avg_ndcg:.4f}")
        print(f"    Answer Faithfulness:{avg_faith:.4f}")
        print(f"    Answer Relevance:   {avg_rel:.4f}")
        print(f"    Hallucination Rate: {h_rate:.4f}")
        print(f"    Mean Latency:       {avg_lat:.2f} ms")

    print("\n" + "=" * 65)
    print("  CATEGORY BREAKDOWN (RECALL@5 / MRR)")
    print("=" * 65)
    all_cats = list(category_stats.get("HYBRID", {}).keys())
    print(f"  {'Category':<25} | {'FULLTEXT':<16} | {'VECTOR':<16} | {'HYBRID':<16}")
    print("  " + "-" * 75)
    for cat in all_cats:
        ft_rec = category_stats.get("FULLTEXT", {}).get(cat, {}).get("recall_at_5")
        vec_rec = category_stats.get("VECTOR", {}).get(cat, {}).get("recall_at_5")
        hyb_rec = category_stats.get("HYBRID", {}).get(cat, {}).get("recall_at_5")
        ft_str = f"{ft_rec:.2f}" if ft_rec is not None else "N/A"
        vec_str = f"{vec_rec:.2f}" if vec_rec is not None else "N/A"
        hyb_str = f"{hyb_rec:.2f}" if hyb_rec is not None else "N/A"
        print(f"  {cat:<25} | Recall: {ft_str:<8} | Recall: {vec_str:<8} | Recall: {hyb_str:<8}")

    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "E1_retrieval_comparison.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"summary": summary_stats, "category_breakdown": category_stats, "detailed_results": results}, f, indent=2)

    print("\n" + "=" * 65)
    print(f"  Results saved to: {out_file}")
    print(f"  Total Evaluation Time: {round(time.time() - start_eval, 2)}s")
    print("=" * 65)

    return summary_stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", default="evaluation/questions.json")
    parser.add_argument("--outdir", default="evaluation/results")
    args = parser.parse_args()

    run_evaluation(args.questions, args.outdir)
