"""
ai/hybrid_retriever.py
Hybrid Retrieval Orchestrator.
Combines Structured SQL Retrieval + Semantic Vector Search + Fact Calculation + 
Provider-Agnostic Vision AI + Cryptographic SHA-256 Byte Verification + Conflict Detection.
"""
import time
import sys, os
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.intent_classifier import IntentClassifier
from ai.entity_extractor import EntityExtractor
from ai.fact_calculator import FactCalculator
from ai.sql_retriever import SQLRetriever
from ai.fulltext_retriever import FullTextRetriever
from ai.vector_retriever import VectorRetriever
from ai.conflict_detector import ConflictDetector
from ai.vision_inspector import VisionInspector
from ai.visual_cross_checker import VisualCrossChecker
from ai.context_builder import ContextBuilder
from ai.grounded_llm import GroundedLLM
from ai.hallucination_guard import HallucinationGuard
from ai.ai_audit import AIAuditLogger


class HybridRetriever:

    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.fact_calculator = FactCalculator()
        self.sql_retriever = SQLRetriever()
        self.fulltext_retriever = FullTextRetriever()
        self.vector_retriever = VectorRetriever()
        self.conflict_detector = ConflictDetector()
        self.vision_inspector = VisionInspector()
        self.visual_cross_checker = VisualCrossChecker()
        self.context_builder = ContextBuilder()
        self.grounded_llm = GroundedLLM()
        self.hallucination_guard = HallucinationGuard()
        self.audit_logger = AIAuditLogger()

    def process_query(self, question: str, officer_id: int = 1, user_role: str = "Junior",
                      retrieval_method: str = "HYBRID") -> dict:
        """Process user question through full multimodal RAG pipeline."""
        start_total = time.time()
        retrieval_start = time.time()

        # 1. Intent classification & entity extraction
        intent = self.intent_classifier.classify(question)
        entities = self.entity_extractor.extract(question)

        eid = entities.get("evidence_id")
        cid = entities.get("case_id")
        fir = entities.get("fir_number")
        badge = entities.get("officer_badge")
        rid = entities.get("report_id")

        # 2. Fact calculation
        facts = {}
        if intent in ("CUSTODY_HISTORY", "ANOMALY_INVESTIGATION"):
            facts["delays"] = self.fact_calculator.calculate_custody_delays(eid)
        if intent in ("INTEGRITY_CHECK", "ANOMALY_INVESTIGATION"):
            facts["expiry"] = self.fact_calculator.calculate_expiry_status(eid)
        if intent in ("EXAMINATION_SUMMARY", "ANOMALY_INVESTIGATION"):
            facts["overdue"] = self.fact_calculator.calculate_overdue_examinations()

        # 2b. Geospatial / Temporal Anomaly Detection (grounded, deterministic)
        if intent in ("ANOMALY_INVESTIGATION", "CUSTODY_HISTORY") and eid:
            facts["geospatial_anomalies"] = self.fact_calculator.calculate_geospatial_anomalies(evidence_id=eid)
        elif intent == "ANOMALY_INVESTIGATION":
            # Run across all evidence if no specific eid
            facts["geospatial_anomalies"] = self.fact_calculator.calculate_geospatial_anomalies()

        # 3. Retrieval dispatch based on method
        sql_data = {}
        vector_results = []
        image_data = {}

        if retrieval_method == "FULLTEXT":
            ft_res = self.fulltext_retriever.retrieve(question, evidence_id=eid, case_id=cid)
            sql_data = {"fulltext_reports": ft_res.get("reports", []), "fulltext_evidence": ft_res.get("evidence", [])}

        elif retrieval_method == "VECTOR":
            v_res = self.vector_retriever.retrieve(question, evidence_id=eid, case_id=cid)
            vector_results = v_res.get("results", [])

        else:
            # PROPOSED HYBRID (SQL + Vector + Vision/Image Integrity)
            if eid:
                sql_data["evidence"] = self.sql_retriever.get_evidence_details(eid, user_role)
                sql_data["custody"] = self.sql_retriever.get_custody_history(eid)
                sql_data["tamper"] = self.sql_retriever.get_tamper_incidents(evidence_id=eid)
                sql_data["examinations"] = self.sql_retriever.get_examination_metadata(eid)
                
                # Retrieve Image Media & SHA-256 byte verification
                image_data = self._retrieve_image_and_integrity(eid, sql_data.get("evidence"))

            if fir or cid:
                sql_data["case_summary"] = self.sql_retriever.get_case_summary_data(fir_number=fir, case_id=cid)

            if badge:
                sql_data["officer"] = self.sql_retriever.get_officer_details(badge)
                sql_data["officer_custody"] = self.sql_retriever.get_officer_custody_history(badge)

            if rid:
                sql_data["report"] = self.sql_retriever.get_report_details(rid)

            # Vector retrieval for semantic report content
            v_res = self.vector_retriever.retrieve(question, evidence_id=eid, case_id=cid, limit=4)
            vector_results = v_res.get("results", [])

            # 3b. Cross-case linkage — triggered by specific intent or keywords
            cross_case_keywords = ["similar", "other case", "cross-case", "related case", "linked", "connection"]
            if eid and (intent in ("ANOMALY_INVESTIGATION", "EXAMINATION_SUMMARY") or
                        any(kw in question.lower() for kw in cross_case_keywords)):
                # Get authorized case IDs for this user's RBAC role
                authorized_ids = self._get_authorized_case_ids(officer_id, user_role)
                # Use the question text as the search chunk for cross-case linkage
                search_chunk = question
                # If we have a specific evidence, use its report text as richer signal
                if vector_results:
                    search_chunk = vector_results[0].get("text", question)
                facts["cross_case_links"] = self.vector_retriever.find_potential_links(
                    evidence_id=eid,
                    text_chunk=search_chunk,
                    top_k=3,
                    authorized_case_ids=authorized_ids,
                )

        retrieval_latency_ms = int((time.time() - retrieval_start) * 1000)

        # 4. Conflict detection
        conflicts = self.conflict_detector.detect_conflicts(sql_data, vector_results)

        # 5. Build validated context package
        context_pkg = self.context_builder.build_context(
            intent=intent,
            entities=entities,
            sql_data=sql_data,
            facts=facts,
            vector_results=vector_results,
            conflicts=conflicts,
            image_data=image_data,
            user_role=user_role,
            question=question
        )
        # Stash facts for why_explainer provenance
        context_pkg["facts"] = facts

        # 6. LLM Generation
        llm_res = self.grounded_llm.generate(question, context_pkg)
        answer = llm_res.get("answer", "")

        # 7. Hallucination Guard Check
        h_check = self.hallucination_guard.validate_answer(answer, context_pkg)

        total_latency_ms = int((time.time() - start_total) * 1000)

        # 8. AI Audit Logging
        query_id = self.audit_logger.log_query(
            officer_id=officer_id,
            question=question,
            intent=intent,
            entities=entities,
            retrieval_method=retrieval_method,
            sql_sources=context_pkg.get("sources", []),
            vector_sources=[{"chunk_id": v["chunk_id"], "score": v["score"]} for v in vector_results],
            retrieval_score=1.0 if (sql_data or vector_results or image_data) else 0.0,
            conflict_detected=conflicts.get("conflict_detected", False),
            conflict_details=conflicts.get("summary", ""),
            model_used=llm_res.get("model_used", "hybrid_engine"),
            generated_answer=answer,
            response_latency_ms=total_latency_ms,
            retrieval_latency_ms=retrieval_latency_ms,
            hallucination_flag=h_check.get("is_valid", True) is False,
            status=llm_res.get("status", "success")
        )

        return {
            "query_id": query_id,
            "question": question,
            "intent": intent,
            "entities": entities,
            "retrieval_method": retrieval_method,
            "answer": answer,
            "sources": context_pkg.get("sources", []),
            "conflict_warning": context_pkg.get("conflict_warning", ""),
            "hallucination_flag": h_check.get("flag", 0),
            "response_latency_ms": total_latency_ms,
            "retrieval_latency_ms": retrieval_latency_ms,
            "status": llm_res.get("status", "success"),
            "context_package": context_pkg,
        }

    def _get_authorized_case_ids(self, officer_id: int, user_role: str) -> list:
        """
        Returns list of case_ids the current officer is authorized to access.
        Admin/Supervisor: all cases.
        Junior/Senior: only cases from their department's police station.
        """
        try:
            from database.db_util import qry as db_qry
        except ImportError:
            try:
                from backend.app import qry as db_qry
            except ImportError:
                return None  # None means no filter applied — fail open for fallback mode

        try:
            if user_role in ("Admin", "Supervisor"):
                # Admin sees all cases
                rows = db_qry("SELECT case_id FROM CriminalCase")
                return [r["case_id"] for r in rows] if rows else []
            else:
                # Junior/Senior: cases from their department's police station
                officer = db_qry(
                    "SELECT o.department_id, d.dept_type FROM Officer o JOIN Department d ON o.department_id=d.dept_id WHERE o.officer_id=%s",
                    (officer_id,), one=True
                )
                if not officer:
                    return []
                dept_id = officer["department_id"]
                # Cases at police stations linked to this department
                rows = db_qry(
                    """SELECT DISTINCT cc.case_id FROM CriminalCase cc
                       JOIN PoliceStation ps ON cc.police_station_id = ps.station_id
                       WHERE cc.investigating_officer_id IN (
                           SELECT officer_id FROM Officer WHERE department_id = %s
                       )""",
                    (dept_id,)
                )
                return [r["case_id"] for r in rows] if rows else []
        except Exception as e:
            print(f"[HybridRetriever] Could not determine authorized cases: {e}")
            return None  # None = no filter (safe fallback)

    def _retrieve_image_and_integrity(self, eid: int, ev_details: dict = None) -> dict:

        """Retrieves EvidenceMedia record, verifies byte SHA-256, runs Vision AI & Cross-Checker."""
        try:
            from database.db_util import qry  # Re-use DB helper
        except ImportError:
            try:
                from backend.app import qry
            except ImportError:
                return {}

        media_rec = qry("SELECT * FROM EvidenceMedia WHERE evidence_id = %s ORDER BY taken_at DESC LIMIT 1", (eid,), one=True)
        if not media_rec or not media_rec.get("file_name"):
            return {
                "sha256_integrity": {
                    "evidence_id": f"E{eid:03d}",
                    "integrity": "NO_IMAGE",
                    "message": "No photographic evidence available for this evidence item."
                },
                "vision_analysis": {
                    "status": "NO_IMAGE",
                    "visible_condition": "No photograph available."
                },
                "visual_cross_check": {
                    "is_consistent": True,
                    "warnings": []
                }
            }

        # Locate image file on disk
        fname = media_rec["file_name"]
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        fpath = os.path.join(backend_dir, "backend", "static", "evidence_photos", fname)

        stored_hash = media_rec.get("sha256_hash")
        curr_hash = None
        integrity = "NO_IMAGE"

        if os.path.isfile(fpath):
            with open(fpath, "rb") as f:
                curr_hash = hashlib.sha256(f.read()).hexdigest()
            if stored_hash and curr_hash == stored_hash:
                integrity = "INTACT"
            elif stored_hash:
                integrity = "COMPROMISED"
            else:
                integrity = "UNVERIFIED"
                stored_hash = curr_hash

        sha_result = {
            "evidence_id": f"E{eid:03d}",
            "file_name": fname,
            "file_path": media_rec.get("file_path", f"evidence_photos/{fname}"),
            "stored_hash": stored_hash,
            "current_hash": curr_hash,
            "integrity": integrity
        }

        # Run Vision Inspector
        expected_desc = ev_details.get("description", "") if isinstance(ev_details, dict) else ""
        vision_result = self.vision_inspector.analyze_image(fpath, eid, expected_desc)

        # Run Visual Cross Checker
        cross_check_result = self.visual_cross_checker.cross_check(eid, ev_details or {}, vision_result, sha_result)

        return {
            "sha256_integrity": sha_result,
            "vision_analysis": vision_result,
            "visual_cross_check": cross_check_result
        }
