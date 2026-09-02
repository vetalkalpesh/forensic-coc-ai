"""
evaluation/metrics.py
Retrieval and generation metrics implementation:
  - Recall@K
  - Precision@K
  - Mean Reciprocal Rank (MRR)
  - nDCG@K
  - Answer Faithfulness & Relevance (cosine / string similarity)
  - Hallucination Rate
  - Latency & Indexing time
"""
import math


# ── RETRIEVAL METRICS ─────────────────────────────────────────

def recall_at_k(retrieved_ids: list, relevant_ids: list, k: int = 5) -> float:
    """Calculate Recall@K: fraction of relevant documents retrieved in top-K."""
    if not relevant_ids:
        return None
    top_k = retrieved_ids[:k]
    hits = len(set(top_k) & set(relevant_ids))
    return hits / len(relevant_ids)


def precision_at_k(retrieved_ids: list, relevant_ids: list, k: int = 5) -> float:
    """Calculate Precision@K: fraction of top-K retrieved documents that are relevant."""
    if not relevant_ids:
        return None
    if k == 0 or not retrieved_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = len(set(top_k) & set(relevant_ids))
    return hits / k


def mean_reciprocal_rank(retrieved_ids: list, relevant_ids: list) -> float:
    """Calculate MRR: reciprocal rank of the first relevant document in retrieved list."""
    if not relevant_ids:
        return None
    if not retrieved_ids:
        return 0.0
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved_ids: list, relevant_ids: list, k: int = 5) -> float:
    """Calculate normalized Discounted Cumulative Gain (nDCG@K)."""
    if not relevant_ids:
        return None
    if not retrieved_ids:
        return 0.0

    top_k = retrieved_ids[:k]

    # DCG calculation
    dcg = 0.0
    for i, doc_id in enumerate(top_k):
        rel = 1.0 if doc_id in relevant_ids else 0.0
        dcg += rel / math.log2(i + 2)

    # Ideal DCG calculation
    idcg = 0.0
    for i in range(min(len(relevant_ids), k)):
        idcg += 1.0 / math.log2(i + 2)

    return (dcg / idcg) if idcg > 0 else 0.0


# ── GENERATION & SYSTEM METRICS ────────────────────────────────

def answer_faithfulness(generated_answer: str, ground_truth: str) -> float:
    """Compute lexical/word overlap faithfulness score between answer and ground truth."""
    if not generated_answer or not ground_truth:
        return 0.0
    ans_words = set(generated_answer.lower().split())
    gt_words = set(ground_truth.lower().split())
    if not gt_words:
        return 1.0
    overlap = len(ans_words & gt_words)
    return round(overlap / len(gt_words), 4)


def answer_relevance(generated_answer: str, question: str) -> float:
    """Compute keyword coverage relevance score between answer and question."""
    if not generated_answer or not question:
        return 0.0
    q_words = [w.lower() for w in question.split() if len(w) > 3]
    if not q_words:
        return 1.0
    ans_lower = generated_answer.lower()
    hits = sum(1 for w in q_words if w in ans_lower)
    return round(hits / len(q_words), 4)


def hallucination_rate(evaluation_results: list) -> float:
    """Compute overall hallucination rate across evaluation question results."""
    if not evaluation_results:
        return 0.0
    flagged = sum(1 for r in evaluation_results if r.get("hallucination_flag", 0) == 1)
    return round(flagged / len(evaluation_results), 4)
