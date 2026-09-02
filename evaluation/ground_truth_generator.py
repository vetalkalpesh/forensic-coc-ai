"""
evaluation/ground_truth_generator.py
Generates SQL-verified ground-truth answers for the evaluation question set.
"""
import mysql.connector
import json
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.config import DB_CONFIG


class GroundTruthGenerator:

    def __init__(self, db_config: dict = None):
        self.db_cfg = db_config or DB_CONFIG

    def _conn(self):
        return mysql.connector.connect(**self.db_cfg)

    def generate_ground_truths(self, questions_file: str = "evaluation/questions.json") -> list:
        """Enriches question json dataset with database-verified ground truth answers."""
        if not os.path.exists(questions_file):
            from evaluation.question_generator import QuestionGenerator
            qg = QuestionGenerator()
            questions = qg.generate_all_questions(questions_file)
        else:
            with open(questions_file, "r", encoding="utf-8") as f:
                questions = json.load(f)

        conn = self._conn()
        cur = conn.cursor(dictionary=True)

        try:
            for q in questions:
                cat = q.get("category")
                entities = q.get("expected_entities", [])

                if cat == "unsupported_queries":
                    q["ground_truth"] = "The available verified records and forensic reports do not contain sufficient information to answer this question."

                elif cat == "evidence_status" and entities:
                    eid_str = entities[0].replace("E", "")
                    try:
                        eid = int(eid_str)
                        cur.execute("SELECT description, current_status FROM Evidence WHERE evidence_id = %s", (eid,))
                        res = cur.fetchone()
                        if res:
                            q["ground_truth"] = f"Evidence E{eid:03d} ({res['description']}) current status is '{res['current_status']}'."
                    except ValueError:
                        pass

                elif cat == "tamper_investigation" and entities:
                    eid_str = entities[0].replace("E", "")
                    try:
                        eid = int(eid_str)
                        cur.execute("SELECT severity, description FROM TamperIncident WHERE evidence_id = %s", (eid,))
                        res = cur.fetchall()
                        if res:
                            q["ground_truth"] = f"Tamper incidents for E{eid:03d}: " + "; ".join([f"{r['severity']} severity: {r['description']}" for r in res])
                        else:
                            q["ground_truth"] = f"No tamper incidents recorded for evidence E{eid:03d}."
                    except ValueError:
                        pass

            with open(questions_file, "w", encoding="utf-8") as f:
                json.dump(questions, f, indent=2)

            print(f"[GroundTruthGenerator] Ground truths verified & updated for {len(questions)} questions.")
            return questions
        finally:
            cur.close(); conn.close()


if __name__ == "__main__":
    gtg = GroundTruthGenerator()
    gtg.generate_ground_truths()
