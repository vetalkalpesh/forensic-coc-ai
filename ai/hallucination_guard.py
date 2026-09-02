"""
ai/hallucination_guard.py
Post-generation validator checking generated answer against retrieved context.
Flags entity IDs or claims mentioned in the answer that do not exist in the context.
"""
import re


class HallucinationGuard:

    def validate_answer(self, answer: str, context: dict) -> dict:
        """Validate generated answer for potential hallucinations."""
        if not answer:
            return {"is_valid": True, "hallucinated_entities": [], "flag": 0}

        # Extract Evidence IDs, Report IDs, and Badges mentioned in answer
        answer_eids = set(re.findall(r"\bE(\d{1,5})\b", answer))
        answer_rids = set(re.findall(r"\bRPT[_\-]?(\d{1,5})\b", answer, re.IGNORECASE))
        answer_badges = set(re.findall(r"\b[A-Z]{2}-\d{4}\b", answer, re.IGNORECASE))

        # Extract IDs present in context
        context_str = str(context)
        context_eids = set(re.findall(r"\bE(\d{1,5})\b", context_str))
        context_rids = set(re.findall(r"\bRPT[_\-]?(\d{1,5})\b", context_str, re.IGNORECASE))
        context_badges = set(re.findall(r"\b[A-Z]{2}-\d{4}\b", context_str, re.IGNORECASE))

        # Identify entity IDs mentioned in answer but missing from retrieved context
        hallucinated = (answer_eids - context_eids) | (answer_rids - context_rids) | (answer_badges - context_badges)

        is_valid = len(hallucinated) == 0
        flag = 0 if is_valid else 1

        return {
            "is_valid": is_valid,
            "hallucinated_entities": list(hallucinated),
            "flag": flag,
            "message": f"Detected potential hallucinated entities: {list(hallucinated)}" if not is_valid else "Answer verified against context."
        }
