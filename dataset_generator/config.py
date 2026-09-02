"""
dataset_generator/config.py
Centralized configuration for the synthetic forensic dataset generator.
All size presets, constants, and distribution parameters are defined here.
"""

# ── SIZE PRESETS ─────────────────────────────────────────────
SIZES = {
    "small": {
        "police_stations":      5,
        "departments":          8,
        "designations":        10,
        "officers":            30,
        "cases":               50,
        "crime_scenes_per_case": 1,
        "evidence_per_case":    4,       # avg; actual is poisson(4)
        "total_evidence":     200,
        "custody_transfers":  800,
        "forensic_labs":        4,
        "examiners":           15,
        "examinations":       150,
        "examination_reports": 150,
        "storage_facilities":   5,
        "storage_units":       10,
        "courts":               5,
        "judges":              10,
        "hearings":            60,
        "court_submissions":   40,
        "tamper_incidents":    20,
        "alerts":             100,
        # Scenario instance counts
        "scenario_instances":  {
            "A": 10, "B": 5, "C": 5, "D": 3, "E": 5,
            "F": 5,  "G": 3, "H": 5, "I": 3, "J": 5,
        },
    },
    "medium": {
        "police_stations":     10,
        "departments":         10,
        "designations":        10,
        "officers":           100,
        "cases":              500,
        "crime_scenes_per_case": 1,
        "evidence_per_case":    4,
        "total_evidence":    2000,
        "custody_transfers": 8000,
        "forensic_labs":        8,
        "examiners":           40,
        "examinations":      1500,
        "examination_reports":1500,
        "storage_facilities":  10,
        "storage_units":       30,
        "courts":              10,
        "judges":              25,
        "hearings":           600,
        "court_submissions":  400,
        "tamper_incidents":   200,
        "alerts":            1000,
        "scenario_instances": {
            "A": 60, "B": 30, "C": 30, "D": 20, "E": 30,
            "F": 30, "G": 20, "H": 50, "I": 20, "J": 30,
        },
    },
    "large": {
        "police_stations":     20,
        "departments":         15,
        "designations":        10,
        "officers":           300,
        "cases":             2000,
        "crime_scenes_per_case": 1,
        "evidence_per_case":    5,
        "total_evidence":   10000,
        "custody_transfers":40000,
        "forensic_labs":       15,
        "examiners":          100,
        "examinations":      7500,
        "examination_reports":7500,
        "storage_facilities":  20,
        "storage_units":       80,
        "courts":              15,
        "judges":              50,
        "hearings":          2500,
        "court_submissions": 1500,
        "tamper_incidents":   800,
        "alerts":            4000,
        "scenario_instances": {
            "A": 250, "B": 120, "C": 120, "D": 80, "E": 120,
            "F": 120, "G": 80,  "H": 200, "I": 80, "J": 120,
        },
    },
}

# ── EVIDENCE STATUS DISTRIBUTION ────────────────────────────
# Weights for random evidence status assignment (non-scenario evidence)
EVIDENCE_STATUS_WEIGHTS = {
    "Collected":    0.05,
    "In Storage":   0.30,
    "In Lab":       0.25,
    "In Court":     0.10,
    "Returned":     0.10,
    "Archived":     0.10,
    "Compromised":  0.05,
    "Expired":      0.05,
}

# ── EVIDENCE TYPE DISTRIBUTION ───────────────────────────────
EVIDENCE_TYPE_WEIGHTS = {
    1: 0.15,   # Biological
    2: 0.25,   # Digital
    3: 0.30,   # Physical
    4: 0.15,   # Documentary
    5: 0.10,   # Chemical
    6: 0.05,   # Ballistic
}

# ── CASE TYPE DISTRIBUTION ───────────────────────────────────
CASE_TYPE_WEIGHTS = {
    1: 0.20,   # Murder
    2: 0.20,   # Theft
    3: 0.20,   # Cybercrime
    4: 0.15,   # Narcotics
    5: 0.10,   # Kidnapping
    6: 0.15,   # Fraud
}

# ── CASE STATUS DISTRIBUTION ─────────────────────────────────
CASE_STATUS_WEIGHTS = {
    1: 0.40,   # Investigation
    2: 0.30,   # Trial
    3: 0.20,   # Closed
    4: 0.10,   # Acquitted
}

# ── TAMPER SEVERITY DISTRIBUTION ────────────────────────────
TAMPER_SEVERITY_WEIGHTS = {
    "Low":      0.20,
    "Medium":   0.35,
    "High":     0.30,
    "Critical": 0.15,
}

# ── BIOLOGICAL EVIDENCE EXPIRY DAYS ─────────────────────────
# Days from collection_datetime to expiry_date
BIO_EXPIRY_DAYS_RANGE = (30, 180)   # uniform range
BIO_EXPIRY_NEAR_DAYS  = 3           # Scenario E: expiry within N days

# ── CUSTODY DELAY THRESHOLDS ─────────────────────────────────
NORMAL_RECORDING_DELAY_HOURS   = (0, 2)    # Normal: 0–2h delay
ANOMALY_RECORDING_DELAY_HOURS  = (5, 48)   # Scenario C: 5–48h delay

# ── EXAMINATION SLA ──────────────────────────────────────────
# Days per examination type (must match ExaminationType seed data)
EXAM_SLA_DAYS = {
    1: 21,   # DNA Analysis
    2: 14,   # Chemical Composition
    3: 10,   # Digital Forensics
    4:  7,   # Fingerprint Analysis
    5: 14,   # Ballistics Analysis
    6: 10,   # Serology
}

# ── OVERDUE THRESHOLD MULTIPLIER ────────────────────────────
# Scenario F: exam started this many × SLA days ago with no report
OVERDUE_MULTIPLIER = 1.5

# ── DEAD MAN SWITCH THRESHOLD ───────────────────────────────
DEAD_MAN_DAYS = 30    # No activity for this many days → alert

# ── REPORT TEXT VARIANTS PER EXAM TYPE ──────────────────────
# How many natural-language variants exist per examination type
REPORT_VARIANTS_PER_TYPE = 5

# ── CHROMA DB CONFIG ────────────────────────────────────────
CHROMA_PERSIST_DIR  = "ai/chroma_data"
CHROMA_COLLECTION   = "forensic_reports"

# ── FULLTEXT SEARCH CONFIG ───────────────────────────────────
FULLTEXT_MIN_RELEVANCE = 0.0001   # MySQL FULLTEXT minimum relevance score

# ── DATABASE CONFIG (matches existing app.py) ───────────────
DB_CONFIG = dict(
    host     = "localhost",
    user     = "root",
    password = "",           # Override via .env: DB_PASSWORD
    database = "forensic_coc",
    charset  = "utf8mb4",
)

# ── SYNTHETIC DATA DISCLAIMER ────────────────────────────────
SYNTHETIC_HEADER = "[SYNTHETIC DATA — NOT REAL — FOR ACADEMIC USE ONLY]"
