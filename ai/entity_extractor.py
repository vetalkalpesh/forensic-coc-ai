"""
ai/entity_extractor.py
Extracts entity identifiers (Evidence ID, Case ID, FIR number, Officer badge, dates) from user queries.
"""
import re


class EntityExtractor:

    def extract(self, question: str) -> dict:
        """Extract structured entities from natural-language query."""
        entities = {
            "evidence_id": None,
            "case_id": None,
            "fir_number": None,
            "officer_badge": None,
            "report_id": None,
            "date": None,
        }

        # 1. Evidence ID pattern: E104, E-104, E 104, evidence 104, E001
        e_match = re.search(r"\b(?:E|E-|\bevidence\s+)(\d{1,5})\b", question, re.IGNORECASE)
        if e_match:
            try:
                entities["evidence_id"] = int(e_match.group(1))
            except ValueError:
                pass

        # 2. Report ID pattern: RPT-9999, RPT_9999, report 9999, RPT9999
        rpt_match = re.search(r"\b(?:RPT[/\-_]?|report\s+)(\d{1,5})\b", question, re.IGNORECASE)
        if rpt_match:
            try:
                entities["report_id"] = int(rpt_match.group(1))
            except ValueError:
                pass

        # 3. FIR number pattern: FIR/2026/PUN/0045 or FIR-2026-0045 or SYN/2024/ST001/0001
        fir_match = re.search(r"\b(?:FIR|SYN)[/\-]\d{4}[/\-][A-Z0-9]+[/\-]\d+\b", question, re.IGNORECASE)
        if fir_match:
            entities["fir_number"] = fir_match.group(0).upper()

        # 4. Officer Badge pattern: MH-2301, DL-1002
        badge_match = re.search(r"\b[A-Z]{2}-\d{4}\b", question, re.IGNORECASE)
        if badge_match:
            entities["officer_badge"] = badge_match.group(0).upper()

        # 5. Date pattern: YYYY-MM-DD
        date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", question)
        if date_match:
            entities["date"] = date_match.group(0)

        return entities
