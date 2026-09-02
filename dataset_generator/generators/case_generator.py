"""
dataset_generator/generators/case_generator.py
Generates: PoliceStation, CaseType (reuses existing), CaseStatus (reuses existing),
           Court (reuses existing), CriminalCase, CrimeScene
"""
import random
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.base_generator import BaseGenerator
from config import CASE_TYPE_WEIGHTS, CASE_STATUS_WEIGHTS


DISTRICTS = [
    ("Pune", "Pune City"), ("Mumbai", "Mumbai West"), ("Mumbai", "Mumbai Central"),
    ("Nagpur", "Nagpur Division"), ("Nashik", "Nashik Division"),
    ("Aurangabad", "Aurangabad Division"), ("Kolhapur", "Kolhapur Division"),
    ("Solapur", "Solapur Division"), ("Thane", "Mumbai North"),
    ("Navi Mumbai", "Konkan Division"), ("Pimpri", "Pune Rural"),
    ("Satara", "Pune Division"), ("Raigad", "Konkan Division"),
    ("Osmanabad", "Aurangabad Division"), ("Ahmednagar", "Nashik Division"),
    ("Dhule", "Nashik Division"), ("Jalgaon", "Nashik Division"),
    ("Latur", "Aurangabad Division"), ("Nanded", "Aurangabad Division"),
    ("Amravati", "Amravati Division"),
]

SCENE_TYPES = [
    "Indoor Residence", "Commercial Premises", "Warehouse", "Outdoor Public Area",
    "Vehicle", "Office Building", "Industrial Site", "Roadside",
    "Hotel Room", "Educational Institution", "Healthcare Facility", "Government Building",
]

CASE_DESCRIPTION_TEMPLATES = {
    1: [  # Murder
        "Body found at {loc}. Victim: {name}. Cause of death under investigation.",
        "Homicide case — victim {name} found deceased at {loc}.",
        "Murder reported at {loc}. Victim identified as {name}.",
    ],
    2: [  # Theft
        "Theft of property valued at {amount} lakhs from {loc}.",
        "Break-in and theft reported at {loc}. Items worth {amount} lakhs stolen.",
        "Jewellery/cash worth {amount} lakhs stolen from {loc}.",
    ],
    3: [  # Cybercrime
        "Large-scale {crime} fraud originating from {loc}.",
        "Cybercrime complaint — {crime} scheme targeting {amount} victims.",
        "Digital fraud case — {crime} reported by {amount} complainants.",
    ],
    4: [  # Narcotics
        "{weight}kg of {drug} seized from {loc}.",
        "Narcotics case — {weight}kg {drug} recovered from {loc}.",
        "Drug trafficking — {weight}kg of {drug} intercepted at {loc}.",
    ],
    5: [  # Kidnapping
        "Minor/adult abducted near {loc}. Victim: {name}.",
        "Kidnapping case — victim {name} reported missing from {loc}.",
        "Unlawful confinement — victim abducted from {loc}.",
    ],
    6: [  # Fraud
        "Financial fraud of {amount} lakhs by {crime} scheme.",
        "Cheating and fraud — {amount} lakhs misappropriated via {crime}.",
        "Investment fraud case — victims defrauded of {amount} lakhs.",
    ],
}

DRUGS    = ["heroin", "cocaine", "methamphetamine", "MDMA", "cannabis", "opium"]
FRAUDS   = ["Ponzi scheme", "SIM card cloning", "phishing", "identity theft", "loan fraud", "insurance fraud"]
CYBERCRIMES = ["banking fraud", "ransomware", "data breach", "online scam", "cryptocurrency fraud"]


class CaseGenerator(BaseGenerator):

    def generate_police_stations(self, count: int) -> list:
        """Generate synthetic police stations."""
        if self.dry_run:
            print("  [DRY RUN] Generated %d police stations." % count)
            return list(range(1, count + 1))
        self.connect()
        stations = []
        used_contacts = set()
        existing_contacts = self.query("SELECT contact_number FROM PoliceStation")
        for r in existing_contacts:
            used_contacts.add(r["contact_number"])

        # Keep existing seed stations intact (IDs 1–5 already in DB)
        existing = self.query("SELECT station_id FROM PoliceStation ORDER BY station_id DESC LIMIT 1")
        start_id = (existing[0]["station_id"] + 1) if existing else 1

        rows = []
        for i in range(count):
            district, zone = random.choice(DISTRICTS)
            contact = self._unique_contact(used_contacts)
            station_name = f"{self.fake.last_name()} Nagar Police Station"
            rows.append((station_name, district, zone, contact))
            self.print_progress("Police Stations", i + 1, count)

        self.execute_many(
            "INSERT INTO PoliceStation (name, district, zone, contact_number) VALUES (%s,%s,%s,%s)",
            rows
        )
        # Retrieve all station IDs
        all_stations = self.query("SELECT station_id FROM PoliceStation")
        self.disconnect()
        return [r["station_id"] for r in all_stations]

    def generate_cases(self, count: int, station_ids: list, officer_ids: list,
                       court_ids: list) -> list:
        """Generate synthetic criminal cases and crime scenes."""
        if self.dry_run:
            print("  [DRY RUN] Generated %d criminal cases." % count)
            return list(range(1, count + 1))
        self.connect()

        # Load existing type/status IDs
        types   = self.query("SELECT type_id FROM CaseType")
        statuses = self.query("SELECT status_id, label FROM CaseStatus")
        type_ids   = [r["type_id"]   for r in types]
        status_ids = [r["status_id"] for r in statuses]
        status_labels = {r["status_id"]: r["label"] for r in statuses}

        # Weighted sampling
        type_weights   = [CASE_TYPE_WEIGHTS.get(tid, 0.1)   for tid in type_ids]
        status_weights = [CASE_STATUS_WEIGHTS.get(sid, 0.25) for sid in status_ids]

        case_rows  = []
        scene_rows = []
        fir_used   = set()

        # Load existing FIR numbers to avoid collision
        existing_firs = self.query("SELECT fir_number FROM CriminalCase")
        for r in existing_firs:
            fir_used.add(r["fir_number"])

        # Load existing case IDs to compute start year
        existing_cases = self.query("SELECT MAX(case_id) AS mx FROM CriminalCase")
        case_seq = (existing_cases[0]["mx"] or 0) + 1

        for i in range(count):
            year     = random.choice([2022, 2023, 2024, 2025, 2026])
            month    = random.randint(1, 12)
            day      = random.randint(1, 28)
            date_str = f"{year}-{month:02d}-{day:02d}"

            type_id   = random.choices(type_ids,   weights=type_weights,   k=1)[0]
            status_id = random.choices(status_ids, weights=status_weights, k=1)[0]
            officer   = random.choice(officer_ids)
            station   = random.choice(station_ids)
            court_id  = random.choice(court_ids) if random.random() > 0.3 else None

            # Unique FIR
            fir = self._unique_fir(year, station, fir_used, case_seq)
            fir_used.add(fir)

            desc = self._case_description(type_id)
            case_rows.append((fir, station, type_id, officer, court_id, status_id, date_str, desc))
            case_seq += 1

            # Crime scene for this case
            district = random.choice(DISTRICTS)[0]
            address  = f"{self.fake.building_number()}, {self.fake.street_name()}, {district}"
            lat      = round(random.uniform(18.0, 21.0), 7)
            lon      = round(random.uniform(73.0, 80.0), 7)
            scene_type = random.choice(SCENE_TYPES)
            scene_rows.append(None)  # placeholder, filled after case insert

            self.print_progress("Criminal Cases", i + 1, count)

        # Bulk insert cases
        self.execute_many(
            """INSERT INTO CriminalCase (fir_number, police_station_id, case_type_id,
               investigating_officer_id, court_id, status_id, date_filed, description)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            case_rows
        )

        # Retrieve newly inserted case IDs
        new_cases = self.query(
            "SELECT case_id, date_filed FROM CriminalCase WHERE fir_number LIKE 'SYN/%' ORDER BY case_id"
        )

        # Insert crime scenes (one per case)
        scene_inserts = []
        for case in new_cases:
            district  = random.choice(DISTRICTS)[0]
            address   = f"{self.fake.building_number()}, {self.fake.street_name()}, {district}"
            lat       = round(random.uniform(18.0, 21.0), 7)
            lon       = round(random.uniform(73.0, 80.0), 7)
            stype     = random.choice(SCENE_TYPES)
            scene_inserts.append((case["case_id"], address, lat, lon, stype))

        self.execute_many(
            "INSERT IGNORE INTO CrimeScene (case_id, address, latitude, longitude, scene_type) VALUES (%s,%s,%s,%s,%s)",
            scene_inserts
        )

        self.disconnect()
        return [r["case_id"] for r in new_cases]

    # ── Private helpers ──────────────────────────────────────
    def _unique_contact(self, used: set) -> str:
        for _ in range(1000):
            n = f"0{random.randint(2000000000, 9999999999)}"[:11]
            if n not in used:
                used.add(n)
                return n
        raise RuntimeError("Could not generate unique contact number")

    def _unique_fir(self, year: int, station_id: int, used: set, seq: int) -> str:
        base = f"SYN/{year}/ST{station_id:03d}/{seq:04d}"
        if base not in used:
            return base
        return f"SYN/{year}/ST{station_id:03d}/{seq:04d}X"

    def _case_description(self, type_id: int) -> str:
        templates = CASE_DESCRIPTION_TEMPLATES.get(type_id, ["Case under investigation."])
        tmpl = random.choice(templates)
        return tmpl.format(
            loc    = self.fake.address().replace("\n", ", "),
            name   = self.fake.name(),
            amount = random.randint(1, 500),
            crime  = random.choice(CYBERCRIMES + FRAUDS),
            weight = round(random.uniform(0.1, 50.0), 2),
            drug   = random.choice(DRUGS),
        )
