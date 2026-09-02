"""
dataset_generator/generators/evidence_generator.py
Generates Evidence, EvidenceType (reuses seed), EvidenceMedia records.
Computes real SHA-256 hashes on synthetic content.
"""
import random
import hashlib
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.base_generator import BaseGenerator
from config import EVIDENCE_TYPE_WEIGHTS, EVIDENCE_STATUS_WEIGHTS, BIO_EXPIRY_DAYS_RANGE


EVIDENCE_DESCRIPTIONS = {
    1: [  # Biological
        "Blood sample collected from {loc}",
        "DNA swab taken from {item}",
        "Tissue specimen from crime scene",
        "Saliva sample collected from {item}",
        "Hair strands recovered from {loc}",
    ],
    2: [  # Digital
        "Laptop computer seized from {loc}",
        "Mobile phone recovered from {item}",
        "USB drive found at {loc}",
        "Hard disk drive extracted from suspect device",
        "SIM card retrieved from {item}",
        "CCTV footage recovered from {loc}",
        "Memory card seized from {item}",
    ],
    3: [  # Physical
        "Knife with suspected bloodstains recovered from {loc}",
        "Fingerprint lifted from {item}",
        "Shoe impression cast from {loc}",
        "Clothing item with suspect stains from {item}",
        "Jewellery recovered from {loc}",
        "Tool marks lifted from {item}",
        "Fired cartridge case collected from {loc}",
    ],
    4: [  # Documentary
        "Financial documents seized from {loc}",
        "Forged identity documents recovered from {item}",
        "Transaction records extracted from {loc}",
        "Contract documents with forged signatures from {item}",
    ],
    5: [  # Chemical
        "Suspected narcotic substance {weight}g sealed in evidence bag from {loc}",
        "Chemical compound seized from {item} — {weight}g",
        "Powder substance recovered from {loc} — {weight}g",
        "Liquid substance in sealed vial from {item}",
    ],
    6: [  # Ballistic
        "Firearm recovered from {loc}",
        "Bullet fragments collected from {loc}",
        "Spent cartridge cases from {item}",
        "Projectile extracted during autopsy from {loc}",
    ],
}

LOCATIONS = [
    "crime scene", "suspect vehicle", "suspect residence", "storage locker",
    "abandoned building", "public road", "victim's body", "warehouse",
    "hotel room", "office premises", "shop floor", "river bank",
]

ITEMS = [
    "door handle", "window sill", "victim's clothing", "suspect's jacket",
    "kitchen knife", "suspect's mobile", "glass surface", "steering wheel",
    "laptop keyboard", "evidence bag seal", "safe lock",
]


class EvidenceGenerator(BaseGenerator):

    def generate_evidence(self, count: int, case_ids: list, officer_ids: list,
                          scene_ids: list = None) -> list:
        """Generate synthetic evidence items with SHA-256 hashes."""
        if self.dry_run:
            print("  [DRY RUN] Generated %d evidence items." % count)
            return list(range(1, count + 1))
        self.connect()

        # Load existing type IDs
        types = self.query("SELECT type_id FROM EvidenceType")
        type_ids = [r["type_id"] for r in types]
        type_weights = [EVIDENCE_TYPE_WEIGHTS.get(tid, 0.1) for tid in type_ids]

        # Load scene-to-case mapping
        scenes = self.query("SELECT scene_id, case_id FROM CrimeScene")
        case_to_scenes = {}
        for s in scenes:
            case_to_scenes.setdefault(s["case_id"], []).append(s["scene_id"])

        rows = []
        evidence_meta = []   # for custody/storage generators

        from datetime import date, timedelta, datetime

        for i in range(count):
            case_id   = random.choice(case_ids)
            type_id   = random.choices(type_ids, weights=type_weights, k=1)[0]
            officer   = random.choice(officer_ids)
            collected_by = officer

            # Crime scene for this case
            scene_list = case_to_scenes.get(case_id, [])
            if scene_list:
                scene_id = random.choice(scene_list)
            else:
                # Use any scene as fallback
                all_scenes = self.query("SELECT scene_id FROM CrimeScene LIMIT 1")
                scene_id = all_scenes[0]["scene_id"] if all_scenes else 1

            # Collection datetime: random date in 2022–2026
            col_year  = random.randint(2022, 2026)
            col_month = random.randint(1, 12)
            col_day   = random.randint(1, 28)
            col_hour  = random.randint(6, 22)
            col_min   = random.randint(0, 59)
            collection_dt = datetime(col_year, col_month, col_day, col_hour, col_min)
            collection_str = collection_dt.strftime("%Y-%m-%d %H:%M:%S")

            # Description
            desc = self._description(type_id)

            # SHA-256 hash (computed on synthetic content string)
            hash_content = f"E_{case_id}_{type_id}_{collection_str}_{desc}"
            hash_value   = hashlib.sha256(hash_content.encode()).hexdigest()

            # Expiry for biological/chemical
            expiry_date = None
            if type_id in (1, 5):
                days = random.randint(*BIO_EXPIRY_DAYS_RANGE)
                expiry_date = (date(col_year, col_month, col_day) + timedelta(days=days)).strftime("%Y-%m-%d")

            # Status (will be overridden by scenario generator for scenario cases)
            status = "Collected"

            rows.append((
                case_id, desc, type_id, collection_str, scene_id, collected_by,
                hash_value, "SHA-256", status, expiry_date, None, 1
            ))
            evidence_meta.append({
                "case_id":        case_id,
                "type_id":        type_id,
                "officer":        collected_by,
                "collection_dt":  collection_dt,
                "hash_value":     hash_value,
            })
            self.print_progress("Evidence", i + 1, count)

        max_before = self.query_one("SELECT MAX(evidence_id) AS mx FROM Evidence")
        min_new_id = (max_before["mx"] or 0) + 1

        self.execute_many(
            """INSERT INTO Evidence (case_id, description, type_id, collection_datetime,
               scene_id, collected_by, hash_value, hash_algorithm, current_status,
               expiry_date, parent_evidence_id, version_number)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            rows
        )

        new_evidence = self.query(
            "SELECT evidence_id FROM Evidence WHERE evidence_id >= %s ORDER BY evidence_id",
            (min_new_id,)
        )
        self.disconnect()
        return [r["evidence_id"] for r in new_evidence]

    def _description(self, type_id: int) -> str:
        templates = EVIDENCE_DESCRIPTIONS.get(type_id, ["Unspecified evidence item"])
        tmpl = random.choice(templates)
        return tmpl.format(
            loc    = random.choice(LOCATIONS),
            item   = random.choice(ITEMS),
            weight = round(random.uniform(0.5, 1000.0), 1),
        )
