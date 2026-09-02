"""
evaluation/conflict_tests.py
Dedicated evaluation test suite for Source Conflict Detection mechanism (Rule 7).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.conflict_detector import ConflictDetector


def test_conflict_detection():
    """Runs source conflict detection tests."""
    detector = ConflictDetector()

    print("=" * 60)
    print("  SOURCE CONFLICT DETECTION TEST SUITE (Rule 7)")
    print("=" * 60)

    # Simulated SQL context where DB status is Compromised
    sql_context = {
        "evidence": {
            "evidence_id": 2,
            "current_status": "Compromised",
            "description": "Kitchen knife"
        }
    }

    # Simulated historical vector chunk claiming item was in pristine condition
    vector_chunks = [{
        "chunk_id": "RPT_1_chk0",
        "text": "The kitchen knife evidence was examined and found in pristine condition with no post-collection damage.",
        "metadata": {"report_id": 1, "evidence_id": 2}
    }]

    res = detector.detect_conflicts(sql_context, vector_chunks)

    is_passed = res.get("conflict_detected") is True
    status_str = "[PASS]" if is_passed else "[FAIL]"

    print(f"  Conflict Test 1 (DB Status Compromised vs Report Intact): {status_str}")
    print(f"  Details: {res.get('summary')}")
    print("=" * 60)


if __name__ == "__main__":
    test_conflict_detection()
