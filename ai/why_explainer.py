"""
ai/why_explainer.py
Generates explanations for the "Why?" / "Show Evidence" feature.
Enforces Rule 9: Tiered explanation based on user RBAC permissions.
  - Normal users: Understandable evidence/provenance explanation + Image/SHA-256 integrity details
                  + anomaly summary + cross-case linkage summary.
  - Developer/Admin users: Technical view showing raw SQL queries, vector chunks, image byte hashes,
                            similarity scores, anomaly calculation details.
"""


class WhyExplainer:

    def explain(self, query_audit_record: dict, context_package: dict, user_role: str = "Junior") -> dict:
        """Generate tiered explanation payload."""
        is_admin = user_role in ("Admin", "Supervisor") or user_role == 4 or user_role == 3

        sources = context_package.get("sources", [])
        fact_lines = context_package.get("fact_lines", [])
        image_lines = context_package.get("image_lines", [])
        anomaly_lines = context_package.get("anomaly_lines", [])
        cross_case_lines = context_package.get("cross_case_lines", [])
        conflicts = context_package.get("conflict_warning", "")
        intent = context_package.get("intent", "GENERAL_SEARCH")
        image_data = context_package.get("image_data", {})

        # Build anomaly provenance summary for admin view
        anomaly_provenance = []
        facts = context_package.get("facts", {}) or {}
        for a in facts.get("geospatial_anomalies", []):
            anomaly_provenance.append({
                "type": a.get("type"),
                "log_id": a.get("log_id"),
                "previous_log_id": a.get("previous_log_id"),
                "from_location": a.get("from_location"),
                "to_location": a.get("to_location"),
                "distance_km": a.get("distance_km"),
                "elapsed_minutes": a.get("elapsed_minutes"),
                "implied_speed_kmh": a.get("implied_speed_kmh"),
                "threshold_kmh": a.get("threshold_kmh"),
                "severity": a.get("severity"),
                "data_source": "CustodyLog + Department.latitude/longitude (mapped from authoritative facility locations)",
                "calculation_method": "Haversine great-circle distance + elapsed time from transfer_datetime",
                "classification": "DETERMINISTIC ANOMALY — requires review — does not establish fraud or misconduct",
            })

        # Build cross-case provenance summary for admin view
        cross_case_provenance = []
        for link in facts.get("cross_case_links", []):
            cross_case_provenance.append({
                "source_evidence_id": link.get("source_evidence_id"),
                "linked_evidence_id": link.get("linked_evidence_id"),
                "linked_case_id": link.get("linked_case_id"),
                "similarity_score": link.get("similarity_score"),
                "vector_retrieval_basis": "ChromaDB cosine similarity over ExaminationReport text embeddings (all-MiniLM-L6-v2)",
                "authorized_scope": link.get("authorized_scope", "cases authorized for current user role"),
                "classification": "POTENTIAL SEMANTIC LINK — supporting signal only — not forensic proof",
            })

        # Plain-language user summary (for all users)
        user_explanation = {
            "summary": f"This answer was derived from verified forensic records and multimodal data sources for intent '{intent}'.",
            "provenance_sources": sources,
            "verified_facts": fact_lines,
            "image_and_integrity_evidence": image_lines,
            "has_conflict": bool(conflicts),
            "conflict_details": conflicts if conflicts else "No source conflicts detected.",
            "temporal_geo_anomalies": {
                "detected": len(anomaly_lines) > 0,
                "count": len(anomaly_lines),
                "summary_lines": anomaly_lines,
                "disclaimer": "Anomalies are deterministic calculations. They do not establish fraud or misconduct.",
            },
            "cross_case_linkage": {
                "found": len(cross_case_lines) > 0,
                "count": len(cross_case_lines),
                "summary_lines": cross_case_lines,
                "disclaimer": "Cross-case links are POTENTIAL SEMANTIC LINKS based on vector similarity. They are not forensic proof of case connection.",
            },
        }

        if not is_admin:
            return {
                "mode": "user",
                "explanation": user_explanation,
            }

        # Admin/Developer view (includes raw technical context)
        tech_explanation = dict(user_explanation)
        tech_explanation.update({
            "raw_sql_data": context_package.get("sql_data", {}),
            "raw_vector_chunks": context_package.get("chunk_lines", []),
            "raw_image_data": image_data,
            "detected_entities": context_package.get("entities", {}),
            "retrieval_method": query_audit_record.get("retrieval_method", "HYBRID"),
            "retrieval_score": query_audit_record.get("retrieval_score", 1.0),
            "response_latency_ms": query_audit_record.get("response_latency_ms", 0),
            "model_used": query_audit_record.get("model_used", "unknown"),
            "anomaly_provenance_detail": anomaly_provenance,
            "cross_case_provenance_detail": cross_case_provenance,
        })

        return {
            "mode": "admin",
            "explanation": tech_explanation,
        }
