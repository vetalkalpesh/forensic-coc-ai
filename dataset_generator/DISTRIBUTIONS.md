# Synthetic Dataset Generator — Statistical Distributions & Parameters

This document formalizes the statistical distributions, probabilities, and parameter spaces used by the synthetic forensic dataset generator.

---

## 1. Case & Location Distributions

### Case Types (`CaseType`)
- Murder (20%)
- Theft (20%)
- Cybercrime (20%)
- Narcotics (15%)
- Kidnapping (10%)
- Fraud (15%)

### Case Statuses (`CaseStatus`)
- Investigation (40%)
- Trial (30%)
- Closed (20%)
- Acquitted (10%)

### Regional Distribution (`PoliceStation` & `Court`)
- Cities: Pune, Mumbai, Nagpur, Nashik, Aurangabad, Kolhapur, Solapur, Thane, Navi Mumbai, Pimpri
- Crime Scene coordinates: Latitude 18.0 to 21.0 N, Longitude 73.0 to 80.0 E (Maharashtra region)

---

## 2. Evidence Distributions

### Evidence Types (`EvidenceType`)
- Physical (30%)
- Digital (25%)
- Biological (15%) - Storage: Refrigerated -4°C to 4°C, Degradation SLA: 90 days
- Documentary (15%)
- Chemical (10%) - Storage: Hazmat sealed, Degradation SLA: 180 days
- Ballistic (5%)

### Evidence Status (`Evidence`)
- In Storage (30%)
- In Lab (25%)
- In Court (10%)
- Returned (10%)
- Archived (10%)
- Collected (5%)
- Compromised (5%)
- Expired (5%)

### Evidence Quantity per Case
- Poisson distribution with mean $\lambda = 4.0$, clamped to $[1, 10]$.

---

## 3. Custody & Transfer Chronology

### Transfer Modes (`CustodyTransfer`)
- Hand Delivery with Receipt (60%)
- Sealed Courier (25%)
- Court Order Transfer (15%)

### Temporal Gaps (`CustodyLog`)
- Normal Transfer Delay: Uniform $U(0, 2)$ hours between physical transfer and digital recording.
- Anomalous Delay (Scenario C): Uniform $U(5, 48)$ hours gap creating a suspicious recording anomaly.

---

## 4. Forensic Examinations & Reports

### Examination Types & SLAs (`ExaminationType`)
1. Fingerprint Analysis: 7 days
2. Digital Forensics: 10 days
3. Serology: 10 days
4. Chemical Composition: 14 days
5. Ballistics Analysis: 14 days
6. DNA Analysis: 21 days

### Examination Statuses
- Completed (70%)
- In Progress (15%)
- Pending (10%)
- Overdue (5%) - Examination start date exceeds SLA with no filed report.

### Report Corpus Variation
- Each examination type has 5 distinct natural-language template structures.
- Findings, observations, and conclusions draw from varied terminology to simulate real examiner style differences for semantic vector evaluation.

---

## 5. Tamper & Alert Distributions

### Tamper Severity (`TamperIncident`)
- Medium (35%)
- High (30%)
- Low (20%)
- Critical (15%)

### Alert Types (`AlertLog`)
- Tamper Alert
- HashMismatch Alert
- Expiry Alert (within 7 days)
- Overdue Examination Alert
- DeadManSwitch Alert (30+ days inactive custody on active case)
- Escalation Alert
