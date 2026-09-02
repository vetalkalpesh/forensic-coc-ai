"""
dataset_generator/generators/custody_generator.py
Generates CustodyLog and CustodyTransfer records with chronological consistency.

FIX (2026-08-26): The MySQL trigger `trg_transfer_lock` fires BEFORE each INSERT
and validates that the new `transferred_by` equals the last `received_by` for that
evidence_id. When rows are batch-inserted via executemany(), MySQL still fires the
trigger per-row, but the "last log for this evidence" lookup within an uncommitted
batch can see rows from earlier in the same batch belonging to DIFFERENT evidence items
inserted in an unexpected order — causing false chain-of-custody violations.

Solution: Insert each evidence item's chain ONE ROW AT A TIME, committing after each
evidence item's complete chain before starting the next evidence item. This guarantees
the trigger always sees a clean, committed state.
"""
import random
from datetime import timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.base_generator import BaseGenerator
from config import NORMAL_RECORDING_DELAY_HOURS


TRANSFER_REASONS = [
    "Initial collection at crime scene",
    "Transfer to central storage vault",
    "Transfer to forensic laboratory for examination",
    "Return to secure storage after lab analysis",
    "Transfer to court for evidence presentation",
    "Return from court after hearing",
    "Transfer between departments for custody handover",
]

CONDITIONS = [
    "Sealed in sterile evidence bag, labelled",
    "Intact, original seals unbroken",
    "Sealed in anti-static container",
    "Packaging intact, condition good",
    "Slight outer packaging wear, inner seal intact",
]

TRANSFER_MODES = [
    "Hand Delivery with Receipt",
    "Sealed Courier",
    "Court Order Transfer",
]


class CustodyGenerator(BaseGenerator):

    def generate_custody_chains(self, count: int, evidence_ids: list, officer_ids: list, dept_ids: list) -> list:
        """Generate chronological custody chain logs and transfer records.

        IMPORTANT: Rows are inserted ONE EVIDENCE AT A TIME and committed after each
        evidence chain to satisfy the trg_transfer_lock trigger which requires that
        each new transferred_by equals the last received_by for that evidence_id.
        """
        if self.dry_run:
            print("  [DRY RUN] Generated %d custody transfer logs." % count)
            return list(range(1, count + 1))
        self.connect()

        # Retrieve evidence details (collection datetime, collected_by)
        evidence_list = self.query(
            "SELECT evidence_id, collection_datetime, collected_by FROM Evidence WHERE evidence_id IN (%s)"
            % ",".join(map(str, evidence_ids))
        ) if evidence_ids else self.query("SELECT evidence_id, collection_datetime, collected_by FROM Evidence")

        all_log_ids = []
        total_evidence = len(evidence_list)

        for idx, ev in enumerate(evidence_list):
            eid = ev["evidence_id"]
            col_dt = ev["collection_datetime"]
            collector = ev["collected_by"]

            # Check if there is already a custody log entry for this evidence item
            last_log = self.query(
                "SELECT received_by, transfer_datetime FROM CustodyLog WHERE evidence_id = %s ORDER BY transfer_datetime DESC LIMIT 1",
                (eid,)
            )

            if last_log:
                current_holder = last_log[0]["received_by"]
                curr_time = last_log[0]["transfer_datetime"]
            else:
                # ── Step 1: Insert initial collection log ──────────────
                rec_dt = col_dt + timedelta(hours=random.uniform(*NORMAL_RECORDING_DELAY_HOURS))
                log_id = self._insert_custody_log(
                    eid, collector, collector,
                    col_dt, rec_dt,
                    "Initial collection at crime scene",
                    random.choice(CONDITIONS)
                )
                all_log_ids.append(log_id)
                current_holder = collector
                curr_time = col_dt

            # ── Step 2: Insert subsequent transfer steps ───────────
            num_steps = random.randint(1, 4)

            for step in range(num_steps):
                curr_time += timedelta(days=random.randint(1, 10), hours=random.randint(1, 12))

                # Next holder MUST be the current holder (already received) — but we want to
                # transfer TO someone else. The trigger requires transferred_by == last received_by,
                # which is current_holder. So transferred_by = current_holder is always valid.
                candidates = [o for o in officer_ids if o != current_holder]
                next_holder = random.choice(candidates) if candidates else current_holder

                rec_time = curr_time + timedelta(hours=random.uniform(*NORMAL_RECORDING_DELAY_HOURS))
                reason = random.choice(TRANSFER_REASONS[1:])
                cond = random.choice(CONDITIONS)

                transfer_log_id = self._insert_custody_log(
                    eid, current_holder, next_holder,
                    curr_time, rec_time,
                    reason, cond
                )
                all_log_ids.append(transfer_log_id)

                # Insert CustodyTransfer detail for this step
                from_dept = random.choice(dept_ids)
                to_dept = random.choice([d for d in dept_ids if d != from_dept] or dept_ids)
                mode = random.choice(TRANSFER_MODES)
                authorizer = random.choice(officer_ids)
                self._insert_custody_transfer(transfer_log_id, from_dept, to_dept, mode, authorizer)

                current_holder = next_holder

            # Commit after EACH evidence item's complete chain
            self._conn.commit()
            self.print_progress("Custody Logs", idx + 1, total_evidence)

        self.disconnect()
        return all_log_ids

    def _insert_custody_log(self, evidence_id, transferred_by, received_by,
                             transfer_dt, recorded_dt, reason, condition) -> int:
        """Insert a single CustodyLog row and return its log_id.
        Does NOT commit — caller commits after the full evidence chain.
        """
        sql = """INSERT INTO CustodyLog
                    (evidence_id, transferred_by, received_by,
                     transfer_datetime, recorded_datetime, reason, condition_at_transfer)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        params = (
            evidence_id, transferred_by, received_by,
            transfer_dt.strftime("%Y-%m-%d %H:%M:%S"),
            recorded_dt.strftime("%Y-%m-%d %H:%M:%S"),
            reason, condition
        )
        self._cur.execute(sql, params)
        return self._cur.lastrowid

    def _insert_custody_transfer(self, log_id, from_dept, to_dept, mode, authorized_by):
        """Insert a CustodyTransfer row. Does NOT commit."""
        sql = """INSERT INTO CustodyTransfer
                    (log_id, from_department_id, to_department_id, transfer_mode, authorized_by)
                 VALUES (%s, %s, %s, %s, %s)"""
        self._cur.execute(sql, (log_id, from_dept, to_dept, mode, authorized_by))
