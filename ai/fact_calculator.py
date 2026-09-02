"""
ai/fact_calculator.py
Executes SQL queries and stored procedures to calculate objective forensic facts.
Enforces Rule 8: LLM is NEVER permitted to perform numeric or status calculations;
all database facts are pre-calculated by MySQL and injected as verified truths.
"""
import mysql.connector
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.config import DB_CONFIG
from ai.anomaly_detector import detect_custody_anomalies

class FactCalculator:

    def __init__(self, db_config: dict = None):
        self.db_cfg = db_config or DB_CONFIG

    def _conn(self):
        return mysql.connector.connect(**self.db_cfg)

    def calculate_custody_delays(self, evidence_id: int = None) -> list:
        """Calculate transfer delay in hours using MySQL TIMESTAMPDIFF."""
        try:
            conn = self._conn()
            cur = conn.cursor(dictionary=True)
            try:
                sql = """
                    SELECT cl.log_id, cl.evidence_id, e.description,
                           o1.full_name AS from_officer, o2.full_name AS to_officer,
                           cl.transfer_datetime, cl.recorded_datetime,
                           TIMESTAMPDIFF(HOUR, cl.transfer_datetime, cl.recorded_datetime) AS delay_hours,
                           CASE WHEN TIMESTAMPDIFF(HOUR, cl.transfer_datetime, cl.recorded_datetime) > 4
                                THEN 'SUSPICIOUS GAP' ELSE 'Normal' END AS delay_flag
                    FROM CustodyLog cl JOIN Evidence e ON cl.evidence_id=e.evidence_id
                    JOIN Officer o1 ON cl.transferred_by=o1.officer_id
                    JOIN Officer o2 ON cl.received_by=o2.officer_id
                """
                params = ()
                if evidence_id:
                    sql += " WHERE cl.evidence_id = %s"
                    params = (evidence_id,)
                sql += " ORDER BY cl.transfer_datetime DESC"

                cur.execute(sql, params)
                return cur.fetchall()
            finally:
                cur.close(); conn.close()
        except mysql.connector.Error as e:
            print(f"[FactCalculator] DB Notice: {e}")
            return []

    def calculate_expiry_status(self, evidence_id: int = None) -> list:
        """Calculate biological evidence degradation and remaining days using DATEDIFF."""
        conn = self._conn()
        cur = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT e.evidence_id, e.description, e.expiry_date,
                       DATEDIFF(e.expiry_date, CURDATE()) AS days_remaining,
                       CASE WHEN DATEDIFF(e.expiry_date, CURDATE()) < 0 THEN 'Expired'
                            WHEN DATEDIFF(e.expiry_date, CURDATE()) <= 7 THEN 'Expiring Soon'
                            ELSE 'Normal' END AS expiry_status
                FROM Evidence e WHERE e.expiry_date IS NOT NULL
            """
            params = ()
            if evidence_id:
                sql += " AND e.evidence_id = %s"
                params = (evidence_id,)

            cur.execute(sql, params)
            return cur.fetchall()
        finally:
            cur.close(); conn.close()

    def calculate_overdue_examinations(self) -> list:
        """Calculate SLA breach for pending examinations using DATEDIFF."""
        conn = self._conn()
        cur = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT ex.exam_id, e.evidence_id, e.description, ext.type_name AS exam_type,
                       ex.start_date, DATEDIFF(CURDATE(), ex.start_date) AS days_pending,
                       ext.typical_duration_days AS sla_days,
                       (DATEDIFF(CURDATE(), ex.start_date) - ext.typical_duration_days) AS overdue_days
                FROM Examination ex JOIN Evidence e ON ex.evidence_id=e.evidence_id
                JOIN ExaminationType ext ON ex.exam_type_id=ext.type_id
                LEFT JOIN ExaminationReport er ON er.exam_id=ex.exam_id
                WHERE er.report_id IS NULL AND DATEDIFF(CURDATE(), ex.start_date) > ext.typical_duration_days
            """
            cur.execute(sql)
            return cur.fetchall()
        finally:
            cur.close(); conn.close()

    def verify_hash(self, evidence_id: int, test_hash: str) -> str:
        """Executes stored procedure verify_evidence_hash to compute integrity result."""
        conn = self._conn()
        cur = conn.cursor()
        try:
            args = cur.callproc("verify_evidence_hash", [evidence_id, test_hash, ""])
            conn.commit()
            return args[2]  # OUT parameter result
        finally:
            cur.close(); conn.close()

    def calculate_dead_man_inactivity(self, evidence_id: int = None) -> list:
        """Calculate inactivity days on active cases using MAX(transfer_datetime)."""
        conn = self._conn()
        cur = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT e.evidence_id, e.description,
                       MAX(cl.transfer_datetime) AS last_activity,
                       DATEDIFF(CURDATE(), MAX(cl.transfer_datetime)) AS inactive_days,
                       CASE WHEN DATEDIFF(CURDATE(), MAX(cl.transfer_datetime)) > 30 THEN 'DEAD MAN TRIGGERED' ELSE 'Active' END AS status
                FROM Evidence e
                JOIN CriminalCase cc ON e.case_id=cc.case_id
                JOIN CaseStatus cs ON cc.status_id=cs.status_id
                JOIN CustodyLog cl ON cl.evidence_id=e.evidence_id
                WHERE cs.label NOT IN ('Closed','Acquitted')
                  AND e.current_status NOT IN ('Archived','Expired','Compromised')
            """
            params = ()
            if evidence_id:
                sql += " AND e.evidence_id = %s"
                params = (evidence_id,)
            sql += " GROUP BY e.evidence_id, e.description HAVING inactive_days > 30"

            cur.execute(sql, params)
            return cur.fetchall()
        finally:
            cur.close(); conn.close()

    def calculate_geospatial_anomalies(self, evidence_id: int = None) -> list:
        """Calculate temporal and geospatial custody anomalies using deterministic Haversine distance & transfer timestamps."""
        conn = self._conn()
        cur = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT cl.log_id, cl.evidence_id, cl.transfer_datetime,
                       d1.dept_name AS from_dept_name, d2.dept_name AS to_dept_name,
                       d1.latitude AS from_lat, d1.longitude AS from_lon,
                       d2.latitude AS to_lat, d2.longitude AS to_lon
                FROM CustodyLog cl
                JOIN CustodyTransfer ct ON cl.log_id = ct.log_id
                LEFT JOIN Department d1 ON ct.from_department_id = d1.dept_id
                LEFT JOIN Department d2 ON ct.to_department_id = d2.dept_id
            """
            params = ()
            if evidence_id:
                sql += " WHERE cl.evidence_id = %s"
                params = (evidence_id,)
            sql += " ORDER BY cl.transfer_datetime ASC"

            cur.execute(sql, params)
            transfers = cur.fetchall()
            if not transfers:
                return []

            # Group transfers by evidence_id
            by_evidence = {}
            for t in transfers:
                eid = t["evidence_id"]
                if eid not in by_evidence:
                    by_evidence[eid] = []
                by_evidence[eid].append(t)

            all_anomalies = []
            for eid, ev_transfers in by_evidence.items():
                result = detect_custody_anomalies(ev_transfers, evidence_id=eid)
                all_anomalies.extend(result.get("anomalies", []))

            return all_anomalies
        finally:
            cur.close(); conn.close()

