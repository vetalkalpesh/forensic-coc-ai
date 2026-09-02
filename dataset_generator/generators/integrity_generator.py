"""
dataset_generator/generators/integrity_generator.py
Generates TamperIncident, AlertLog, EscalationLog, and AuditLog records.
"""
import random
from datetime import timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.base_generator import BaseGenerator
from config import TAMPER_SEVERITY_WEIGHTS


TAMPER_DESCRIPTIONS = [
    "Scratch marks observed on blade/surface during lab examination. Possible post-collection damage.",
    "Anti-static bag seal appears to have been opened and resealed. Hash verification pending.",
    "Weight discrepancy noted — recorded weight at collection differs from lab measurement.",
    "Packaging seal torn during transit. Evidence exposure suspected.",
    "SHA-256 hash mismatch detected during integrity audit.",
    "Unauthorized access attempt to digital evidence storage volume.",
    "Temperature spike recorded in biological storage freezer unit.",
]

ALERT_TYPES = [
    "Expiry", "Tamper", "Overdue", "Escalation", "HashMismatch", "DeadManSwitch"
]


class IntegrityGenerator(BaseGenerator):

    def generate_integrity_records(self, tamper_count: int, alert_count: int,
                                    evidence_ids: list, officer_ids: list) -> tuple:
        """Generate TamperIncident, AlertLog, EscalationLog, and AuditLog records."""
        if self.dry_run:
            print("  [DRY RUN] Generated %d tamper incidents and %d alert logs." % (tamper_count, alert_count))
            return list(range(1, tamper_count + 1)), list(range(1, alert_count + 1))
        self.connect()

        severities = list(TAMPER_SEVERITY_WEIGHTS.keys())
        sev_weights = list(TAMPER_SEVERITY_WEIGHTS.values())

        # Generate TamperIncident
        tamper_rows = []
        high_critical_incidents = []

        for i in range(tamper_count):
            eid = random.choice(evidence_ids)
            reported_by = random.choice(officer_ids)
            rep_dt = self.fake.date_time_between(start_date="-1y", end_date="now")
            desc = random.choice(TAMPER_DESCRIPTIONS)
            sev = random.choices(severities, weights=sev_weights, k=1)[0]
            status = random.choice(["Open", "Under Investigation", "Resolved"])
            res_on = (rep_dt + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d") if status == "Resolved" else None

            tamper_rows.append((
                eid, reported_by, rep_dt.strftime("%Y-%m-%d %H:%M:%S"),
                desc, sev, status, res_on
            ))
            if sev in ("High", "Critical"):
                high_critical_incidents.append(i + 1)  # temp index

            self.print_progress("Tamper Incidents", i + 1, tamper_count)

        max_before = self.query_one("SELECT MAX(incident_id) AS mx FROM TamperIncident")
        min_new_incident_id = (max_before["mx"] or 0) + 1

        self.execute_many(
            """INSERT INTO TamperIncident (evidence_id, reported_by, reported_datetime, description, severity, resolution_status, resolved_on)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            tamper_rows
        )

        inserted_tampers = self.query(
            "SELECT incident_id, severity FROM TamperIncident WHERE incident_id >= %s ORDER BY incident_id",
            (min_new_incident_id,)
        )
        tamper_ids = [r["incident_id"] for r in inserted_tampers]

        # Generate EscalationLog for High/Critical incidents
        esc_rows = []
        for incident in inserted_tampers:
            if incident["severity"] in ("High", "Critical"):
                iid = incident["incident_id"]
                esc_to = random.choice(officer_ids)
                reason = "Escalated to supervisor due to high-severity integrity risk."
                esc_rows.append((iid, esc_to, reason))

        self.execute_many(
            "INSERT INTO EscalationLog (incident_id, escalated_to, reason) VALUES (%s,%s,%s)",
            esc_rows
        )

        # Generate AlertLog
        alert_rows = []
        for i in range(alert_count):
            atype = random.choice(ALERT_TYPES)
            eid = random.choice(evidence_ids) if random.random() > 0.1 else None
            oid = random.choice(officer_ids) if random.random() > 0.1 else None
            msg = f"{atype.upper()} ALERT: Event recorded for evidence E{eid or 0:03d}."
            ack = 1 if random.random() > 0.4 else 0

            alert_rows.append((atype, eid, oid, msg, ack))

            self.print_progress("Alert Logs", i + 1, alert_count)

        self.execute_many(
            "INSERT INTO AlertLog (alert_type, evidence_id, officer_id, message, is_acknowledged) VALUES (%s,%s,%s,%s,%s)",
            alert_rows
        )

        # Generate AuditLog entries
        audit_rows = []
        for i in range(min(100, len(evidence_ids))):
            eid = evidence_ids[i]
            by = random.choice(officer_ids)
            audit_rows.append((
                "Evidence", eid,
                '{"status":"Collected"}', '{"status":"In Storage"}',
                by
            ))

        self.execute_many(
            "INSERT INTO AuditLog (table_name, record_id, old_values, new_values, changed_by) VALUES (%s,%s,%s,%s,%s)",
            audit_rows
        )

        alerts = self.query("SELECT alert_id FROM AlertLog")
        self.disconnect()
        return tamper_ids, [r["alert_id"] for r in alerts]
