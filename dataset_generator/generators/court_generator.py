"""
dataset_generator/generators/court_generator.py
Generates Judge, Hearing, CourtSubmission, and SubmissionReturn records.
"""
import random
from datetime import timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.base_generator import BaseGenerator


JUDGE_DESIGNATIONS = [
    "Additional Sessions Judge", "Metropolitan Magistrate",
    "Sessions Judge", "High Court Judge", "Chief Judicial Magistrate"
]

HEARING_PURPOSES = [
    "Charge framing", "Evidence presentation", "Bail hearing",
    "Witness examination", "Final arguments", "Pre-trial conference"
]

HEARING_OUTCOMES = [
    "Charges framed against accused", "Evidence E002 and E010 presented",
    "Bail rejected", "Case adjourned for witness testimony",
    "Evidence marked as Exhibit A", "Case closed — accused acquitted",
    "Case closed — accused convicted"
]


class CourtGenerator(BaseGenerator):

    def generate_judges(self, count: int, court_ids: list) -> list:
        """Generate synthetic judges."""
        self.connect()

        judge_rows = []
        for i in range(count):
            name = f"Hon. Justice {self.fake.name()}"
            court = random.choice(court_ids)
            desig = random.choice(JUDGE_DESIGNATIONS)
            judge_rows.append((name, court, desig))

        max_j = self.query_one("SELECT MAX(judge_id) AS mx FROM Judge")
        min_j_id = (max_j["mx"] or 0) + 1

        self.execute_many(
            "INSERT INTO Judge (full_name, court_id, designation) VALUES (%s,%s,%s)",
            judge_rows
        )
        judges = self.query("SELECT judge_id FROM Judge WHERE judge_id >= %s ORDER BY judge_id", (min_j_id,))
        self.disconnect()
        return [r["judge_id"] for r in judges]

    def generate_court_workflows(self, hearing_count: int, sub_count: int,
                                 case_ids: list, court_ids: list, judge_ids: list,
                                 evidence_ids: list, officer_ids: list) -> tuple:
        """Generate Hearing, CourtSubmission, and SubmissionReturn workflow records."""
        if self.dry_run:
            print("  [DRY RUN] Generated %d hearings & court submissions." % hearing_count)
            return list(range(1, hearing_count + 1)), list(range(1, sub_count + 1))
        self.connect()

        cases = self.query("SELECT case_id, date_filed FROM CriminalCase")
        case_dates = {r["case_id"]: r["date_filed"] for r in cases}

        max_h = self.query_one("SELECT MAX(hearing_id) AS mx FROM Hearing")
        min_h_id = (max_h["mx"] or 0) + 1

        # Generate Hearing
        hearing_rows = []
        for i in range(hearing_count):
            cid = random.choice(case_ids)
            court = random.choice(court_ids)
            judge = random.choice(judge_ids)
            file_date = case_dates.get(cid)
            if not file_date:
                file_date = self.fake.date_between(start_date="-2y", end_date="today")

            h_date = file_date + timedelta(days=random.randint(15, 120))
            purpose = random.choice(HEARING_PURPOSES)
            outcome = random.choice(HEARING_OUTCOMES) if random.random() > 0.3 else None
            next_date = (h_date + timedelta(days=random.randint(14, 60))).strftime("%Y-%m-%d") if outcome and "adjourned" in outcome else None

            hearing_rows.append((
                cid, court, judge, h_date.strftime("%Y-%m-%d"),
                purpose, outcome, next_date
            ))

        self.execute_many(
            """INSERT INTO Hearing (case_id, court_id, judge_id, hearing_date, hearing_purpose, outcome, next_date)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            hearing_rows
        )
        hearings = self.query("SELECT hearing_id, case_id FROM Hearing WHERE hearing_id >= %s ORDER BY hearing_id", (min_h_id,))
        hearing_ids = [r["hearing_id"] for r in hearings]

        # Generate CourtSubmission
        sub_rows = []
        ret_candidates = []

        max_s = self.query_one("SELECT MAX(submission_id) AS mx FROM CourtSubmission")
        min_s_id = (max_s["mx"] or 0) + 1

        for i in range(sub_count):
            eid = random.choice(evidence_ids)
            hearing = random.choice(hearings)
            hid = hearing["hearing_id"]
            cid = hearing["case_id"]
            sub_by = random.choice(officer_ids)
            sub_date = self.fake.date_time_between(start_date="-1y", end_date="now")
            status = random.choice(["Submitted", "Returned", "Retained by Court"])

            sub_rows.append((eid, cid, hid, sub_by, sub_date.strftime("%Y-%m-%d %H:%M:%S"), status))
            if status == "Returned":
                ret_candidates.append(i + 1)  # temp index

        self.execute_many(
            """INSERT INTO CourtSubmission (evidence_id, case_id, hearing_id, submitted_by, submission_date, status)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            sub_rows
        )

        inserted_subs = self.query("SELECT submission_id, status FROM CourtSubmission WHERE submission_id >= %s ORDER BY submission_id", (min_s_id,))

        # Generate SubmissionReturn for Returned submissions
        ret_rows = []
        for sub in inserted_subs:
            if sub["status"] == "Returned":
                sub_id = sub["submission_id"]
                ret_to = random.choice(officer_ids)
                auth_by = random.choice(officer_ids)
                notes = "Returned after hearing. Returned to storage vault."
                ret_rows.append((sub_id, ret_to, auth_by, notes))

        self.execute_many(
            """INSERT INTO SubmissionReturn (submission_id, returned_to, authorized_by, notes)
               VALUES (%s,%s,%s,%s)""",
            ret_rows
        )

        self.disconnect()
        return hearing_ids, [r["submission_id"] for r in inserted_subs]
