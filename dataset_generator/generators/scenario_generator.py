"""
dataset_generator/generators/scenario_generator.py
Embeds controlled forensic scenarios A–J into the synthetic dataset.
"""
import random
from datetime import datetime, timedelta, date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.base_generator import BaseGenerator
from generators.report_generator import ReportGenerator


class ScenarioGenerator(BaseGenerator):

    def inject_scenarios(self, scenario_counts: dict, case_ids: list, officer_ids: list,
                         examiner_ids: list, lab_ids: list) -> dict:
        """Inject controlled scenarios A through J into designated cases and evidence items."""
        if self.dry_run:
            print("  [DRY RUN] Injected scenario instances.")
            return {s: scenario_counts.get(s, 0) for s in "ABCDEFGHIJ"}
        self.connect()

        summary = {s: 0 for s in "ABCDEFGHIJ"}

        # Select distinct cases for scenario embedding
        available_cases = list(case_ids)
        random.shuffle(available_cases)

        # ── SCENARIO A: Normal Clean Evidence ───────────────────────
        count_a = scenario_counts.get("A", 5)
        for _ in range(count_a):
            if available_cases:
                cid = available_cases.pop()
                self._create_scenario_a(cid, officer_ids, examiner_ids)
                summary["A"] += 1

        # ── SCENARIO B: Hash Mismatch (Tamper Detected) ────────────
        count_b = scenario_counts.get("B", 5)
        for _ in range(count_b):
            if available_cases:
                cid = available_cases.pop()
                self._create_scenario_b(cid, officer_ids)
                summary["B"] += 1

        # ── SCENARIO C: Custody Delay (Temporal Anomaly) ───────────
        count_c = scenario_counts.get("C", 5)
        for _ in range(count_c):
            if available_cases:
                cid = available_cases.pop()
                self._create_scenario_c(cid, officer_ids)
                summary["C"] += 1

        # ── SCENARIO D: Derived Evidence Cascade ───────────────────
        count_d = scenario_counts.get("D", 3)
        for _ in range(count_d):
            if available_cases:
                cid = available_cases.pop()
                self._create_scenario_d(cid, officer_ids)
                summary["D"] += 1

        # ── SCENARIO E: Expiring Biological Evidence ───────────────
        count_e = scenario_counts.get("E", 5)
        for _ in range(count_e):
            if available_cases:
                cid = available_cases.pop()
                self._create_scenario_e(cid, officer_ids)
                summary["E"] += 1

        # ── SCENARIO F: Overdue Examination ───────────────────────
        count_f = scenario_counts.get("F", 5)
        for _ in range(count_f):
            if available_cases:
                cid = available_cases.pop()
                self._create_scenario_f(cid, officer_ids, examiner_ids)
                summary["F"] += 1

        # ── SCENARIO G: Dead-Man Inactivity Switch ─────────────────
        count_g = scenario_counts.get("G", 3)
        for _ in range(count_g):
            if available_cases:
                cid = available_cases.pop()
                self._create_scenario_g(cid, officer_ids)
                summary["G"] += 1

        # ── SCENARIO H: Normal Clean Case ──────────────────────────
        count_h = scenario_counts.get("H", 5)
        for _ in range(count_h):
            if available_cases:
                cid = available_cases.pop()
                self._create_scenario_h(cid, officer_ids, examiner_ids)
                summary["H"] += 1

        # ── SCENARIO I: Multiple Anomalies Case ────────────────────
        count_i = scenario_counts.get("I", 3)
        for _ in range(count_i):
            if available_cases:
                cid = available_cases.pop()
                self._create_scenario_i(cid, officer_ids, examiner_ids)
                summary["I"] += 1

        # ── SCENARIO J: Ambiguous / Insufficient Evidence ───────────
        count_j = scenario_counts.get("J", 5)
        for _ in range(count_j):
            if available_cases:
                cid = available_cases.pop()
                self._create_scenario_j(cid, officer_ids)
                summary["J"] += 1

        self.disconnect()
        return summary

    # ── Scenario Implementation Helpers ───────────────────────

    def _get_scene(self, case_id: int) -> int:
        scenes = self.query("SELECT scene_id FROM CrimeScene WHERE case_id = %s", (case_id,))
        return scenes[0]["scene_id"] if scenes else 1

    def _create_scenario_a(self, case_id: int, officer_ids: list, examiner_ids: list):
        """Scenario A: Normal Clean Evidence"""
        off = random.choice(officer_ids)
        sc = self._get_scene(case_id)
        eid = self.execute(
            """INSERT INTO Evidence (case_id, description, type_id, collection_datetime, scene_id, collected_by, current_status)
               VALUES (%s, 'Clean physical evidence item', 3, NOW(), %s, %s, 'In Storage')""",
            (case_id, sc, off)
        )
        self.execute(
            """INSERT INTO CustodyLog (evidence_id, transferred_by, received_by, transfer_datetime, reason, condition_at_transfer)
               VALUES (%s, %s, %s, NOW(), 'Initial collection', 'Sealed, intact')""",
            (eid, off, off)
        )

    def _create_scenario_b(self, case_id: int, officer_ids: list):
        """Scenario B: Hash Mismatch (Tamper Incident)"""
        off = random.choice(officer_ids)
        sc = self._get_scene(case_id)
        original_hash = self.sha256(f"original_digital_content_{case_id}")

        eid = self.execute(
            """INSERT INTO Evidence (case_id, description, type_id, collection_datetime, scene_id, collected_by, hash_value, current_status)
               VALUES (%s, 'Digital drive with hash integrity check', 2, NOW(), %s, %s, %s, 'Compromised')""",
            (case_id, sc, off, original_hash)
        )
        self.execute(
            """INSERT INTO TamperIncident (evidence_id, reported_by, description, severity, resolution_status)
               VALUES (%s, %s, 'SHA-256 hash mismatch detected during verification check.', 'Critical', 'Open')""",
            (eid, off)
        )
        self.execute(
            """INSERT INTO AlertLog (alert_type, evidence_id, officer_id, message)
               VALUES ('HashMismatch', %s, %s, 'HASH MISMATCH ALERT: Evidence SHA-256 integrity check failed.')""",
            (eid, off)
        )

    def _create_scenario_c(self, case_id: int, officer_ids: list):
        """Scenario C: Custody Delay (Temporal Anomaly)"""
        off1, off2 = random.sample(officer_ids, 2)
        sc = self._get_scene(case_id)
        eid = self.execute(
            """INSERT INTO Evidence (case_id, description, type_id, collection_datetime, scene_id, collected_by, current_status)
               VALUES (%s, 'Physical evidence with delayed custody logging', 3, NOW(), %s, %s, 'In Storage')""",
            (case_id, sc, off1)
        )
        trans_dt = datetime.now() - timedelta(days=2)
        rec_dt = trans_dt + timedelta(hours=14)  # 14 hour gap (> 4 hours)

        self.execute(
            """INSERT INTO CustodyLog (evidence_id, transferred_by, received_by, transfer_datetime, recorded_datetime, reason, condition_at_transfer)
               VALUES (%s, %s, %s, %s, %s, 'Transfer to central vault', 'Packaging intact')""",
            (eid, off1, off2, trans_dt.strftime("%Y-%m-%d %H:%M:%S"), rec_dt.strftime("%Y-%m-%d %H:%M:%S"))
        )

    def _create_scenario_d(self, case_id: int, officer_ids: list):
        """Scenario D: Derived Evidence Cascade"""
        off = random.choice(officer_ids)
        sc = self._get_scene(case_id)

        parent_id = self.execute(
            """INSERT INTO Evidence (case_id, description, type_id, collection_datetime, scene_id, collected_by, current_status)
               VALUES (%s, 'Parent seized laptop computer', 2, NOW(), %s, %s, 'Compromised')""",
            (case_id, sc, off)
        )
        child_id = self.execute(
            """INSERT INTO Evidence (case_id, description, type_id, collection_datetime, scene_id, collected_by, parent_evidence_id, current_status)
               VALUES (%s, 'Child extracted hard drive image', 2, NOW(), %s, %s, %s, 'Compromised')""",
            (case_id, sc, off, parent_id)
        )

        self.execute(
            """INSERT INTO AlertLog (alert_type, evidence_id, message)
               VALUES ('Tamper', %s, 'TAMPER CASCADE: Parent evidence compromised; derived evidence auto-flagged.')""",
            (child_id,)
        )

    def _create_scenario_e(self, case_id: int, officer_ids: list):
        """Scenario E: Expiring Biological Evidence"""
        off = random.choice(officer_ids)
        sc = self._get_scene(case_id)
        exp_date = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")

        eid = self.execute(
            """INSERT INTO Evidence (case_id, description, type_id, collection_datetime, scene_id, collected_by, expiry_date, current_status)
               VALUES (%s, 'Biological blood sample nearing expiration', 1, NOW(), %s, %s, %s, 'In Storage')""",
            (case_id, sc, off, exp_date)
        )
        self.execute(
            """INSERT INTO AlertLog (alert_type, evidence_id, officer_id, message)
               VALUES ('Expiry', %s, %s, 'EXPIRY WARNING: Biological evidence expires in 3 days.')""",
            (eid, off)
        )

    def _create_scenario_f(self, case_id: int, officer_ids: list, examiner_ids: list):
        """Scenario F: Overdue Examination"""
        off = random.choice(officer_ids)
        ex = random.choice(examiner_ids)
        sc = self._get_scene(case_id)

        eid = self.execute(
            """INSERT INTO Evidence (case_id, description, type_id, collection_datetime, scene_id, collected_by, current_status)
               VALUES (%s, 'Evidence assigned for DNA analysis (Overdue)', 1, NOW(), %s, %s, 'In Lab')""",
            (case_id, sc, off)
        )
        start_d = (date.today() - timedelta(days=35)).strftime("%Y-%m-%d")

        ex_id = self.execute(
            """INSERT INTO Examination (evidence_id, examiner_id, exam_type_id, start_date, status)
               VALUES (%s, %s, 1, %s, 'Overdue')""",
            (eid, ex, start_d)
        )
        self.execute(
            """INSERT INTO AlertLog (alert_type, evidence_id, officer_id, message)
               VALUES ('Overdue', %s, %s, 'OVERDUE: Examination pending for 35 days (SLA: 21 days).')""",
            (eid, off)
        )

    def _create_scenario_g(self, case_id: int, officer_ids: list):
        """Scenario G: Dead-Man Switch"""
        off = random.choice(officer_ids)
        sc = self._get_scene(case_id)

        eid = self.execute(
            """INSERT INTO Evidence (case_id, description, type_id, collection_datetime, scene_id, collected_by, current_status)
               VALUES (%s, 'Evidence item with zero activity for >30 days', 3, NOW() - INTERVAL 45 DAY, %s, %s, 'In Storage')""",
            (case_id, sc, off)
        )
        old_dt = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d %H:%M:%S")

        self.execute(
            """INSERT INTO CustodyLog (evidence_id, transferred_by, received_by, transfer_datetime, reason, condition_at_transfer)
               VALUES (%s, %s, %s, %s, 'Initial collection', 'Sealed')""",
            (eid, off, off, old_dt)
        )
        self.execute(
            """INSERT INTO AlertLog (alert_type, evidence_id, officer_id, message)
               VALUES ('DeadManSwitch', %s, %s, 'DEAD MAN SWITCH: Zero activity for 40 days.')""",
            (eid, off)
        )

    def _create_scenario_h(self, case_id: int, officer_ids: list, examiner_ids: list):
        """Scenario H: Normal Clean Case"""
        off = random.choice(officer_ids)
        ex = random.choice(examiner_ids)
        sc = self._get_scene(case_id)

        eid = self.execute(
            """INSERT INTO Evidence (case_id, description, type_id, collection_datetime, scene_id, collected_by, current_status)
               VALUES (%s, 'Clean physical evidence in pristine condition', 3, NOW(), %s, %s, 'In Storage')""",
            (case_id, sc, off)
        )
        self.execute(
            """INSERT INTO CustodyLog (evidence_id, transferred_by, received_by, transfer_datetime, reason, condition_at_transfer)
               VALUES (%s, %s, %s, NOW(), 'Initial collection', 'Sealed, intact')""",
            (eid, off, off)
        )

    def _create_scenario_i(self, case_id: int, officer_ids: list, examiner_ids: list):
        """Scenario I: Multiple Anomalies Case (Scenarios B + C + F combined)"""
        self._create_scenario_b(case_id, officer_ids)
        self._create_scenario_c(case_id, officer_ids)
        self._create_scenario_f(case_id, officer_ids, examiner_ids)

    def _create_scenario_j(self, case_id: int, officer_ids: list):
        """Scenario J: Ambiguous / Insufficient Evidence"""
        off = random.choice(officer_ids)
        sc = self._get_scene(case_id)

        # Insert item with minimal metadata and NO custody/examination reports
        self.execute(
            """INSERT INTO Evidence (case_id, description, type_id, collection_datetime, scene_id, collected_by, current_status)
               VALUES (%s, 'Ambiguous item recovered with incomplete records', 3, NOW(), %s, %s, 'Collected')""",
            (case_id, sc, off)
        )
