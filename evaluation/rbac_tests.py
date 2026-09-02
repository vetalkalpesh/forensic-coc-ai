"""
evaluation/rbac_tests.py
Dedicated evaluation suite for Role-Based Access Control (RBAC) security filtering.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.sql_retriever import SQLRetriever


def test_rbac_security():
    """Verifies that Junior role cannot retrieve Admin-scoped records."""
    retriever = SQLRetriever()

    print("=" * 60)
    print("  RBAC SECURITY RETRIEVAL TEST SUITE")
    print("=" * 60)

    # 1. Admin role query on AuditLog
    admin_res = retriever.get_audit_log(table_name="Evidence", user_role="Admin")
    print(f"  Admin AuditLog Access: {len(admin_res)} records returned.")

    # 2. Junior role query on AuditLog
    junior_res = retriever.get_audit_log(table_name="Evidence", user_role="Junior")
    print(f"  Junior AuditLog Access: {len(junior_res)} records returned.")

    is_passed = (len(admin_res) >= 0) and (len(junior_res) == 0)
    status_str = "[PASS]" if is_passed else "[FAIL]"

    print(f"  RBAC Enforce Result: {status_str}")
    print("=" * 60)


if __name__ == "__main__":
    test_rbac_security()
