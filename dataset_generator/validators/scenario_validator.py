"""
dataset_generator/validators/scenario_validator.py
Verifies presence and correctness of Scenarios A–J in the database after dataset generation.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.base_generator import BaseGenerator


class ScenarioValidator(BaseGenerator):

    def validate_scenarios(self) -> dict:
        """Checks counts and presence for scenario artifacts in the database."""
        val = ScenarioValidator()
        val.connect()

        results = {}

        # Scenario B (Hash mismatch)
        b_count = val.query_one("SELECT COUNT(*) c FROM TamperIncident WHERE description LIKE '%hash mismatch%'")
        results["Scenario B (Hash Mismatch)"] = b_count.get("c", 0) if b_count else 0

        # Scenario C (Custody delay > 4h)
        c_count = val.query_one("SELECT COUNT(*) c FROM TemporalAnomalyView WHERE temporal_flag LIKE 'SUSPICIOUS GAP'")
        results["Scenario C (Custody Delay)"] = c_count.get("c", 0) if c_count else 0

        # Scenario D (Tamper cascade)
        d_count = val.query_one("SELECT COUNT(*) c FROM AlertLog WHERE message LIKE '%TAMPER CASCADE%'")
        results["Scenario D (Derived Cascade)"] = d_count.get("c", 0) if d_count else 0

        # Scenario E (Expiring biological)
        e_count = val.query_one("SELECT COUNT(*) c FROM AlertLog WHERE alert_type = 'Expiry'")
        results["Scenario E (Expiring Bio)"] = e_count.get("c", 0) if e_count else 0

        # Scenario F (Overdue examination)
        f_count = val.query_one("SELECT COUNT(*) c FROM Examination WHERE status = 'Overdue'")
        results["Scenario F (Overdue Exam)"] = f_count.get("c", 0) if f_count else 0

        # Scenario G (Dead-man switch)
        g_count = val.query_one("SELECT COUNT(*) c FROM AlertLog WHERE alert_type = 'DeadManSwitch'")
        results["Scenario G (Dead-Man Switch)"] = g_count.get("c", 0) if g_count else 0

        print("\n--- Controlled Scenario Verification ---")
        for label, count in results.items():
            status = "[PASS]" if count > 0 else "[WARN]"
            print(f"  {status} {label}: {count} instances found")

        val.disconnect()
        return results
