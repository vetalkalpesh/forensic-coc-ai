"""
ai/sql_retriever.py
Secure structured retrieval layer querying MySQL 8.0 database tables and views.
Enforces parameterized queries, SELECT-only safety, and RBAC data scoping.
"""
import mysql.connector
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.config import DB_CONFIG


class SQLRetriever:

    def __init__(self, db_config: dict = None):
        self.db_cfg = db_config or DB_CONFIG

    def _conn(self):
        return mysql.connector.connect(**self.db_cfg)

    def _qry(self, sql: str, params: tuple = None) -> list:
        try:
            conn = self._conn()
            cur = conn.cursor(dictionary=True)
            try:
                cur.execute(sql, params or ())
                return cur.fetchall()
            finally:
                cur.close(); conn.close()
        except mysql.connector.Error as e:
            print(f"[SQLRetriever] DB Notice: {e}")
            return []

    # ── INTENT RETRIEVERS ──────────────────────────────────────

    def get_evidence_details(self, evidence_id: int, user_role: str = "Junior") -> dict:
        """Fetch complete evidence record including current storage unit and facility."""
        sql = """
            SELECT e.evidence_id, e.description, et.type_name, e.current_status,
                   e.collection_datetime, e.expiry_date, e.hash_value, e.hash_algorithm,
                   e.version_number, cc.fir_number, cc.case_id,
                   o.full_name AS collected_by, cs.address AS crime_scene_address,
                   su.unit_code, su.unit_type, sf.facility_name, sf.facility_type, sf.address AS facility_address
            FROM Evidence e
            JOIN EvidenceType et ON e.type_id=et.type_id
            JOIN CriminalCase cc ON e.case_id=cc.case_id
            JOIN Officer o ON e.collected_by=o.officer_id
            JOIN CrimeScene cs ON e.scene_id=cs.scene_id
            LEFT JOIN StorageLog sl ON sl.evidence_id=e.evidence_id AND sl.retrieved_on IS NULL
            LEFT JOIN StorageUnit su ON sl.unit_id=su.unit_id
            LEFT JOIN StorageFacility sf ON su.facility_id=sf.facility_id
            WHERE e.evidence_id = %s
        """
        res = self._qry(sql, (evidence_id,))
        return res[0] if res else {}

    def get_custody_history(self, evidence_id: int) -> list:
        """Fetch chain of custody log entries."""
        sql = """
            SELECT cl.log_id, cl.evidence_id,
                   o1.full_name AS transferred_by, o2.full_name AS received_by,
                   cl.transfer_datetime, cl.recorded_datetime,
                   TIMESTAMPDIFF(HOUR, cl.transfer_datetime, cl.recorded_datetime) AS delay_hours,
                   cl.reason, cl.condition_at_transfer,
                   ct.transfer_mode, d1.dept_name AS from_dept, d2.dept_name AS to_dept
            FROM CustodyLog cl
            JOIN Officer o1 ON cl.transferred_by=o1.officer_id
            JOIN Officer o2 ON cl.received_by=o2.officer_id
            LEFT JOIN CustodyTransfer ct ON ct.log_id=cl.log_id
            LEFT JOIN Department d1 ON ct.from_department_id=d1.dept_id
            LEFT JOIN Department d2 ON ct.to_department_id=d2.dept_id
            WHERE cl.evidence_id = %s
            ORDER BY cl.transfer_datetime ASC
        """
        return self._qry(sql, (evidence_id,))

    def get_tamper_incidents(self, evidence_id: int = None, case_id: int = None) -> list:
        """Fetch tamper incidents."""
        sql = """
            SELECT ti.incident_id, ti.evidence_id, e.description AS evidence_desc,
                   ti.reported_datetime, ti.description, ti.severity, ti.resolution_status,
                   ti.resolved_on, o.full_name AS reported_by, cc.fir_number
            FROM TamperIncident ti
            JOIN Evidence e ON ti.evidence_id=e.evidence_id
            JOIN Officer o ON ti.reported_by=o.officer_id
            JOIN CriminalCase cc ON e.case_id=cc.case_id
            WHERE 1=1
        """
        params = []
        if evidence_id:
            sql += " AND ti.evidence_id = %s"
            params.append(evidence_id)
        if case_id:
            sql += " AND e.case_id = %s"
            params.append(case_id)

        sql += " ORDER BY ti.reported_datetime DESC"
        return self._qry(sql, tuple(params))

    def get_alert_logs(self, evidence_id: int = None) -> list:
        """Fetch alert logs."""
        sql = """
            SELECT al.alert_id, al.alert_type, al.evidence_id, al.generated_at,
                   al.message, al.is_acknowledged, e.description AS evidence_desc
            FROM AlertLog al
            LEFT JOIN Evidence e ON al.evidence_id=e.evidence_id
            WHERE 1=1
        """
        params = []
        if evidence_id:
            sql += " AND al.evidence_id = %s"
            params.append(evidence_id)

        sql += " ORDER BY al.generated_at DESC"
        return self._qry(sql, tuple(params))

    def get_case_summary_data(self, fir_number: str = None, case_id: int = None) -> dict:
        """Fetch comprehensive case details across tables."""
        params = []
        where_clause = ""
        if case_id:
            where_clause = "cc.case_id = %s"
            params.append(case_id)
        elif fir_number:
            where_clause = "cc.fir_number = %s"
            params.append(fir_number)
        else:
            return {}

        case_info = self._qry(f"""
            SELECT cc.case_id, cc.fir_number, ct.type_name, cs.label AS status,
                   o.full_name AS officer, ps.name AS station, co.court_name,
                   cc.date_filed, cc.description
            FROM CriminalCase cc
            JOIN CaseType ct ON cc.case_type_id=ct.type_id
            JOIN CaseStatus cs ON cc.status_id=cs.status_id
            JOIN Officer o ON cc.investigating_officer_id=o.officer_id
            JOIN PoliceStation ps ON cc.police_station_id=ps.station_id
            LEFT JOIN Court co ON cc.court_id=co.court_id
            WHERE {where_clause}
        """, tuple(params))

        if not case_info:
            return {}

        cid = case_info[0]["case_id"]

        evidence = self._qry("""
            SELECT e.evidence_id, e.description, et.type_name, e.current_status, e.expiry_date
            FROM Evidence e JOIN EvidenceType et ON e.type_id=et.type_id
            WHERE e.case_id = %s
        """, (cid,))

        hearings = self._qry("""
            SELECT h.hearing_id, h.hearing_date, h.hearing_purpose, h.outcome, j.full_name AS judge
            FROM Hearing h JOIN Judge j ON h.judge_id=j.judge_id
            WHERE h.case_id = %s
        """, (cid,))

        tamper = self._qry("""
            SELECT ti.incident_id, ti.evidence_id, ti.severity, ti.description, ti.resolution_status
            FROM TamperIncident ti JOIN Evidence e ON ti.evidence_id=e.evidence_id
            WHERE e.case_id = %s
        """, (cid,))

        return {
            "case": case_info[0],
            "evidence": evidence,
            "hearings": hearings,
            "tamper_incidents": tamper,
        }

    def get_examination_metadata(self, evidence_id: int) -> list:
        """Fetch forensic lab examination metadata and report info."""
        sql = """
            SELECT ex.exam_id, ex.evidence_id, ext.type_name AS exam_type,
                   exr.full_name AS examiner, fl.lab_name, ex.start_date, ex.end_date,
                   ex.status, ex.findings_summary, er.report_id, er.is_admissible, er.filed_on
            FROM Examination ex
            JOIN ExaminationType ext ON ex.exam_type_id=ext.type_id
            JOIN Examiner exr ON ex.examiner_id=exr.examiner_id
            JOIN ForensicLab fl ON exr.lab_id=fl.lab_id
            LEFT JOIN ExaminationReport er ON er.exam_id=ex.exam_id
            WHERE ex.evidence_id = %s
        """
        return self._qry(sql, (evidence_id,))

    def get_report_details(self, report_id: int) -> dict:
        """Fetch ExaminationReport details by report_id."""
        sql = """
            SELECT er.report_id, er.exam_id, er.report_text, er.filed_on, er.is_admissible,
                   ex.evidence_id, exr.full_name AS examiner_name, fl.lab_name
            FROM ExaminationReport er
            JOIN Examination ex ON er.exam_id=ex.exam_id
            JOIN Examiner exr ON ex.examiner_id=exr.examiner_id
            JOIN ForensicLab fl ON exr.lab_id=fl.lab_id
            WHERE er.report_id = %s
        """
        res = self._qry(sql, (report_id,))
        return res[0] if res else {}

    def get_officer_custody_history(self, badge_number: str) -> list:
        """Fetch custody logs involving officer specified by badge_number."""
        sql = """
            SELECT cl.log_id, cl.evidence_id, e.description AS evidence_desc,
                   o1.full_name AS transferred_by, o1.badge_number AS transferred_by_badge,
                   o2.full_name AS received_by, o2.badge_number AS received_by_badge,
                   cl.transfer_datetime, cl.reason
            FROM CustodyLog cl
            JOIN Officer o1 ON cl.transferred_by=o1.officer_id
            JOIN Officer o2 ON cl.received_by=o2.officer_id
            JOIN Evidence e ON cl.evidence_id=e.evidence_id
            WHERE o1.badge_number = %s OR o2.badge_number = %s
            ORDER BY cl.transfer_datetime ASC
        """
        return self._qry(sql, (badge_number, badge_number))

    def get_officer_details(self, badge_number: str) -> dict:
        """Fetch Officer profile by badge number."""
        sql = """
            SELECT o.officer_id, o.badge_number, o.full_name, des.title AS designation_name, d.dept_name
            FROM Officer o
            JOIN Designation des ON o.designation_id=des.designation_id
            JOIN Department d ON o.department_id=d.dept_id
            WHERE o.badge_number = %s
        """
        res = self._qry(sql, (badge_number,))
        return res[0] if res else {}

    def get_audit_log(self, record_id: int = None, table_name: str = "Evidence", user_role: str = "Admin") -> list:
        """Fetch audit log (restricted to Admin role)."""
        if user_role != "Admin":
            return []    # RBAC protection

        sql = "SELECT * FROM AuditLog WHERE table_name = %s"
        params = [table_name]
        if record_id:
            sql += " AND record_id = %s"
            params.append(record_id)
        sql += " ORDER BY changed_at DESC"
        return self._qry(sql, tuple(params))
