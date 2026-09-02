"""
ai/grounded_llm.py
Interface for grounded LLM inference (Google Gemini / OpenAI / mock fallback).
Enforces grounded context execution, measures latency, and handles API errors gracefully.
"""
import time
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.config import LLM_PROVIDER, LLM_API_KEY, LLM_MODEL
from ai.prompt_builder import PromptBuilder, SYSTEM_PROMPT

# Placeholder strings that indicate a key has not actually been configured
_PLACEHOLDER_KEY_FRAGMENTS = (
    "your_gemini_api_key",
    "your_openai_api_key",
    "placeholder",
    "example_key",
    "xxxxxxxx",
)


def _is_real_api_key(key: str) -> bool:
    """Returns True only if the key looks like a real configured key."""
    if not key or len(key) < 10:
        return False
    key_lower = key.lower()
    if any(frag in key_lower for frag in _PLACEHOLDER_KEY_FRAGMENTS):
        return False
    if key.startswith("AQ."):
        return False
    return True


class GroundedLLM:

    def __init__(self, provider: str = LLM_PROVIDER, api_key: str = LLM_API_KEY, model_name: str = LLM_MODEL):
        self.provider = provider.lower()
        self.api_key = api_key
        self.model_name = model_name
        self.prompt_builder = PromptBuilder()

    def generate(self, question: str, context: dict) -> dict:
        """Generates grounded answer from context."""
        start_time = time.time()
        system_prompt, user_prompt = self.prompt_builder.build_prompt(question, context)

        if not context.get("is_sufficient", True):
            answer = "The available verified records and forensic reports do not contain sufficient information to answer this question."
            latency = int((time.time() - start_time) * 1000)
            return {
                "answer": answer,
                "sources": context.get("sources", []),
                "latency_ms": latency,
                "status": "insufficient",
                "model_used": "rule_engine",
            }

        # Check prompt injection in question
        if self._detect_prompt_injection(question):
            latency = int((time.time() - start_time) * 1000)
            return {
                "answer": "Security Policy Warning: Query contains potential instruction override / prompt injection attempt.",
                "sources": [],
                "latency_ms": latency,
                "status": "injection_blocked",
                "model_used": "security_filter",
            }

        # Dispatch to provider — only if we have a real, non-placeholder API key
        if self.provider == "gemini" and _is_real_api_key(self.api_key):
            answer, model_used = self._call_gemini(system_prompt, user_prompt, context)
        elif self.provider == "openai" and _is_real_api_key(self.api_key):
            answer, model_used = self._call_openai(system_prompt, user_prompt, context)
        else:
            # Fallback deterministic answer synthesis from context for offline/test environments
            answer, model_used = self._synthesize_local_answer(question, context)

        latency = int((time.time() - start_time) * 1000)

        # If local synthesis returned insufficient (no facts/chunks), mark status accordingly
        if "do not contain sufficient information" in answer:
            return {
                "answer": answer,
                "sources": context.get("sources", []),
                "latency_ms": latency,
                "status": "insufficient",
                "model_used": model_used,
            }

        return {
            "answer": answer,
            "sources": context.get("sources", []),
            "latency_ms": latency,
            "status": "success",
            "model_used": model_used,
        }

    def _call_gemini(self, system_prompt: str, user_prompt: str, context: dict) -> tuple:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt
            )
            response = model.generate_content(user_prompt, request_options={'timeout': 10})
            return response.text.strip(), self.model_name
        except Exception as e:
            print(f"[GroundedLLM] Gemini API error: {e}. Falling back to local synthesis.")
            # Pass through original context — NOT empty dict
            return self._synthesize_local_answer(user_prompt, context)

    def _call_openai(self, system_prompt: str, user_prompt: str, context: dict) -> tuple:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model_name or "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content.strip(), self.model_name
        except Exception as e:
            print(f"[GroundedLLM] OpenAI API error: {e}. Falling back to local synthesis.")
            # Pass through original context — NOT empty dict
            return self._synthesize_local_answer(user_prompt, context)

    def _synthesize_local_answer(self, question: str, context: dict) -> tuple:
        """Deterministic local answer synthesis grounded strictly in verified database context."""
        sql_data = context.get("sql_data", {})
        fact_lines = context.get("fact_lines", [])
        image_lines = context.get("image_lines", [])
        chunk_lines = context.get("chunk_lines", [])
        conflict_warning = context.get("conflict_warning", "")

        parts = []
        if conflict_warning:
            parts.append(conflict_warning)

        # 1. Image & Integrity Verification Lines
        if image_lines:
            for il in image_lines:
                if not ("unavailable" in il and "[IMAGE ANALYSIS]" in il):
                    parts.append(il)

        # 2. Pre-calculated Database Facts
        if fact_lines:
            parts.append("DATABASE:")
            for fl in fact_lines:
                parts.append(f"• {fl}")

        # 3. Structured Database Records (sql_data)
        if isinstance(sql_data, dict):
            # Evidence Details & Location
            if sql_data.get("evidence"):
                ev = sql_data["evidence"]
                if isinstance(ev, dict) and ev.get("evidence_id"):
                    eid_str = f"E{ev['evidence_id']:03d}"
                    status = ev.get("current_status", "")
                    if ev.get("unit_code"):
                        loc_str = f" Currently stored in Storage Unit '{ev['unit_code']}' ({ev.get('unit_type', 'Vault')}) at {ev.get('facility_name', 'Storage Facility')} ({ev.get('facility_address', '')})."
                    elif status == "In Lab":
                        loc_str = " Location: Currently located at Forensic Laboratory for Examination."
                    elif status == "In Court":
                        loc_str = " Location: Currently submitted to Court for Proceedings."
                    else:
                        loc_str = f" Location: Crime Scene ({ev.get('crime_scene_address', 'On File')})."
                    parts.append(f"DATABASE: Evidence {eid_str} ({ev.get('description')}) — Type: {ev.get('type_name')}, Current Status: {status}, Case FIR: {ev.get('fir_number')}, Collected By: {ev.get('collected_by')} at {ev.get('collection_datetime')}.{loc_str}")

            # Custody History
            if sql_data.get("custody") is not None:
                cust = sql_data["custody"]
                if isinstance(cust, list) and len(cust) > 0:
                    parts.append(f"DATABASE: Chain of Custody History ({len(cust)} record(s)):")
                    for c in cust:
                        parts.append(f"• [{c.get('transfer_datetime')}] {c.get('transferred_by')} → {c.get('received_by')} ({c.get('from_dept', 'Origin')} → {c.get('to_dept', 'Destination')}). Reason: {c.get('reason')}. Condition: {c.get('condition_at_transfer')}.")
                elif context.get("intent") in ("CUSTODY_HISTORY", "EVIDENCE_HISTORY", "GENERAL_SEARCH"):
                    parts.append("DATABASE: Chain of Custody History: No custody transfers recorded (initial collection state).")

            # Examinations & Reports
            if sql_data.get("examinations") is not None:
                exams = sql_data["examinations"]
                if isinstance(exams, list) and len(exams) > 0:
                    parts.append(f"DATABASE: Forensic Examinations ({len(exams)} record(s)):")
                    for ex in exams:
                        rpt_status = f"Filed (Admissible: {'Yes' if ex.get('is_admissible') else 'No'})" if ex.get("report_id") else "Pending Report"
                        parts.append(f"• Exam #{ex.get('exam_id')}: {ex.get('exam_type')} by {ex.get('examiner')} ({ex.get('lab_name')}). Status: {ex.get('status')} ({rpt_status}). Findings: {ex.get('findings_summary', 'None')}.")
                else:
                    parts.append("DATABASE: Forensic Examinations: No examinations currently assigned for this evidence item.")

            # Tamper Incidents
            if sql_data.get("tamper") is not None:
                tamper = sql_data["tamper"]
                if isinstance(tamper, list) and len(tamper) > 0:
                    parts.append(f"DATABASE: Tamper Incidents ({len(tamper)} record(s)):")
                    for t in tamper:
                        parts.append(f"• Incident #{t.get('incident_id')}: Severity {t.get('severity')} reported on {t.get('reported_datetime')} by {t.get('reported_by')}. Details: {t.get('description')}. Status: {t.get('resolution_status')}.")
                elif context.get("intent") in ("INTEGRITY_CHECK", "TAMPER_INVESTIGATION"):
                    parts.append("DATABASE: No tamper incidents reported for this evidence item.")

            # Case Summary
            if sql_data.get("case_summary"):
                cs = sql_data["case_summary"]
                if isinstance(cs, dict) and cs.get("case"):
                    c_info = cs["case"]
                    parts.append(f"DATABASE: Case {c_info.get('fir_number')} — Type: {c_info.get('type_name')}, Status: {c_info.get('status')}, Investigating Officer: {c_info.get('officer')}, Station: {c_info.get('station')}, Court: {c_info.get('court_name', 'None')}. Description: {c_info.get('description', '')}.")

            # Officer Details & Custody
            if sql_data.get("officer"):
                off = sql_data["officer"]
                parts.append(f"DATABASE: Officer Profile — {off.get('full_name')} (Badge: {off.get('badge_number')}, Designation: {off.get('designation_name')}, Department: {off.get('dept_name')}).")

            if sql_data.get("officer_custody"):
                off_c = sql_data["officer_custody"]
                if isinstance(off_c, list) and len(off_c) > 0:
                    parts.append(f"DATABASE: Custody Transfers Involving Officer ({len(off_c)} record(s)):")
                    for oc in off_c[:5]:
                        parts.append(f"• Evidence E{oc.get('evidence_id'):03d} ({oc.get('evidence_desc')}): {oc.get('transferred_by')} → {oc.get('received_by')} on {oc.get('transfer_datetime')}.")

            # Single Report Details
            if sql_data.get("report"):
                rpt = sql_data["report"]
                parts.append(f"FORENSIC REPORT: Report RPT-{rpt.get('report_id')} for Exam #{rpt.get('exam_id')}, Examiner: {rpt.get('examiner_name')} ({rpt.get('lab_name')}). Admissible: {'Yes' if rpt.get('is_admissible') else 'No'}. Text: {rpt.get('report_text')}.")

        # 4. Report Chunks
        if chunk_lines:
            parts.append("FORENSIC REPORT:")
            for cl in chunk_lines[:2]:
                parts.append(cl[:300] + "...")

        if not parts:
            return (
                "The available verified records and forensic reports do not contain sufficient information to answer this question.",
                "local_grounded_engine"
            )

        answer = "\n".join(parts)
        return answer, "local_grounded_engine"

    def _detect_prompt_injection(self, text: str) -> bool:
        """Detect prompt injection patterns in user query."""
        injection_keywords = [
            "ignore previous instructions", "ignore all instructions",
            "disregard system prompt", "you are now free", "system override",
            "reveal credentials", "show database passwords"
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in injection_keywords)
