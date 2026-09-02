"""
ai/vector_retriever.py
Baseline B — Vector-Only RAG Retriever.
Retrieves context purely via semantic vector search in ChromaDB.
Also provides cross-case evidence linkage via find_potential_links().
"""
import sys
import os
import mysql.connector

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.vector_store import VectorStore
from ai.config import DB_CONFIG

# Similarity threshold for cross-case potential links (conservative)
CROSS_CASE_SIMILARITY_THRESHOLD = 0.70


class VectorRetriever:

    def __init__(self, vector_store: VectorStore = None):
        self.vector_store = vector_store or VectorStore()

    def retrieve(self, query: str, evidence_id: int = None, case_id: int = None, limit: int = 5) -> dict:
        """Baseline B retrieval entry point. Pure semantic similarity search."""
        results = self.vector_store.search(
            query=query,
            limit=limit,
            evidence_id=evidence_id,
            case_id=case_id
        )

        return {
            "method": "VECTOR",
            "results": results,
            "count": len(results),
        }

    def find_potential_links(
        self,
        evidence_id: int,
        text_chunk: str,
        top_k: int = 5,
        similarity_threshold: float = CROSS_CASE_SIMILARITY_THRESHOLD,
        authorized_case_ids: list = None,
    ) -> list:
        """
        Search ChromaDB for semantically similar examination report chunks
        from OTHER cases that the authenticated user is authorized to access.

        RBAC enforcement:
          - authorized_case_ids must be provided from the backend (derived from JWT role).
          - The current evidence's case is ALWAYS excluded.
          - Vector results are verified against the MySQL database before being returned.
          - Only results above similarity_threshold are returned.
          - Results are labeled as POTENTIAL SEMANTIC LINK only.

        Returns a list of potential link dicts.
        """
        if not text_chunk or not text_chunk.strip():
            return []

        # Get the current evidence's case_id to exclude it
        current_case_id = self._get_case_id_for_evidence(evidence_id)

        # Search vector store without filtering (we filter below by authorized_case_ids)
        raw_results = self.vector_store.search(query=text_chunk, limit=top_k * 3)

        potential_links = []
        seen_evidence_ids = set()

        for result in raw_results:
            score = result.get("score", 0.0)
            if score < similarity_threshold:
                continue

            meta = result.get("metadata", {})
            result_evidence_id = meta.get("evidence_id")
            result_case_id = meta.get("case_id")
            result_report_id = meta.get("report_id")

            # Skip same evidence
            if result_evidence_id == evidence_id:
                continue

            # Skip current case
            if current_case_id and result_case_id == current_case_id:
                continue

            # RBAC: Skip cases not in authorized list (when list is provided)
            if authorized_case_ids is not None and result_case_id not in authorized_case_ids:
                continue

            # Skip duplicates (multiple chunks from same evidence)
            if result_evidence_id in seen_evidence_ids:
                continue

            # Verify against MySQL database (ground truth)
            db_record = self._verify_against_db(result_evidence_id, result_case_id, result_report_id)
            if not db_record:
                # Vector record has no backing DB record — skip (stale index)
                continue

            seen_evidence_ids.add(result_evidence_id)

            potential_links.append({
                "source_evidence_id": evidence_id,
                "linked_evidence_id": result_evidence_id,
                "linked_case_id": result_case_id,
                "linked_report_id": result_report_id,
                "similarity_score": round(score, 4),
                "link_type": "POTENTIAL_SEMANTIC_LINK",
                "db_verified": True,
                "evidence_description": db_record.get("evidence_description", ""),
                "case_fir": db_record.get("fir_number", ""),
                "report_summary": db_record.get("report_excerpt", ""),
                "examiner_name": meta.get("examiner_name", ""),
                "lab_name": meta.get("lab_name", ""),
                "filed_on": meta.get("filed_on", ""),
                "authorized_scope": f"case_ids: {authorized_case_ids}",
                "explanation": (
                    f"Potential cross-case linkage detected. Semantic similarity score: {round(score, 4)}. "
                    f"This is a supporting signal based on vector similarity of forensic examination report text. "
                    f"It is NOT forensic proof of a confirmed case connection."
                ),
            })

            if len(potential_links) >= top_k:
                break

        return potential_links

    def _get_case_id_for_evidence(self, evidence_id: int):
        """Returns the case_id for a given evidence_id from the authoritative database."""
        if not evidence_id:
            return None
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cur = conn.cursor(dictionary=True)
            try:
                cur.execute("SELECT case_id FROM Evidence WHERE evidence_id = %s", (evidence_id,))
                row = cur.fetchone()
                return row["case_id"] if row else None
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            print(f"[VectorRetriever] DB error getting case_id: {e}")
            return None

    def _verify_against_db(self, evidence_id, case_id, report_id) -> dict:
        """
        Verifies that the vector result corresponds to a real record in MySQL.
        Returns a dict with key fields, or None if not found (stale index).
        """
        if not evidence_id:
            return None
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cur = conn.cursor(dictionary=True)
            try:
                cur.execute(
                    """SELECT e.evidence_id, e.description AS evidence_description,
                              cc.case_id, cc.fir_number, er.report_text
                       FROM Evidence e
                       JOIN CriminalCase cc ON e.case_id = cc.case_id
                       LEFT JOIN Examination ex ON ex.evidence_id = e.evidence_id
                       LEFT JOIN ExaminationReport er ON er.exam_id = ex.exam_id
                       WHERE e.evidence_id = %s
                       LIMIT 1""",
                    (evidence_id,)
                )
                row = cur.fetchone()
                if not row:
                    return None
                # Truncate report text to a short excerpt
                report_text = row.get("report_text") or ""
                row["report_excerpt"] = report_text[:200] + "..." if len(report_text) > 200 else report_text
                return row
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            print(f"[VectorRetriever] DB verification error: {e}")
            return None
