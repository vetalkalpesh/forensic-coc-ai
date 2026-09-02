"""
dataset_generator/generate_dataset.py
Main CLI entry point for the reproducible synthetic forensic dataset generator.

Usage:
    python generate_dataset.py --size small --seed 42
    python generate_dataset.py --size medium --seed 42
    python generate_dataset.py --size large --seed 42
    python generate_dataset.py --size small --dry-run
    python generate_dataset.py --validate
"""
import argparse
import sys, os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SIZES, SYNTHETIC_HEADER
from generators.base_generator import BaseGenerator
from generators.case_generator import CaseGenerator
from generators.officer_generator import OfficerGenerator
from generators.evidence_generator import EvidenceGenerator
from generators.custody_generator import CustodyGenerator
from generators.forensic_generator import ForensicGenerator
from generators.storage_generator import StorageGenerator
from generators.court_generator import CourtGenerator
from generators.integrity_generator import IntegrityGenerator
from generators.scenario_generator import ScenarioGenerator
from validators.fk_validator import FKValidator
from validators.scenario_validator import ScenarioValidator


def main():
    parser = argparse.ArgumentParser(description="Synthetic Forensic Dataset Generator")
    parser.add_argument("--size", choices=["small", "medium", "large"], default="small",
                        help="Dataset size preset (default: small)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for deterministic generation (default: 42)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate generation without writing to database")
    parser.add_argument("--validate", action="store_true",
                        help="Run foreign key and scenario validation checks on existing DB")
    args = parser.parse_args()

    print("=" * 65)
    print("  FORENSIC EVIDENCE CHAIN OF CUSTODY SYSTEM")
    print("  Synthetic Dataset Generator — Reproducible & Deterministic")
    print("=" * 65)
    print(f"  {SYNTHETIC_HEADER}")
    print(f"  Size Preset: {args.size.upper()}")
    print(f"  Random Seed: {args.seed}")
    print(f"  Dry Run Mode: {args.dry_run}")
    print("=" * 65)

    if args.validate:
        FKValidator.validate_all_foreign_keys()
        val = ScenarioValidator(seed=args.seed)
        val.validate_scenarios()
        return

    cfg = SIZES[args.size]
    start_time = time.time()

    # 1. Police Stations & Cases
    print("\n[Phase 1/7] Generating Police Stations, Cases & Crime Scenes...")
    cg = CaseGenerator(seed=args.seed, dry_run=args.dry_run)
    station_ids = cg.generate_police_stations(cfg["police_stations"])

    # 2. Officers & Postings
    print("\n[Phase 2/7] Generating Officers & Department Postings...")
    og = OfficerGenerator(seed=args.seed, dry_run=args.dry_run)
    officer_ids = og.generate_officers(cfg["officers"], station_ids)

    # Re-connect to get seed court IDs
    bg = BaseGenerator(seed=args.seed, dry_run=args.dry_run)
    bg.connect()
    courts = bg.query("SELECT court_id FROM Court")
    court_ids = [r["court_id"] for r in courts] if courts else [1]
    depts = bg.query("SELECT dept_id FROM Department")
    dept_ids = [r["dept_id"] for r in depts] if depts else [1]
    bg.disconnect()

    # Finish Cases
    case_ids = cg.generate_cases(cfg["cases"], station_ids, officer_ids, court_ids)

    # 3. Evidence
    print("\n[Phase 3/7] Generating Evidence Items & SHA-256 Hashes...")
    eg = EvidenceGenerator(seed=args.seed, dry_run=args.dry_run)
    evidence_ids = eg.generate_evidence(cfg["total_evidence"], case_ids, officer_ids)

    # 4. Custody Logs
    print("\n[Phase 4/7] Generating Custody Chain Logs & Transfers...")
    cust_g = CustodyGenerator(seed=args.seed, dry_run=args.dry_run)
    log_ids = cust_g.generate_custody_chains(cfg["custody_transfers"], evidence_ids, officer_ids, dept_ids)

    # 5. Forensic Labs & Examinations
    print("\n[Phase 5/7] Generating Forensic Labs, Examiners, Exams & Reports...")
    fg = ForensicGenerator(seed=args.seed, dry_run=args.dry_run)
    lab_ids, examiners = fg.generate_labs_and_examiners(cfg["forensic_labs"], cfg["examiners"])
    exam_ids = fg.generate_examinations(cfg["examinations"], evidence_ids, examiners, officer_ids)

    # 6. Storage & Court Workflows
    print("\n[Phase 6/7] Generating Storage Facilities & Court Workflows...")
    sg = StorageGenerator(seed=args.seed, dry_run=args.dry_run)
    fac_ids, unit_ids = sg.generate_facilities_and_units(cfg["storage_facilities"], cfg["storage_units"], dept_ids)
    sg.generate_storage_logs(evidence_ids, unit_ids, officer_ids)

    court_g = CourtGenerator(seed=args.seed, dry_run=args.dry_run)
    judge_ids = court_g.generate_judges(cfg["judges"], court_ids)
    court_g.generate_court_workflows(cfg["hearings"], cfg["court_submissions"], case_ids, court_ids, judge_ids, evidence_ids, officer_ids)

    # Integrity & Alerts
    ig = IntegrityGenerator(seed=args.seed, dry_run=args.dry_run)
    ig.generate_integrity_records(cfg["tamper_incidents"], cfg["alerts"], evidence_ids, officer_ids)

    # 7. Controlled Scenarios A-J
    print("\n[Phase 7/7] Injecting Controlled Forensic Scenarios (A–J)...")
    scen_g = ScenarioGenerator(seed=args.seed, dry_run=args.dry_run)
    examiner_ids = [e["examiner_id"] for e in examiners]
    scen_summary = scen_g.inject_scenarios(cfg["scenario_instances"], case_ids, officer_ids, examiner_ids, lab_ids)

    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 65)
    print(f"  DATASET GENERATION COMPLETE in {elapsed} seconds")
    print("=" * 65)
    print("  Scenario Injection Summary:")
    for scen, cnt in scen_summary.items():
        print(f"    Scenario {scen}: {cnt} instances injected")
    print("=" * 65)

    if not args.dry_run:
        FKValidator.validate_all_foreign_keys()
        val = ScenarioValidator(seed=args.seed)
        val.validate_scenarios()


if __name__ == "__main__":
    main()
