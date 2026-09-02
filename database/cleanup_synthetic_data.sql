-- ============================================================
--  SYNTHETIC DATA CLEANUP SCRIPT v3 — Correct Schema
--  Removes ONLY rows inserted by the synthetic dataset generator
--  Original project: officer_id 1-11, station_id 1-5, case_id 1-6, evidence by original cases
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;

-- ─── Custody ────────────────────────────────────────────────

-- Remove CustodyTransfer for synthetic custody logs
DELETE ct FROM CustodyTransfer ct
  JOIN CustodyLog cl ON ct.log_id = cl.log_id
  JOIN Evidence e ON cl.evidence_id = e.evidence_id
  JOIN CriminalCase cc ON e.case_id = cc.case_id
  WHERE cc.fir_number LIKE 'SYN/%';

-- Remove partial custody logs (the 9 that got through from synthetic evidence 
-- linked to original cases via the partial run before trigger fired)
-- These partial logs have transferred_by OR received_by pointing to synthetic officers (id > 11)
DELETE FROM CustodyLog
  WHERE transferred_by > 11 OR received_by > 11;

-- Remove remaining custody logs for synthetic evidence
DELETE cl FROM CustodyLog cl
  JOIN Evidence e ON cl.evidence_id = e.evidence_id
  JOIN CriminalCase cc ON e.case_id = cc.case_id
  WHERE cc.fir_number LIKE 'SYN/%';

-- ─── Alert / Tamper ─────────────────────────────────────────

DELETE ti FROM TamperIncident ti
  JOIN Evidence e ON ti.evidence_id = e.evidence_id
  JOIN CriminalCase cc ON e.case_id = cc.case_id
  WHERE cc.fir_number LIKE 'SYN/%';

DELETE al FROM AlertLog al
  JOIN Evidence e ON al.evidence_id = e.evidence_id
  JOIN CriminalCase cc ON e.case_id = cc.case_id
  WHERE cc.fir_number LIKE 'SYN/%';

-- ─── Forensic Examination ───────────────────────────────────

-- ExaminationReport.exam_id FK -> Examination.exam_id
DELETE er FROM ExaminationReport er
  JOIN Examination ex ON er.exam_id = ex.exam_id
  JOIN Evidence e ON ex.evidence_id = e.evidence_id
  JOIN CriminalCase cc ON e.case_id = cc.case_id
  WHERE cc.fir_number LIKE 'SYN/%';

DELETE ex FROM Examination ex
  JOIN Evidence e ON ex.evidence_id = e.evidence_id
  JOIN CriminalCase cc ON e.case_id = cc.case_id
  WHERE cc.fir_number LIKE 'SYN/%';

-- ─── Court ──────────────────────────────────────────────────

DELETE cs FROM CourtSubmission cs
  JOIN CriminalCase cc ON cs.case_id = cc.case_id
  WHERE cc.fir_number LIKE 'SYN/%';

DELETE h FROM Hearing h
  JOIN CriminalCase cc ON h.case_id = cc.case_id
  WHERE cc.fir_number LIKE 'SYN/%';

-- ─── Storage ────────────────────────────────────────────────

DELETE sl FROM StorageLog sl
  JOIN Evidence e ON sl.evidence_id = e.evidence_id
  JOIN CriminalCase cc ON e.case_id = cc.case_id
  WHERE cc.fir_number LIKE 'SYN/%';

-- ─── Media / Audit ──────────────────────────────────────────

DELETE em FROM EvidenceMedia em
  JOIN Evidence e ON em.evidence_id = e.evidence_id
  JOIN CriminalCase cc ON e.case_id = cc.case_id
  WHERE cc.fir_number LIKE 'SYN/%';

-- EscalationLog and AuditLog don't have direct case_id FK; generator doesn't populate them.

-- ─── Crime Scene ────────────────────────────────────────────

DELETE cs2 FROM CrimeScene cs2
  JOIN CriminalCase cc ON cs2.case_id = cc.case_id
  WHERE cc.fir_number LIKE 'SYN/%';

-- ─── Evidence ───────────────────────────────────────────────

DELETE e FROM Evidence e
  JOIN CriminalCase cc ON e.case_id = cc.case_id
  WHERE cc.fir_number LIKE 'SYN/%';

-- ─── Cases ──────────────────────────────────────────────────

DELETE FROM CriminalCase WHERE fir_number LIKE 'SYN/%';

-- ─── Officers ───────────────────────────────────────────────
-- Original project officers: id 1-11
-- Backup ID-based deletion to clean any orphaned synthetic records
DELETE FROM SubmissionReturn WHERE submission_id > 3;
DELETE FROM CourtSubmission WHERE submission_id > 3 OR case_id > 6 OR evidence_id > 10;
DELETE FROM Hearing WHERE hearing_id > 5 OR case_id > 6;
DELETE FROM Judge WHERE judge_id > 4;
DELETE FROM StorageLog WHERE log_id > 7 OR evidence_id > 10;
DELETE FROM StorageUnit WHERE unit_id > 6;
DELETE FROM StorageFacility WHERE facility_id > 5;
DELETE FROM ExaminationReport WHERE exam_id > 5;
DELETE FROM Examination WHERE exam_id > 5 OR evidence_id > 10;
DELETE FROM Examiner WHERE examiner_id > 5;
DELETE FROM ForensicLab WHERE lab_id > 4;
DELETE FROM AlertLog WHERE alert_id > 5 OR evidence_id > 10;
DELETE FROM EscalationLog WHERE incident_id > 3;
DELETE FROM TamperIncident WHERE incident_id > 3 OR evidence_id > 10;
DELETE FROM CustodyTransfer WHERE transfer_id > 5;
DELETE FROM CustodyLog WHERE log_id > 9 OR evidence_id > 10;
DELETE FROM CrimeScene WHERE scene_id > 10 OR case_id > 6;
DELETE FROM EvidenceMedia WHERE evidence_id > 10;
DELETE FROM Evidence WHERE evidence_id > 10;
DELETE FROM CriminalCase WHERE case_id > 5 OR fir_number LIKE 'SYN/%';
DELETE FROM Posting WHERE officer_id > 11;
DELETE FROM Officer WHERE officer_id > 11;
DELETE FROM PoliceStation WHERE station_id > 5;

SET FOREIGN_KEY_CHECKS = 1;

-- ─── Verify Cleanup ─────────────────────────────────────────
SELECT 'Cleanup complete:' AS status;
SELECT COUNT(*) AS remaining_cases FROM CriminalCase;
SELECT COUNT(*) AS remaining_officers FROM Officer;
SELECT COUNT(*) AS remaining_evidence FROM Evidence;
SELECT COUNT(*) AS remaining_custody FROM CustodyLog;
SELECT COUNT(*) AS remaining_stations FROM PoliceStation;
