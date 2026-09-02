"""
dataset_generator/validators/fk_validator.py
Validates Foreign Key integrity across all database tables after synthetic data generation.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.base_generator import BaseGenerator


class FKValidator(BaseGenerator):

    def validate_all_foreign_keys() -> bool:
        """Runs validation checks on foreign keys across all core tables."""
        val = FKValidator()
        val.connect()

        checks = [
            ("Officer -> Designation", "SELECT COUNT(*) c FROM Officer o LEFT JOIN Designation d ON o.designation_id=d.designation_id WHERE d.designation_id IS NULL"),
            ("Officer -> Department", "SELECT COUNT(*) c FROM Officer o LEFT JOIN Department d ON o.department_id=d.dept_id WHERE d.dept_id IS NULL"),
            ("CriminalCase -> PoliceStation", "SELECT COUNT(*) c FROM CriminalCase cc LEFT JOIN PoliceStation ps ON cc.police_station_id=ps.station_id WHERE ps.station_id IS NULL"),
            ("CriminalCase -> CaseType", "SELECT COUNT(*) c FROM CriminalCase cc LEFT JOIN CaseType ct ON cc.case_type_id=ct.type_id WHERE ct.type_id IS NULL"),
            ("CriminalCase -> Officer", "SELECT COUNT(*) c FROM CriminalCase cc LEFT JOIN Officer o ON cc.investigating_officer_id=o.officer_id WHERE o.officer_id IS NULL"),
            ("Evidence -> CriminalCase", "SELECT COUNT(*) c FROM Evidence e LEFT JOIN CriminalCase cc ON e.case_id=cc.case_id WHERE cc.case_id IS NULL"),
            ("Evidence -> EvidenceType", "SELECT COUNT(*) c FROM Evidence e LEFT JOIN EvidenceType et ON e.type_id=et.type_id WHERE et.type_id IS NULL"),
            ("Evidence -> Officer", "SELECT COUNT(*) c FROM Evidence e LEFT JOIN Officer o ON e.collected_by=o.officer_id WHERE o.officer_id IS NULL"),
            ("CustodyLog -> Evidence", "SELECT COUNT(*) c FROM CustodyLog cl LEFT JOIN Evidence e ON cl.evidence_id=e.evidence_id WHERE e.evidence_id IS NULL"),
            ("CustodyLog -> Officer (transferred_by)", "SELECT COUNT(*) c FROM CustodyLog cl LEFT JOIN Officer o ON cl.transferred_by=o.officer_id WHERE o.officer_id IS NULL"),
            ("CustodyLog -> Officer (received_by)", "SELECT COUNT(*) c FROM CustodyLog cl LEFT JOIN Officer o ON cl.received_by=o.officer_id WHERE o.officer_id IS NULL"),
            ("Examination -> Evidence", "SELECT COUNT(*) c FROM Examination ex LEFT JOIN Evidence e ON ex.evidence_id=e.evidence_id WHERE e.evidence_id IS NULL"),
            ("Examination -> Examiner", "SELECT COUNT(*) c FROM Examination ex LEFT JOIN Examiner exr ON ex.examiner_id=exr.examiner_id WHERE exr.examiner_id IS NULL"),
            ("ExaminationReport -> Examination", "SELECT COUNT(*) c FROM ExaminationReport er LEFT JOIN Examination ex ON er.exam_id=ex.exam_id WHERE ex.exam_id IS NULL"),
            ("StorageLog -> Evidence", "SELECT COUNT(*) c FROM StorageLog sl LEFT JOIN Evidence e ON sl.evidence_id=e.evidence_id WHERE e.evidence_id IS NULL"),
            ("StorageLog -> StorageUnit", "SELECT COUNT(*) c FROM StorageLog sl LEFT JOIN StorageUnit su ON sl.unit_id=su.unit_id WHERE su.unit_id IS NULL"),
            ("CourtSubmission -> Evidence", "SELECT COUNT(*) c FROM CourtSubmission cs LEFT JOIN Evidence e ON cs.evidence_id=e.evidence_id WHERE e.evidence_id IS NULL"),
            ("TamperIncident -> Evidence", "SELECT COUNT(*) c FROM TamperIncident ti LEFT JOIN Evidence e ON ti.evidence_id=e.evidence_id WHERE e.evidence_id IS NULL"),
        ]

        all_passed = True
        print("\n--- Running Foreign Key Integrity Validation ---")

        for label, sql in checks:
            res = val.query_one(sql)
            count = res.get("c", 0) if res else 0
            if count == 0:
                print(f"  [PASS] {label}")
            else:
                print(f"  [FAIL] {label}: {count} orphaned records found!")
                all_passed = False

        val.disconnect()
        return all_passed
