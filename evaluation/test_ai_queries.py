"""
evaluation/test_ai_queries.py
Comprehensive Functional & Grounding Regression Test Suite for Forensic AI Assistant:
1. Evidence E001 history
2. Evidence E003 current location
3. E002 tamper status
4. Overdue examinations
5. Custody transfers for evidence
6. Storage location tracking
7. Examination status
8. Court submission status
9. Missing-image evidence handling
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.hybrid_retriever import HybridRetriever

def run_ai_query_tests():
    hr = HybridRetriever()

    test_cases = [
        {
            "id": 1,
            "q": "Give me the complete history of evidence E001.",
            "expected_intent": "EVIDENCE_HISTORY",
            "expected_keywords": ["E001", "Blood sample", "Chain of Custody"]
        },
        {
            "id": 2,
            "q": "Where is evidence E003 currently located?",
            "expected_intent": "EVIDENCE_LOCATION",
            "expected_keywords": ["E003", "In Storage", "Storage Unit"]
        },
        {
            "id": 3,
            "q": "Was evidence E002 tampered with?",
            "expected_intent": "INTEGRITY_CHECK",
            "expected_keywords": ["E002"]
        },
        {
            "id": 4,
            "q": "Which forensic examinations are overdue?",
            "expected_intent": "EXAMINATION_SUMMARY",
            "expected_keywords": ["Overdue Exam Fact"]
        },
        {
            "id": 5,
            "q": "Show custody transfers for evidence E004.",
            "expected_intent": "CUSTODY_HISTORY",
            "expected_keywords": ["E004", "Chain of Custody"]
        },
        {
            "id": 6,
            "q": "What is the storage location of evidence E005?",
            "expected_intent": "GENERAL_SEARCH",
            "expected_keywords": ["E005", "Location"]
        },
        {
            "id": 7,
            "q": "What is the examination status for evidence E006?",
            "expected_intent": "EXAMINATION_SUMMARY",
            "expected_keywords": ["E006", "Examination"]
        },
        {
            "id": 8,
            "q": "Has evidence E008 been submitted to court?",
            "expected_intent": "COURT_HISTORY",
            "expected_keywords": ["E008"]
        },
        {
            "id": 9,
            "q": "What does the photograph of evidence E010 show?",
            "expected_intent": "GENERAL_SEARCH",
            "expected_keywords": ["No photographic evidence is currently available"]
        }
    ]

    print("=" * 65)
    print("  FORENSIC AI ASSISTANT COMPREHENSIVE FUNCTIONAL TEST SUITE")
    print("=" * 65)

    passed_count = 0
    for t in test_cases:
        q = t["q"]
        res = hr.process_query(q)
        ans = res.get("answer", "")
        status = res.get("status", "")
        sources = res.get("sources", [])

        print(f"\nTest {t['id']}: '{q}'")
        print(f"  Intent: {res.get('intent')} | Status: {status}")
        src_labels = [s['type'] + ' ' + s['id'] for s in sources]
        print(f"  Sources: {src_labels}")
        print(f"  Answer Snippet:\n{ans[:200]}...")

        # Assertions
        assert status == "success" or (t["id"] == 9 and "No photographic evidence" in ans), f"Unexpected status: '{status}'"
        for kw in t["expected_keywords"]:
            assert kw.lower() in ans.lower(), f"Expected keyword '{kw}' missing from answer for query: {q}"

        print(f"  Result: [PASS]")
        passed_count += 1

    print("=" * 65)
    print(f"  RESULTS: {passed_count}/{len(test_cases)} AI Functional Tests Passed.")
    print("=" * 65)

if __name__ == "__main__":
    run_ai_query_tests()
