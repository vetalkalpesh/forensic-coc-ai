"""
ai/fulltext_retriever.py
Baseline A — MySQL FULLTEXT keyword retrieval engine.
Queries MySQL FULLTEXT indexes on ExaminationReport.report_text and Evidence.description.
"""
import mysql.connector
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.config import DB_CONFIG, FULLTEXT_MIN_RELEVANCE


class FullTextRetriever:

    def __init__(self, db_config: dict = None):
        self.db_cfg = db_config or DB_CONFIG

    def _conn(self):
        return mysql.connector.connect(**self.db_cfg)

    def search_reports(self, query_text: str, evidence_id: int = None, case_id: int = None, limit: int = 5) -> list:
        """Search ExaminationReport table using MATCH() AGAINST()."""
        conn = self._conn()
        cur = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT er.report_id, er.exam_id, er.report_text, er.filed_on, er.is_admissible,
                       ex.evidence_id, ex.examiner_id, e.case_id,
                       MATCH(er.report_text) AGAINST(%s IN NATURAL LANGUAGE MODE) AS relevance_score
                FROM ExaminationReport er
                JOIN Examination ex ON er.exam_id=ex.exam_id
                JOIN Evidence e ON ex.evidence_id=e.evidence_id
                WHERE MATCH(er.report_text) AGAINST(%s IN NATURAL LANGUAGE MODE) > %s
            """
            params = [query_text, query_text, FULLTEXT_MIN_RELEVANCE]

            if evidence_id:
                sql += " AND ex.evidence_id = %s"
                params.append(evidence_id)
            if case_id:
                sql += " AND e.case_id = %s"
                params.append(case_id)

            sql += " ORDER BY relevance_score DESC LIMIT %s"
            params.append(limit)

            cur.execute(sql, tuple(params))
            return cur.fetchall()
        finally:
            cur.close(); conn.close()

    def search_evidence_descriptions(self, query_text: str, limit: int = 5) -> list:
        """Search Evidence table using MATCH() AGAINST()."""
        conn = self._conn()
        cur = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT e.evidence_id, e.description, e.current_status, e.case_id,
                       MATCH(e.description) AGAINST(%s IN NATURAL LANGUAGE MODE) AS relevance_score
                FROM Evidence e
                WHERE MATCH(e.description) AGAINST(%s IN NATURAL LANGUAGE MODE) > %s
                ORDER BY relevance_score DESC LIMIT %s
            """
            cur.execute(sql, (query_text, query_text, FULLTEXT_MIN_RELEVANCE, limit))
            return cur.fetchall()
        finally:
            cur.close(); conn.close()

    def retrieve(self, query_text: str, evidence_id: int = None, case_id: int = None, limit: int = 5) -> dict:
        """Baseline A retrieval entry point. Returns full-text matched reports and evidence descriptions."""
        reports = self.search_reports(query_text, evidence_id, case_id, limit)
        evidence = self.search_evidence_descriptions(query_text, limit)

        return {
            "method": "FULLTEXT",
            "reports": reports,
            "evidence": evidence,
            "count": len(reports) + len(evidence),
        }
