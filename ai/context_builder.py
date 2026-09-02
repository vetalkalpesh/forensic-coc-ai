"""
ai/context_builder.py
Assembles structured SQL data, pre-calculated facts, semantic vector chunks,
image metadata, SHA-256 byte integrity, Vision AI observations, conflict flags,
temporal/geospatial anomaly findings, and cross-case linkage signals
into a validated context package for LLM generation.
"""
import os

class ContextBuilder:

    def build_context(self, intent: str, entities: dict, sql_data: dict,
                      facts: dict, vector_results: list, conflicts: dict,
                      image_data: dict = None, user_role: str = "Junior",
                      question: str = "") -> dict:
        """Assembles verified context package."""

        # Format pre-calculated facts
        fact_lines = []
        if facts.get("delays"):
            for d in facts["delays"]:
                fact_lines.append(
                    f"Custody Transfer Delay: Evidence E{d['evidence_id']} transferred from {d['from_officer']} to {d['to_officer']} on {d['transfer_datetime']}. Physical vs Recorded Delay: {d['delay_hours']} hours ({d['delay_flag']})."
                )
        if facts.get("expiry"):
            for exp in facts["expiry"]:
                fact_lines.append(
                    f"Expiry Fact: Evidence E{exp['evidence_id']} ({exp['description']}) expiry date is {exp['expiry_date']}. Remaining: {exp['days_remaining']} days ({exp['expiry_status']})."
                )
        if facts.get("overdue"):
            for ov in facts["overdue"]:
                fact_lines.append(
                    f"Overdue Exam Fact: Evidence E{ov['evidence_id']} examination type '{ov['exam_type']}' started on {ov['start_date']}. Pending for {ov['days_pending']} days vs SLA of {ov['sla_days']} days ({ov['overdue_days']} days overdue)."
                )
        if facts.get("dead_man"):
            for dm in facts["dead_man"]:
                fact_lines.append(
                    f"Dead-Man Switch Fact: Evidence E{dm['evidence_id']} ({dm['description']}) has been inactive for {dm['inactive_days']} days. Last activity: {dm['last_activity']}."
                )

        # Temporal & Geospatial Anomaly Lines
        anomaly_lines = []
        if facts.get("geospatial_anomalies"):
            for a in facts["geospatial_anomalies"]:
                if a.get("type") == "IMPOSSIBLE_TRAVEL_SPEED":
                    anomaly_lines.append(
                        f"[TEMPORAL/GEO ANOMALY] {a['type']}: Transfer log #{a['log_id']} from {a['from_location']} to {a['to_location']}. "
                        f"Distance: {a['distance_km']} km, Elapsed: {a['elapsed_minutes']} min, "
                        f"Implied speed: {a['implied_speed_kmh']} km/h (threshold: {a['threshold_kmh']} km/h). "
                        f"Severity: {a['severity']}. {a['explanation']}"
                    )
                elif a.get("type") == "IMPOSSIBLE_INSTANTANEOUS_MOVEMENT":
                    anomaly_lines.append(
                        f"[TEMPORAL/GEO ANOMALY] {a['type']}: Transfer log #{a['log_id']} from {a['from_location']} to {a['to_location']}. "
                        f"Distance: {a['distance_km']} km with 0 elapsed time. "
                        f"Severity: {a['severity']}. {a['explanation']}"
                    )
                elif a.get("type") == "TEMPORAL_ORDERING_INCONSISTENCY":
                    anomaly_lines.append(
                        f"[TEMPORAL/GEO ANOMALY] {a['type']}: Transfer log #{a['log_id']} precedes log #{a['previous_log_id']} by {abs(a['elapsed_minutes'])} min. "
                        f"Severity: {a['severity']}. {a['explanation']}"
                    )
                else:
                    anomaly_lines.append(f"[TEMPORAL/GEO ANOMALY] {a.get('type','UNKNOWN')}: {a.get('explanation','')}")

        # Cross-Case Linkage Lines
        cross_case_lines = []
        if facts.get("cross_case_links"):
            for link in facts["cross_case_links"]:
                cross_case_lines.append(
                    f"[CROSS-CASE LINKAGE] Potential Link: Source evidence E{link.get('source_evidence_id')} "
                    f"has semantic similarity {link.get('similarity_score', 0.0):.3f} with evidence E{link.get('linked_evidence_id')} "
                    f"in case {link.get('linked_case_id')}. Report: {link.get('report_summary','N/A')}. "
                    f"Classification: POTENTIAL SEMANTIC LINK (not forensic proof). {link.get('explanation','')}"
                )

        # Image & SHA-256 Integrity Lines
        image_lines = []
        if image_data:
            eid_str = f"E{entities.get('evidence_id', 0):03d}" if entities.get('evidence_id') else "Evidence"
            
            # SHA-256 Cryptographic Verification Line
            sha_info = image_data.get("sha256_integrity", {})
            st = sha_info.get("integrity", "NO_IMAGE")
            if st != "NO_IMAGE":
                image_lines.append(
                    f"[INTEGRITY] Evidence {eid_str} Image File: '{sha_info.get('file_path')}' | Cryptographic SHA-256 Byte Verification Status: {st} | Stored Hash: {sha_info.get('stored_hash')} | Current Bytes Hash: {sha_info.get('current_hash')}."
                )
            else:
                image_lines.append(f"[INTEGRITY] Evidence {eid_str}: No photographic evidence is currently available.")

            # Vision AI Observations Line
            vis = image_data.get("vision_analysis", {})
            if vis and vis.get("status") == "ANALYZED":
                obs_str = " ".join(vis.get("observations", []))
                image_lines.append(f"[IMAGE ANALYSIS] Evidence {eid_str} Photograph Visual Observations: {obs_str} (Condition: {vis.get('visible_condition')}).")
            elif vis and vis.get("status") == "UNAVAILABLE_NO_API_KEY":
                image_lines.append(f"[IMAGE ANALYSIS] Evidence {eid_str}: Visual AI analysis unavailable (No Vision API configured).")

            # Visual-DB Cross Check Line
            cc_res = image_data.get("visual_cross_check", {})
            if cc_res and cc_res.get("warnings"):
                warn_msgs = "; ".join([w["description"] for w in cc_res["warnings"]])
                image_lines.append(f"[VISUAL CROSS-CHECK] ⚠ WARNING: {warn_msgs}")

        # Format vector chunks
        chunk_lines = []
        for i, chunk in enumerate(vector_results):
            meta = chunk.get("metadata", {})
            chunk_lines.append(
                f"[Report Source {i+1}] (Report ID: RPT_{meta.get('report_id')}, Evidence: E{meta.get('evidence_id')}, Lab: {meta.get('lab_name')}, Examiner: {meta.get('examiner_name')}, Date: {meta.get('filed_on')}):\n{chunk.get('text')}"
            )

        # Format conflict warning
        conflict_warning = ""
        if conflicts.get("conflict_detected"):
            conflict_warning = "⚠ SOURCE CONFLICT WARNING:\n" + "\n".join([f"- {c['description']}" for c in conflicts.get("conflicts", [])])

        is_sufficient = self._check_sufficiency(entities, sql_data, fact_lines, vector_results, question, image_data)

        return {
            "intent": intent,
            "entities": entities,
            "sql_data": sql_data,
            "fact_lines": fact_lines,
            "anomaly_lines": anomaly_lines,
            "cross_case_lines": cross_case_lines,
            "image_lines": image_lines,
            "chunk_lines": chunk_lines,
            "conflict_warning": conflict_warning,
            "is_sufficient": is_sufficient,
            "image_data": image_data or {},
            "sources": self._extract_sources(sql_data, vector_results, image_data, facts),
        }

    def _check_sufficiency(self, entities: dict, sql_data: dict, fact_lines: list,
                            vector_results: list, question: str = "", image_data: dict = None) -> bool:
        """Determines if the retrieved context is sufficient to answer the specific question."""
        eid = entities.get("evidence_id")
        rid = entities.get("report_id")
        badge = entities.get("officer_badge")
        fir = entities.get("fir_number")

        # 1. If explicit evidence_id requested, verify it exists in retrieved DB data or media
        if eid is not None:
            has_eid = False
            if sql_data.get("evidence") or sql_data.get("custody") or sql_data.get("examinations") or sql_data.get("tamper"):
                has_eid = True
            for f in fact_lines:
                if f"E{eid}" in f:
                    has_eid = True
            for v in vector_results:
                if v.get("metadata", {}).get("evidence_id") == eid:
                    has_eid = True
            if image_data and image_data.get("sha256_integrity") and image_data["sha256_integrity"].get("integrity") != "NO_IMAGE":
                has_eid = True
            if not has_eid:
                return False

        # 2. If explicit report_id requested, verify it exists in retrieved data
        if rid is not None:
            has_rid = False
            if sql_data.get("report"):
                has_rid = True
            for v in vector_results:
                if v.get("metadata", {}).get("report_id") == rid:
                    has_rid = True
            if not has_rid:
                return False

        # 3. If explicit officer_badge requested, verify officer/custody logs exist
        if badge is not None:
            has_badge = False
            if sql_data.get("officer") or sql_data.get("officer_custody"):
                has_badge = True
            if not has_badge:
                return False

        # 4. If explicit fir_number requested, verify case details exist
        if fir is not None:
            has_fir = False
            if sql_data.get("case_summary"):
                has_fir = True
            if not has_fir:
                return False

        # 5. General presence check
        has_sql = False
        if isinstance(sql_data, dict):
            for k, v in sql_data.items():
                if v:
                    has_sql = True
                    break

        has_image = bool(image_data and image_data.get("sha256_integrity"))

        if not (has_sql or fact_lines or vector_results or has_image):
            return False

        # 6. Specific predicate / attribute grounding check
        if question:
            q_lower = question.lower()
            unsupported_terms = ["satellite", "alien", "ufo", "spacecraft", "magic", "telepathy", "cryptocurrency wallet"]
            for term in unsupported_terms:
                if term in q_lower:
                    all_text = " ".join(fact_lines) + " " + " ".join([c.get("text", "") for c in vector_results]) + " " + str(sql_data)
                    if term not in all_text.lower():
                        return False

        return True

    def _extract_sources(self, sql_data: dict, vector_results: list, image_data: dict = None, facts: dict = None) -> list:
        sources = []

        # 1. Parse Image & Integrity Sources
        if image_data and image_data.get("sha256_integrity"):
            sha_info = image_data["sha256_integrity"]
            if sha_info.get("integrity") != "NO_IMAGE":
                sources.append({"type": "EvidenceImage", "id": os.path.basename(sha_info.get("file_path", "")), "table": "EvidenceMedia"})
                sources.append({"type": "SHA256IntegrityRecord", "id": f"Hash-{sha_info.get('stored_hash', '')[:8]}", "table": "EvidenceMedia"})

        # 2. Parse SQL Sources
        if isinstance(sql_data, dict):
            if sql_data.get("evidence"):
                ev = sql_data["evidence"]
                items = ev if isinstance(ev, list) else [ev]
                for item in items:
                    if isinstance(item, dict) and item.get("evidence_id"):
                        sources.append({"type": "Evidence", "id": f"E{item['evidence_id']:03d}", "table": "Evidence"})

            if sql_data.get("custody"):
                cust = sql_data["custody"]
                if isinstance(cust, list):
                    for c in cust:
                        if isinstance(c, dict) and c.get("evidence_id"):
                            sources.append({"type": "Evidence", "id": f"E{c['evidence_id']:03d}", "table": "CustodyLog"})

            if sql_data.get("tamper"):
                tamp = sql_data["tamper"]
                if isinstance(tamp, list):
                    for t in tamp:
                        if isinstance(t, dict) and t.get("evidence_id"):
                            sources.append({"type": "Evidence", "id": f"E{t['evidence_id']:03d}", "table": "TamperIncident"})

            if sql_data.get("examinations"):
                exams = sql_data["examinations"]
                if isinstance(exams, list):
                    for ex in exams:
                        if isinstance(ex, dict):
                            if ex.get("evidence_id"):
                                sources.append({"type": "Evidence", "id": f"E{ex['evidence_id']:03d}", "table": "Examination"})
                            if ex.get("report_id"):
                                sources.append({"type": "ExaminationReport", "id": f"RPT-{ex['report_id']}", "table": "ExaminationReport"})

            if sql_data.get("case_summary"):
                cs = sql_data["case_summary"]
                if isinstance(cs, dict):
                    if cs.get("case") and isinstance(cs["case"], dict) and cs["case"].get("fir_number"):
                        sources.append({"type": "Case", "id": cs["case"]["fir_number"], "table": "CriminalCase"})
                    if cs.get("evidence") and isinstance(cs["evidence"], list):
                        for item in cs["evidence"]:
                            if isinstance(item, dict) and item.get("evidence_id"):
                                sources.append({"type": "Evidence", "id": f"E{item['evidence_id']:03d}", "table": "Evidence"})

            if sql_data.get("report"):
                rpt = sql_data["report"]
                if isinstance(rpt, dict):
                    if rpt.get("report_id"):
                        sources.append({"type": "ExaminationReport", "id": f"RPT-{rpt['report_id']}", "table": "ExaminationReport"})
                    if rpt.get("evidence_id"):
                        sources.append({"type": "Evidence", "id": f"E{rpt['evidence_id']:03d}", "table": "Evidence"})

        # 3. Parse Vector Sources
        if isinstance(vector_results, list):
            for chunk in vector_results:
                if isinstance(chunk, dict):
                    meta = chunk.get("metadata", {})
                    if meta.get("evidence_id"):
                        sources.append({"type": "Evidence", "id": f"E{int(meta['evidence_id']):03d}", "table": "Evidence"})
                    if meta.get("fir_number"):
                        sources.append({"type": "Case", "id": meta["fir_number"], "table": "CriminalCase"})
                    if meta.get("report_id"):
                        sources.append({"type": "ExaminationReport", "id": f"RPT-{meta['report_id']}", "table": "ExaminationReport"})

        # 4. Anomaly Sources
        if facts and facts.get("geospatial_anomalies"):
            for a in facts["geospatial_anomalies"]:
                if a.get("log_id"):
                    sources.append({"type": "TemporalGeoAnomaly", "id": f"LOG-{a['log_id']}", "table": "CustodyLog"})

        # 5. Cross-Case Linkage Sources
        if facts and facts.get("cross_case_links"):
            for link in facts["cross_case_links"]:
                if link.get("linked_evidence_id"):
                    sources.append({"type": "CrossCasePotentialLink", "id": f"E{int(link['linked_evidence_id']):03d}", "table": "Evidence"})

        # Unique sources deduction
        unique_sources = []
        seen = set()
        for s in sources:
            key = f"{s['type']}:{s['id']}"
            if key not in seen:
                seen.add(key)
                unique_sources.append(s)

        return unique_sources
