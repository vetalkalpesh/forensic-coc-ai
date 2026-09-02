"""
ai/ai_audit.py
Logs every AI query into the MySQL AIQueryAuditLog table for transparency and security auditing.
"""
import mysql.connector
import json
import uuid
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.config import DB_CONFIG


class AIAuditLogger:

    def __init__(self, db_config: dict = None):
        self.db_cfg = db_config or DB_CONFIG

    def _conn(self):
        return mysql.connector.connect(**self.db_cfg)

    def log_query(
        self,
        officer_id: int,
        question: str,
        intent: str,
        entities: dict,
        retrieval_method: str,
        sql_sources: list,
        vector_sources: list,
        retrieval_score: float,
        conflict_detected: bool,
        conflict_details: str,
        model_used: str,
        generated_answer: str,
        response_latency_ms: int,
        retrieval_latency_ms: int,
        hallucination_flag: bool,
        status: str = "success"
    ) -> str:
        """Insert query record into AIQueryAuditLog table. Returns query_id UUID."""
        query_id = str(uuid.uuid4())
        try:
            conn = self._conn()
            cur = conn.cursor()
            try:
                sql = """
                    INSERT INTO AIQueryAuditLog (
                        query_id, officer_id, original_question, detected_intent,
                        extracted_entities, retrieval_method, sql_sources, vector_sources,
                        retrieval_score, conflict_detected, conflict_details, model_used,
                        generated_answer, response_latency_ms, retrieval_latency_ms,
                        hallucination_flag, status
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
                cur.execute(sql, (
                    query_id, officer_id, question, intent,
                    json.dumps(entities or {}), retrieval_method,
                    json.dumps(sql_sources or []), json.dumps(vector_sources or []),
                    retrieval_score, 1 if conflict_detected else 0, conflict_details or "",
                    model_used, (generated_answer or "")[:65000], response_latency_ms, retrieval_latency_ms,
                    1 if hallucination_flag else 0, status
                ))
                conn.commit()
            finally:
                cur.close(); conn.close()
            return query_id
        except Exception as e:
            print(f"[AIAuditLogger] DB Notice: Failed to log audit record ({e})")
            return query_id

    def get_query_log(self, query_id: str) -> dict:
        """Fetch query audit log by query_id."""
        try:
            conn = self._conn()
            cur = conn.cursor(dictionary=True)
            try:
                cur.execute("SELECT * FROM AIQueryAuditLog WHERE query_id = %s", (query_id,))
                res = cur.fetchone()
                return res if res else {}
            finally:
                cur.close(); conn.close()
        except mysql.connector.Error as e:
            print(f"[AIAuditLogger] DB Notice: {e}")
            return {}
