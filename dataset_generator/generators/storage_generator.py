"""
dataset_generator/generators/storage_generator.py
Generates StorageFacility, StorageUnit, and StorageLog records.
"""
import random
from datetime import timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.base_generator import BaseGenerator


FACILITY_TYPES = [
    "Police Vault", "Forensic Storage", "Biohazard Cold Storage",
    "Court Archive", "Digital Secure Room"
]

UNIT_TYPES = [
    "Secure Vault", "Weapons Locker", "Freezer Unit",
    "Biological Freezer", "Document Archive", "Digital Server Room"
]

TEMP_RANGES = [
    "Ambient", "18C to 22C", "-4C to 4C", "-20C to -4C", "Controlled Humidity"
]


class StorageGenerator(BaseGenerator):

    def generate_facilities_and_units(self, fac_count: int, unit_count: int, dept_ids: list) -> tuple:
        """Generate storage facilities and storage units."""
        if self.dry_run:
            print("  [DRY RUN] Generated %d facilities and %d storage units." % (fac_count, unit_count))
            return list(range(1, fac_count + 1)), list(range(1, unit_count + 1))
        self.connect()

        # Generate StorageFacility
        fac_rows = []
        for i in range(fac_count):
            name = f"{self.fake.city()} Evidence Store #{i+1}"
            addr = f"{self.fake.street_address()}, {self.fake.city()}"
            ftype = random.choice(FACILITY_TYPES)
            dept = random.choice(dept_ids)
            fac_rows.append((name, addr, ftype, dept))

        max_f = self.query_one("SELECT MAX(facility_id) AS mx FROM StorageFacility")
        min_f_id = (max_f["mx"] or 0) + 1

        self.execute_many(
            "INSERT INTO StorageFacility (facility_name, address, facility_type, managing_dept_id) VALUES (%s,%s,%s,%s)",
            fac_rows
        )
        facs = self.query("SELECT facility_id FROM StorageFacility WHERE facility_id >= %s ORDER BY facility_id", (min_f_id,))
        fac_ids = [r["facility_id"] for r in facs]

        # Generate StorageUnit
        used_codes = set()
        existing_units = self.query("SELECT unit_code FROM StorageUnit")
        for r in existing_units:
            used_codes.add(r["unit_code"])

        unit_rows = []
        for i in range(unit_count):
            fac = random.choice(fac_ids)
            seq = i + 1
            code = f"SU-{seq:03d}"
            while code in used_codes:
                seq += 1
                code = f"SU-{seq:03d}"
            used_codes.add(code)

            utype = random.choice(UNIT_TYPES)
            cap = random.choice([20, 30, 50, 100, 200])
            temp = random.choice(TEMP_RANGES)
            unit_rows.append((fac, code, utype, cap, temp, 0))

        max_u = self.query_one("SELECT MAX(unit_id) AS mx FROM StorageUnit")
        min_u_id = (max_u["mx"] or 0) + 1

        self.execute_many(
            "INSERT INTO StorageUnit (facility_id, unit_code, unit_type, capacity, temperature_range, current_count) VALUES (%s,%s,%s,%s,%s,%s)",
            unit_rows
        )
        units = self.query("SELECT unit_id, capacity FROM StorageUnit WHERE unit_id >= %s ORDER BY unit_id", (min_u_id,))

        self.disconnect()
        return fac_ids, [r["unit_id"] for r in units]

    def generate_storage_logs(self, evidence_ids: list, unit_ids: list, officer_ids: list) -> list:
        """Generate StorageLog entries for stored evidence."""
        self.connect()

        # Query evidence collection dates
        evidence_list = self.query(
            "SELECT evidence_id, collection_datetime FROM Evidence WHERE evidence_id IN (%s)"
            % ",".join(map(str, evidence_ids))
        ) if evidence_ids else self.query("SELECT evidence_id, collection_datetime FROM Evidence")

        log_rows = []
        unit_counts = {uid: 0 for uid in unit_ids}

        for ev in evidence_list:
            eid = ev["evidence_id"]
            col_dt = ev["collection_datetime"]
            stored_on = col_dt + timedelta(hours=random.randint(1, 6))
            retrieved_on = None if random.random() > 0.3 else stored_on + timedelta(days=random.randint(5, 60))
            stored_by = random.choice(officer_ids)
            unit_id = random.choice(unit_ids)

            if retrieved_on is None:
                unit_counts[unit_id] = unit_counts.get(unit_id, 0) + 1

            log_rows.append((
                eid, unit_id, stored_on.strftime("%Y-%m-%d %H:%M:%S"),
                retrieved_on.strftime("%Y-%m-%d %H:%M:%S") if retrieved_on else None,
                stored_by
            ))

        max_l = self.query_one("SELECT MAX(log_id) AS mx FROM StorageLog")
        min_l_id = (max_l["mx"] or 0) + 1

        self.execute_many(
            "INSERT INTO StorageLog (evidence_id, unit_id, stored_on, retrieved_on, stored_by) VALUES (%s,%s,%s,%s,%s)",
            log_rows
        )

        # Update StorageUnit.current_count
        for uid, count in unit_counts.items():
            self.execute("UPDATE StorageUnit SET current_count = LEAST(capacity, %s) WHERE unit_id = %s", (count, uid))

        logs = self.query("SELECT log_id FROM StorageLog WHERE log_id >= %s ORDER BY log_id", (min_l_id,))
        self.disconnect()
        return [r["log_id"] for r in logs]
