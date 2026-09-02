"""
dataset_generator/generators/forensic_generator.py
Generates ForensicLab, Examiner, Examination, and ExaminationReport records.
"""
import random
from datetime import timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.base_generator import BaseGenerator
from generators.report_generator import ReportGenerator
from config import EXAM_SLA_DAYS


LAB_SPECIALIZATIONS = [
    "General Forensics", "Biology & Chemistry", "Digital Evidence",
    "Ballistics & Weapons", "Questioned Documents", "Toxicology & Narcotics"
]

EXAMINER_SPECIALIZATIONS = [
    "DNA Analysis", "Chemical Analysis", "Digital Forensics",
    "Fingerprint Analysis", "Ballistics", "Serology", "Cyber Forensics"
]

QUALIFICATIONS = [
    "PhD Forensic Biology", "PhD Chemistry", "MSc Cyber Security",
    "MSc Forensic Science", "BE Mechanical, FSL Certified", "MSc Biochemistry"
]


class ForensicGenerator(BaseGenerator):

    def generate_labs_and_examiners(self, lab_count: int, examiner_count: int) -> tuple:
        """Generate forensic labs and examiners."""
        if self.dry_run:
            print("  [DRY RUN] Generated %d labs and %d examiners." % (lab_count, examiner_count))
            return list(range(1, lab_count + 1)), [{"examiner_id": i, "full_name": f"Dr. Examiner {i}", "lab_id": 1} for i in range(1, examiner_count + 1)]
        self.connect()
        # Query existing accreditation numbers and contact numbers
        used_accs = set()
        used_phones = set()
        existing_labs = self.query("SELECT accreditation_number, contact_number FROM ForensicLab")
        for r in existing_labs:
            used_accs.add(r["accreditation_number"])
            used_phones.add(r["contact_number"])

        max_l = self.query_one("SELECT MAX(lab_id) AS mx FROM ForensicLab")
        min_l_id = (max_l["mx"] or 0) + 1

        # Generate ForensicLab
        lab_rows = []
        for i in range(lab_count):
            name = f"{self.fake.city()} Regional FSL"
            addr = f"{self.fake.street_address()}, {self.fake.city()}"
            
            seq = i + 1
            acc = f"NABL-FSL-{2024 + (seq // 10):04d}-{seq:03d}"
            while acc in used_accs:
                seq += 1
                acc = f"NABL-FSL-{2024 + (seq // 10):04d}-{seq:03d}"
            used_accs.add(acc)

            phone = f"0{random.randint(2000000000, 9999999999)}"[:11]
            while phone in used_phones:
                phone = f"0{random.randint(2000000000, 9999999999)}"[:11]
            used_phones.add(phone)

            spec = random.choice(LAB_SPECIALIZATIONS)
            lab_rows.append((name, addr, acc, spec, phone))

        self.execute_many(
            "INSERT INTO ForensicLab (lab_name, address, accreditation_number, specialization, contact_number) VALUES (%s,%s,%s,%s,%s)",
            lab_rows
        )
        labs = self.query("SELECT lab_id, lab_name FROM ForensicLab WHERE lab_id >= %s ORDER BY lab_id", (min_l_id,))
        lab_ids = [r["lab_id"] for r in labs]

        max_e = self.query_one("SELECT MAX(examiner_id) AS mx FROM Examiner")
        min_e_id = (max_e["mx"] or 0) + 1

        # Generate Examiner
        examiner_rows = []
        for i in range(examiner_count):
            name = f"Dr. {self.fake.name()}" if random.random() > 0.4 else f"Mr. {self.fake.name()}"
            lab_id = random.choice(lab_ids)
            spec = random.choice(EXAMINER_SPECIALIZATIONS)
            qual = random.choice(QUALIFICATIONS)
            examiner_rows.append((name, lab_id, spec, qual))

        self.execute_many(
            "INSERT INTO Examiner (full_name, lab_id, specialization, qualification) VALUES (%s,%s,%s,%s)",
            examiner_rows
        )
        examiners = self.query("SELECT examiner_id, full_name, lab_id FROM Examiner WHERE examiner_id >= %s ORDER BY examiner_id", (min_e_id,))

        self.disconnect()
        return lab_ids, examiners

    def generate_examinations(self, count: int, evidence_ids: list, examiners: list, officer_ids: list) -> list:
        """Generate examination records and natural-language examination reports."""
        if self.dry_run:
            print("  [DRY RUN] Generated %d examinations & reports." % count)
            return list(range(1, count + 1))
        self.connect()

        report_gen = ReportGenerator(seed=self.seed)

        # Load ExaminationType
        exam_types = self.query("SELECT type_id, type_name, typical_duration_days FROM ExaminationType")
        if not exam_types:
            raise RuntimeError("ExaminationType seed data missing")

        type_map = {r["type_id"]: r for r in exam_types}
        type_ids = list(type_map.keys())

        # Query evidence and associated cases
        evidence_list = self.query(
            """SELECT e.evidence_id, e.collection_datetime, cc.fir_number, e.type_id
               FROM Evidence e JOIN CriminalCase cc ON e.case_id=cc.case_id
               WHERE e.evidence_id IN (%s)""" % ",".join(map(str, evidence_ids))
        ) if evidence_ids else self.query(
            "SELECT e.evidence_id, e.collection_datetime, cc.fir_number, e.type_id FROM Evidence e JOIN CriminalCase cc ON e.case_id=cc.case_id"
        )

        examiner_ids = [r["examiner_id"] for r in examiners]
        examiner_info = {r["examiner_id"]: r for r in examiners}

        # Query lab names
        labs = self.query("SELECT lab_id, lab_name FROM ForensicLab")
        lab_names = {r["lab_id"]: r["lab_name"] for r in labs}

        exam_rows = []
        report_data = []

        for idx in range(count):
            ev = random.choice(evidence_list)
            eid = ev["evidence_id"]
            fir = ev["fir_number"]
            col_dt = ev["collection_datetime"]

            exam_type_id = random.choice(type_ids)
            examiner_id = random.choice(examiner_ids)

            # Start date is 1-15 days after collection
            start_date = (col_dt + timedelta(days=random.randint(1, 15))).date()

            sla_days = type_map[exam_type_id]["typical_duration_days"]

            # Status determination (70% Completed, 15% In Progress, 10% Pending, 5% Overdue)
            status_r = random.random()
            if status_r < 0.70:
                status = "Completed"
                end_date = start_date + timedelta(days=random.randint(1, sla_days))
                summary = "Examination completed successfully. Report filed."
            elif status_r < 0.85:
                status = "In Progress"
                end_date = None
                summary = "Analysis currently in progress."
            elif status_r < 0.95:
                status = "Pending"
                end_date = None
                summary = "Scheduled for analysis."
            else:
                status = "Overdue"
                end_date = None
                summary = "Overdue - examination pending beyond SLA."

            exam_rows.append((eid, examiner_id, exam_type_id, start_date.strftime("%Y-%m-%d"),
                              end_date.strftime("%Y-%m-%d") if end_date else None, status, summary))

            # Store info for report generation if completed
            if status == "Completed":
                ex_info = examiner_info.get(examiner_id, {})
                lab_name = lab_names.get(ex_info.get("lab_id"), "Regional Forensic Science Laboratory")
                filed_by = random.choice(officer_ids)

                report_text = report_gen.generate_report_text(
                    exam_type_id=exam_type_id,
                    fir=fir,
                    evidence_id=eid,
                    examiner_name=ex_info.get("full_name", "Dr. Forensic Examiner"),
                    lab_name=lab_name,
                    exam_date=end_date.strftime("%Y-%m-%d"),
                    report_id=f"RPT-{idx+101:05d}"
                )

                filed_on = f"{end_date.strftime('%Y-%m-%d')} {random.randint(9,17):02d}:{random.randint(0,59):02d}:00"
                is_admissible = 1 if random.random() > 0.05 else 0

                report_data.append((idx + 1, report_text, filed_on, filed_by, is_admissible))

            self.print_progress("Examinations", idx + 1, count)

        max_before = self.query_one("SELECT MAX(exam_id) AS mx FROM Examination")
        min_new_exam_id = (max_before["mx"] or 0) + 1

        # Insert Examination rows
        self.execute_many(
            """INSERT INTO Examination (evidence_id, examiner_id, exam_type_id, start_date, end_date, status, findings_summary)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            exam_rows
        )

        # Retrieve inserted exam IDs
        inserted_exams = self.query(
            "SELECT exam_id FROM Examination WHERE exam_id >= %s ORDER BY exam_id",
            (min_new_exam_id,)
        )
        exam_ids = [r["exam_id"] for r in inserted_exams]

        # Insert ExaminationReport rows matching inserted exam IDs
        report_inserts = []
        report_idx = 0
        for i, er in enumerate(exam_rows):
            # er status is at index 5
            if er[5] == "Completed" and report_idx < len(report_data):
                rd = report_data[report_idx]
                report_inserts.append((exam_ids[i], rd[1], rd[2], rd[3], rd[4]))
                report_idx += 1

        self.execute_many(
            """INSERT INTO ExaminationReport (exam_id, report_text, filed_on, filed_by, is_admissible)
               VALUES (%s,%s,%s,%s,%s)""",
            report_inserts
        )

        self.disconnect()
        return exam_ids
