"""
ai/document_processor.py
Extracts and cleans raw text documents from MySQL tables for vector chunking.
"""
import mysql.connector
import sys, os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.config import DB_CONFIG


class DocumentProcessor:

    def __init__(self, db_config: dict = None):
        self.db_cfg = db_config or DB_CONFIG

    def _conn(self):
        return mysql.connector.connect(**self.db_cfg)

    def clean_text(self, text: str) -> str:
        """Clean raw report text."""
        if not text:
            return ""
        # Collapse multiple whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def fetch_all_reports_for_indexing(self) -> list:
        """Fetch all ExaminationReport records with associated metadata for chunking."""
        conn = self._conn()
        cur = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT er.report_id, er.exam_id, er.report_text, er.filed_on, er.filed_by, er.is_admissible,
                       ex.evidence_id, ex.examiner_id, ex.exam_type_id,
                       e.case_id, cc.fir_number, e.description AS evidence_desc,
                       exr.full_name AS examiner_name, fl.lab_name
                FROM ExaminationReport er
                JOIN Examination ex ON er.exam_id=ex.exam_id
                JOIN Evidence e ON ex.evidence_id=e.evidence_id
                JOIN CriminalCase cc ON e.case_id=cc.case_id
                JOIN Examiner exr ON ex.examiner_id=exr.examiner_id
                JOIN ForensicLab fl ON exr.lab_id=fl.lab_id
            """
            cur.execute(sql)
            docs = cur.fetchall()

            processed = []
            for d in docs:
                processed.append({
                    "doc_id": f"RPT_{d['report_id']}",
                    "report_id": d["report_id"],
                    "exam_id": d["exam_id"],
                    "evidence_id": d["evidence_id"],
                    "case_id": d["case_id"],
                    "fir_number": d["fir_number"],
                    "examiner_id": d["examiner_id"],
                    "examiner_name": d["examiner_name"],
                    "lab_name": d["lab_name"],
                    "filed_on": str(d["filed_on"]),
                    "text": self.clean_text(d["report_text"]),
                })

            return processed
        finally:
            cur.close(); conn.close()
