"""
ai/intent_classifier.py
Classifies user natural-language questions into one of 15 intent categories.
Uses fast deterministic pattern and keyword matching (no external LLM call needed).
"""
import re


INTENTS = [
    "EVIDENCE_HISTORY",
    "EVIDENCE_LOCATION",
    "CUSTODY_HISTORY",
    "INTEGRITY_CHECK",
    "HASH_VERIFICATION",
    "TAMPER_INVESTIGATION",
    "ALERT_INVESTIGATION",
    "CASE_SUMMARY",
    "FORENSIC_FINDINGS",
    "EXAMINATION_SUMMARY",
    "COURT_HISTORY",
    "STORAGE_HISTORY",
    "ANOMALY_INVESTIGATION",
    "GENERAL_SEARCH",
    "UNSUPPORTED_QUERY",
]

PATTERNS = {
    "INTEGRITY_CHECK": [
        r"integrity", r"tamper", r"compromis", r"altered", r"hash mismatch", r"corrupt"
    ],
    "HASH_VERIFICATION": [
        r"sha-?256", r"hash value", r"hash verification", r"checksum", r"hash match"
    ],
    "CUSTODY_HISTORY": [
        r"custody", r"handled", r"transfer", r"chain of custody", r"who had", r"who took", r"held by"
    ],
    "EVIDENCE_LOCATION": [
        r"where is", r"current location", r"currently located", r"stored at", r"which facility", r"which unit"
    ],
    "EVIDENCE_HISTORY": [
        r"complete history", r"history of evidence", r"timeline of", r"life cycle", r"trace evidence"
    ],
    "FORENSIC_FINDINGS": [
        r"forensic finding", r"examiner conclude", r"lab report", r"analysis result", r"dna profile", r"fingerprint result"
    ],
    "EXAMINATION_SUMMARY": [
        r"overdue", r"pending exam", r"examination summary", r"status of exam", r"exam.*overdue", r"overdue.*exam"
    ],
    "CASE_SUMMARY": [
        r"summarize case", r"summary of case", r"case summary", r"fir-", r"fir/"
    ],
    "TAMPER_INVESTIGATION": [
        r"tamper incident", r"tamper report", r"why was .* marked as compromised", r"compromised evidence"
    ],
    "ALERT_INVESTIGATION": [
        r"alert", r"warning", r"escalation", r"dead man"
    ],
    "STORAGE_HISTORY": [
        r"storage history", r"stored on", r"vault", r"freezer"
    ],
    "COURT_HISTORY": [
        r"court", r"hearing", r"judge", r"submitted to court", r"admissible"
    ],
    "ANOMALY_INVESTIGATION": [
        r"delay", r"expiring", r"suspicious", r"anomaly", r"gap", r"dead-man"
    ],
}


class IntentClassifier:

    def classify(self, question: str) -> str:
        """Classify question into one of 15 intents."""
        q_lower = question.lower().strip()

        if not q_lower or len(q_lower) < 3:
            return "UNSUPPORTED_QUERY"

        for intent, regex_list in PATTERNS.items():
            for pattern in regex_list:
                if re.search(pattern, q_lower):
                    return intent

        return "GENERAL_SEARCH"
