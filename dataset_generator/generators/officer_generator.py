"""
dataset_generator/generators/officer_generator.py
Generates: Officer records (with password_hash), Posting records
Reuses existing Designation and Department seed data.
"""
import random
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.base_generator import BaseGenerator
from werkzeug.security import generate_password_hash


# Standard password for all synthetic officers — clearly documented
SYNTHETIC_OFFICER_PASSWORD = "SyntheticPass#2024"


class OfficerGenerator(BaseGenerator):

    def generate_officers(self, count: int, station_ids: list) -> list:
        """Generate synthetic officers using existing designation/department seed data."""
        self.connect()

        # Load existing designations and departments (seed data)
        designations = self.query("SELECT designation_id, rank_level, permissions_level FROM Designation")
        departments  = self.query("SELECT dept_id FROM Department")

        if self.dry_run:
            print("  [DRY RUN] Generated %d synthetic officers." % count)
            return list(range(1, count + 1))

        if not designations or not departments:
            raise RuntimeError("Seed Designation and Department data missing. Run complete_database.sql first.")

        dept_ids = [r["dept_id"] for r in departments]

        # Password hash — same for all synthetic officers (clearly documented)
        pwd_hash = generate_password_hash(SYNTHETIC_OFFICER_PASSWORD)

        # Check if password_hash column exists (added by set_passwords.py migration)
        try:
            self.query("SELECT password_hash FROM Officer LIMIT 1")
            has_pwd_col = True
        except Exception:
            has_pwd_col = False

        used_badges = set()
        # Load existing badge numbers
        existing = self.query("SELECT badge_number FROM Officer")
        for r in existing:
            used_badges.add(r["badge_number"])

        rows = []
        for i in range(count):
            designation = random.choice(designations)
            dept_id     = random.choice(dept_ids)
            badge       = self._unique_badge(used_badges)
            name        = self.fake.name()
            join_year   = random.randint(2005, 2023)
            join_month  = random.randint(1, 12)
            join_day    = random.randint(1, 28)
            date_joined = f"{join_year}-{join_month:02d}-{join_day:02d}"
            is_active   = 1 if random.random() > 0.05 else 0   # 95% active

            if has_pwd_col:
                rows.append((badge, name, designation["designation_id"], dept_id, date_joined, is_active, pwd_hash))
            else:
                rows.append((badge, name, designation["designation_id"], dept_id, date_joined, is_active))

            self.print_progress("Officers", i + 1, count)

        if has_pwd_col:
            self.execute_many(
                """INSERT INTO Officer (badge_number, full_name, designation_id, department_id, date_joined, is_active, password_hash)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                rows
            )
        else:
            self.execute_many(
                """INSERT INTO Officer (badge_number, full_name, designation_id, department_id, date_joined, is_active)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                rows
            )

        # Generate posting records (officer ↔ station history)
        all_officers = self.query("SELECT officer_id FROM Officer ORDER BY officer_id")
        officer_ids  = [r["officer_id"] for r in all_officers]

        posting_rows = []
        for oid in officer_ids[-count:]:  # Only newly created officers
            station    = random.choice(station_ids)
            from_year  = random.randint(2015, 2023)
            from_date  = f"{from_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
            to_date    = None if random.random() > 0.4 else f"{from_year + random.randint(1,3)}-{random.randint(1,12):02d}-01"
            posting_rows.append((oid, station, from_date, to_date))

        self.execute_many(
            "INSERT INTO Posting (officer_id, station_id, from_date, to_date) VALUES (%s,%s,%s,%s)",
            posting_rows
        )

        self.disconnect()
        return officer_ids

    def _unique_badge(self, used: set) -> str:
        prefixes = ["MH", "DL", "UP", "GJ", "KA", "TN", "RJ", "MP"]
        for _ in range(1000):
            prefix = random.choice(prefixes)
            num    = random.randint(1000, 9999)
            badge  = f"{prefix}-{num}"
            if badge not in used:
                used.add(badge)
                return badge
        raise RuntimeError("Badge number space exhausted")
