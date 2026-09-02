# Synthetic Dataset Generator — Controlled Forensic Scenarios (A–J)

To systematically evaluate the Hybrid RAG Forensic Intelligence Platform under varied operational conditions, the generator embeds 10 controlled scenarios into the synthetic dataset.

---

## Scenario Definitions

### Scenario A — Normal Clean Evidence
- **Description**: Standard evidence lifecycle without any anomalies.
- **Workflow**: Collection → Storage → Lab Examination → Report Filed → Court Submission.
- **Status**: Intact, hash verified, admissible in court.

### Scenario B — Hash Mismatch (Tamper Detected)
- **Description**: Integrity violation where current SHA-256 hash does not match original stored hash.
- **Trigger**: System flags `HASH_MISMATCH_TAMPERED`, sets status to `Compromised`, files a `Critical` `TamperIncident`, and emits a `HashMismatch` `AlertLog`.

### Scenario C — Custody Delay (Temporal Anomaly)
- **Description**: Suspicious delay between physical transfer time and recorded system time ($> 4$ hours).
- **Flag**: Highlighted in `TemporalAnomalyView` with a `SUSPICIOUS GAP` status.

### Scenario D — Derived Evidence Cascade
- **Description**: Parent evidence (e.g., seized laptop) marked as `Compromised`.
- **Cascade**: Trigger `trg_tamper_cascade` automatically marks all child evidence (e.g., extracted hard disk, recovered files) as `Compromised` and logs an audit trail.

### Scenario E — Expiring Biological Evidence
- **Description**: Biological sample with degradation period approaching expiry ($ \le 7$ days remaining).
- **Trigger**: System generates an `Expiry` `AlertLog` via trigger `trg_expiry_alert` and displays in `ExpiringEvidenceView`.

### Scenario F — Overdue Examination
- **Description**: Laboratory examination active past its standard SLA duration without a submitted report.
- **Trigger**: Visible in `OverdueExaminationView` and triggers an `Overdue` `AlertLog`.

### Scenario G — Dead-Man Inactivity Switch
- **Description**: Evidence associated with an open case that has had zero custody transfers or lab activity for $> 30$ days.
- **Trigger**: Stored procedure `dead_man_switch()` flags the item and logs a `DeadManSwitch` `AlertLog`.

### Scenario H — Normal Clean Case
- **Description**: Case containing multiple evidence items with 100% clean chain of custody, no alerts, and admissible forensic reports.

### Scenario I — Multiple Anomalies Case
- **Description**: High-complexity case featuring a combination of Scenarios B, C, and F (hash mismatch, custody delay, and overdue exam).
- **Purpose**: Tests multi-table SQL joins and complex RAG query reasoning.

### Scenario J — Ambiguous / Insufficient Evidence
- **Description**: Case or evidence item with missing records, unfiled reports, or incomplete transfer logs.
- **Purpose**: Critical for testing **hallucination prevention** (system must explicitly declare insufficient information rather than inventing facts).
