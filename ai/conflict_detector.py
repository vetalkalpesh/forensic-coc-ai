"""
ai/conflict_detector.py
Detects conflicts between current authoritative MySQL database state and historical report text.
Enforces Rule 7: Explains conflicts, prioritizes MySQL DB as single source of truth,
and preserves report provenance.
"""

class ConflictDetector:

    def detect_conflicts(self, sql_context: dict, vector_chunks: list) -> dict:
        """Compares structured SQL facts against semantic vector report text for discrepancies."""
        conflicts = []

        if not sql_context or not vector_chunks:
            return {"conflict_detected": False, "conflicts": []}

        # 1. Evidence status conflict check
        evidence_info = sql_context.get("evidence", {})
        if isinstance(evidence_info, list) and evidence_info:
            evidence_info = evidence_info[0]

        curr_status = evidence_info.get("current_status") if isinstance(evidence_info, dict) else None

        for chunk in vector_chunks:
            text = chunk.get("text", "").lower()
            meta = chunk.get("metadata", {})

            # Status mismatch check
            if curr_status == "Compromised":
                if "in pristine condition" in text or "admissible without qualification" in text:
                    conflicts.append({
                        "type": "STATUS_MISMATCH",
                        "severity": "HIGH",
                        "description": f"Historical report {meta.get('report_id')} states evidence was intact, but current authoritative database status is 'Compromised'.",
                        "authoritative_state": "Compromised (Database)",
                        "historical_claim": text[:120] + "...",
                    })

            # Weight discrepancy check
            if "weight" in text and "discrepancy" in text:
                conflicts.append({
                    "type": "WEIGHT_DISCREPANCY",
                    "severity": "MEDIUM",
                    "description": f"Report mentions weight discrepancy for Evidence E{meta.get('evidence_id')}.",
                    "authoritative_state": "Database records open TamperIncident/AuditLog for weight discrepancy.",
                    "historical_claim": text[:120] + "...",
                })

        conflict_detected = len(conflicts) > 0
        return {
            "conflict_detected": conflict_detected,
            "conflicts": conflicts,
            "summary": f"Detected {len(conflicts)} conflict(s) between database state and report text." if conflict_detected else "No conflicts detected."
        }
