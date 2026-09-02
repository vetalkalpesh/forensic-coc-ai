-- ============================================================
--  FORENSIC EVIDENCE CHAIN OF CUSTODY SYSTEM
--  COMPLETE DATABASE — MySQL 8.0
-- ============================================================
DROP DATABASE IF EXISTS forensic_coc;
CREATE DATABASE forensic_coc CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE forensic_coc;

-- ── MODULE 1: CASE MANAGEMENT ─────────────────────────────
CREATE TABLE PoliceStation (
    station_id     INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(100) NOT NULL,
    district       VARCHAR(100) NOT NULL,
    zone           VARCHAR(100) NOT NULL,
    contact_number VARCHAR(15)  NOT NULL UNIQUE
);

CREATE TABLE CaseType (
    type_id     INT AUTO_INCREMENT PRIMARY KEY,
    type_name   VARCHAR(50)  NOT NULL UNIQUE,
    description VARCHAR(255)
);

CREATE TABLE CaseStatus (
    status_id INT AUTO_INCREMENT PRIMARY KEY,
    label     ENUM('Investigation','Trial','Closed','Acquitted') NOT NULL UNIQUE
);

CREATE TABLE Court (
    court_id     INT AUTO_INCREMENT PRIMARY KEY,
    court_name   VARCHAR(100) NOT NULL,
    city         VARCHAR(100) NOT NULL,
    jurisdiction VARCHAR(100) NOT NULL
);

CREATE TABLE Department (
    dept_id   INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL,
    dept_type ENUM('Police','Forensic','Court','Storage') NOT NULL
);

CREATE TABLE Designation (
    designation_id    INT AUTO_INCREMENT PRIMARY KEY,
    title             VARCHAR(100) NOT NULL,
    rank_level        INT          NOT NULL,
    permissions_level ENUM('Junior','Senior','Supervisor','Admin') NOT NULL
);

CREATE TABLE Officer (
    officer_id     INT AUTO_INCREMENT PRIMARY KEY,
    badge_number   VARCHAR(20)  NOT NULL UNIQUE,
    full_name      VARCHAR(100) NOT NULL,
    designation_id INT          NOT NULL,
    department_id  INT          NOT NULL,
    date_joined    DATE         NOT NULL,
    is_active      TINYINT(1)   NOT NULL DEFAULT 1,
    FOREIGN KEY (designation_id) REFERENCES Designation(designation_id),
    FOREIGN KEY (department_id)  REFERENCES Department(dept_id)
);

CREATE TABLE CriminalCase (
    case_id                  INT AUTO_INCREMENT PRIMARY KEY,
    fir_number               VARCHAR(30)  NOT NULL UNIQUE,
    police_station_id        INT          NOT NULL,
    case_type_id             INT          NOT NULL,
    investigating_officer_id INT          NOT NULL,
    court_id                 INT,
    status_id                INT          NOT NULL,
    date_filed               DATE         NOT NULL,
    description              TEXT,
    FOREIGN KEY (police_station_id)        REFERENCES PoliceStation(station_id),
    FOREIGN KEY (case_type_id)             REFERENCES CaseType(type_id),
    FOREIGN KEY (investigating_officer_id) REFERENCES Officer(officer_id),
    FOREIGN KEY (court_id)                 REFERENCES Court(court_id),
    FOREIGN KEY (status_id)                REFERENCES CaseStatus(status_id)
);

-- ── MODULE 2: EVIDENCE ────────────────────────────────────
CREATE TABLE EvidenceType (
    type_id             INT AUTO_INCREMENT PRIMARY KEY,
    type_name           VARCHAR(50)  NOT NULL UNIQUE,
    storage_requirement VARCHAR(100) NOT NULL,
    degradation_period  INT          COMMENT 'Days until degradation'
);

CREATE TABLE CrimeScene (
    scene_id   INT AUTO_INCREMENT PRIMARY KEY,
    case_id    INT          NOT NULL,
    address    VARCHAR(255) NOT NULL,
    latitude   DECIMAL(10,7),
    longitude  DECIMAL(10,7),
    scene_type VARCHAR(50)  NOT NULL,
    FOREIGN KEY (case_id) REFERENCES CriminalCase(case_id)
);

CREATE TABLE Evidence (
    evidence_id         INT AUTO_INCREMENT PRIMARY KEY,
    case_id             INT          NOT NULL,
    description         VARCHAR(255) NOT NULL,
    type_id             INT          NOT NULL,
    collection_datetime DATETIME     NOT NULL,
    scene_id            INT          NOT NULL,
    collected_by        INT          NOT NULL,
    hash_value          VARCHAR(64),
    hash_algorithm      VARCHAR(20)  DEFAULT 'SHA-256',
    current_status      ENUM('Collected','In Storage','In Lab','In Court','Returned','Archived','Compromised','Expired') NOT NULL DEFAULT 'Collected',
    expiry_date         DATE,
    parent_evidence_id  INT,
    version_number      INT          NOT NULL DEFAULT 1,
    FOREIGN KEY (case_id)            REFERENCES CriminalCase(case_id),
    FOREIGN KEY (type_id)            REFERENCES EvidenceType(type_id),
    FOREIGN KEY (scene_id)           REFERENCES CrimeScene(scene_id),
    FOREIGN KEY (collected_by)       REFERENCES Officer(officer_id),
    FOREIGN KEY (parent_evidence_id) REFERENCES Evidence(evidence_id)
);

CREATE TABLE EvidenceMedia (
    media_id    INT AUTO_INCREMENT PRIMARY KEY,
    evidence_id INT          NOT NULL,
    file_path   VARCHAR(500) NOT NULL,
    file_name   VARCHAR(255) NOT NULL,
    media_type  ENUM('photo','video','document') NOT NULL DEFAULT 'photo',
    event_type  ENUM('Collection','Transfer','Tamper','CourtSubmission','Other') NOT NULL,
    taken_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    taken_by    INT          NOT NULL,
    notes       VARCHAR(500),
    FOREIGN KEY (evidence_id) REFERENCES Evidence(evidence_id),
    FOREIGN KEY (taken_by)    REFERENCES Officer(officer_id)
);

-- ── MODULE 3: CHAIN OF CUSTODY ────────────────────────────
CREATE TABLE CustodyLog (
    log_id                INT AUTO_INCREMENT PRIMARY KEY,
    evidence_id           INT          NOT NULL,
    transferred_by        INT          NOT NULL,
    received_by           INT          NOT NULL,
    transfer_datetime     DATETIME     NOT NULL,
    recorded_datetime     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reason                VARCHAR(255) NOT NULL,
    condition_at_transfer VARCHAR(255) NOT NULL,
    parent_log_id         INT,
    FOREIGN KEY (evidence_id)    REFERENCES Evidence(evidence_id),
    FOREIGN KEY (transferred_by) REFERENCES Officer(officer_id),
    FOREIGN KEY (received_by)    REFERENCES Officer(officer_id),
    FOREIGN KEY (parent_log_id)  REFERENCES CustodyLog(log_id)
);

CREATE TABLE CustodyTransfer (
    transfer_id        INT AUTO_INCREMENT PRIMARY KEY,
    log_id             INT          NOT NULL,
    from_department_id INT          NOT NULL,
    to_department_id   INT          NOT NULL,
    transfer_mode      VARCHAR(50)  NOT NULL,
    authorized_by      INT          NOT NULL,
    FOREIGN KEY (log_id)             REFERENCES CustodyLog(log_id),
    FOREIGN KEY (from_department_id) REFERENCES Department(dept_id),
    FOREIGN KEY (to_department_id)   REFERENCES Department(dept_id),
    FOREIGN KEY (authorized_by)      REFERENCES Officer(officer_id)
);

CREATE TABLE AuditLog (
    audit_id   INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50)  NOT NULL,
    record_id  INT          NOT NULL,
    old_values TEXT,
    new_values TEXT,
    changed_by INT,
    changed_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── MODULE 4: FORENSIC LAB ────────────────────────────────
CREATE TABLE ForensicLab (
    lab_id               INT AUTO_INCREMENT PRIMARY KEY,
    lab_name             VARCHAR(100) NOT NULL,
    address              VARCHAR(255) NOT NULL,
    accreditation_number VARCHAR(50)  NOT NULL UNIQUE,
    specialization       VARCHAR(100) NOT NULL,
    contact_number       VARCHAR(15)
);

CREATE TABLE Examiner (
    examiner_id    INT AUTO_INCREMENT PRIMARY KEY,
    full_name      VARCHAR(100) NOT NULL,
    lab_id         INT          NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    qualification  VARCHAR(100) NOT NULL,
    FOREIGN KEY (lab_id) REFERENCES ForensicLab(lab_id)
);

CREATE TABLE ExaminationType (
    type_id               INT AUTO_INCREMENT PRIMARY KEY,
    type_name             VARCHAR(100) NOT NULL UNIQUE,
    typical_duration_days INT          NOT NULL,
    equipment_required    VARCHAR(255)
);

CREATE TABLE Examination (
    exam_id          INT AUTO_INCREMENT PRIMARY KEY,
    evidence_id      INT          NOT NULL,
    examiner_id      INT          NOT NULL,
    exam_type_id     INT          NOT NULL,
    start_date       DATE         NOT NULL,
    end_date         DATE,
    status           ENUM('Pending','In Progress','Completed','Overdue') NOT NULL DEFAULT 'Pending',
    findings_summary TEXT,
    FOREIGN KEY (evidence_id)  REFERENCES Evidence(evidence_id),
    FOREIGN KEY (examiner_id)  REFERENCES Examiner(examiner_id),
    FOREIGN KEY (exam_type_id) REFERENCES ExaminationType(type_id)
);

CREATE TABLE ExaminationReport (
    report_id     INT AUTO_INCREMENT PRIMARY KEY,
    exam_id       INT          NOT NULL UNIQUE,
    report_text   TEXT         NOT NULL,
    filed_on      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    filed_by      INT          NOT NULL,
    is_admissible TINYINT(1)   NOT NULL DEFAULT 1,
    FOREIGN KEY (exam_id)  REFERENCES Examination(exam_id),
    FOREIGN KEY (filed_by) REFERENCES Officer(officer_id)
);

-- ── MODULE 5: STORAGE ─────────────────────────────────────
CREATE TABLE StorageFacility (
    facility_id      INT AUTO_INCREMENT PRIMARY KEY,
    facility_name    VARCHAR(100) NOT NULL,
    address          VARCHAR(255) NOT NULL,
    facility_type    VARCHAR(50)  NOT NULL,
    managing_dept_id INT          NOT NULL,
    FOREIGN KEY (managing_dept_id) REFERENCES Department(dept_id)
);

CREATE TABLE StorageUnit (
    unit_id           INT AUTO_INCREMENT PRIMARY KEY,
    facility_id       INT          NOT NULL,
    unit_code         VARCHAR(20)  NOT NULL UNIQUE,
    unit_type         VARCHAR(50)  NOT NULL,
    capacity          INT          NOT NULL,
    temperature_range VARCHAR(30),
    current_count     INT          NOT NULL DEFAULT 0,
    FOREIGN KEY (facility_id) REFERENCES StorageFacility(facility_id)
);

CREATE TABLE StorageLog (
    log_id       INT AUTO_INCREMENT PRIMARY KEY,
    evidence_id  INT          NOT NULL,
    unit_id      INT          NOT NULL,
    stored_on    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    retrieved_on DATETIME,
    stored_by    INT          NOT NULL,
    FOREIGN KEY (evidence_id) REFERENCES Evidence(evidence_id),
    FOREIGN KEY (unit_id)     REFERENCES StorageUnit(unit_id),
    FOREIGN KEY (stored_by)   REFERENCES Officer(officer_id)
);

-- ── MODULE 6: COURT ───────────────────────────────────────
CREATE TABLE Judge (
    judge_id    INT AUTO_INCREMENT PRIMARY KEY,
    full_name   VARCHAR(100) NOT NULL,
    court_id    INT          NOT NULL,
    designation VARCHAR(100) NOT NULL,
    FOREIGN KEY (court_id) REFERENCES Court(court_id)
);

CREATE TABLE Hearing (
    hearing_id      INT AUTO_INCREMENT PRIMARY KEY,
    case_id         INT          NOT NULL,
    court_id        INT          NOT NULL,
    judge_id        INT          NOT NULL,
    hearing_date    DATE         NOT NULL,
    hearing_purpose VARCHAR(255) NOT NULL,
    outcome         VARCHAR(255),
    next_date       DATE,
    FOREIGN KEY (case_id)  REFERENCES CriminalCase(case_id),
    FOREIGN KEY (court_id) REFERENCES Court(court_id),
    FOREIGN KEY (judge_id) REFERENCES Judge(judge_id)
);

CREATE TABLE CourtSubmission (
    submission_id   INT AUTO_INCREMENT PRIMARY KEY,
    evidence_id     INT          NOT NULL,
    case_id         INT          NOT NULL,
    hearing_id      INT          NOT NULL,
    submitted_by    INT          NOT NULL,
    submission_date DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          ENUM('Submitted','Returned','Retained by Court') NOT NULL DEFAULT 'Submitted',
    FOREIGN KEY (evidence_id)  REFERENCES Evidence(evidence_id),
    FOREIGN KEY (case_id)      REFERENCES CriminalCase(case_id),
    FOREIGN KEY (hearing_id)   REFERENCES Hearing(hearing_id),
    FOREIGN KEY (submitted_by) REFERENCES Officer(officer_id)
);

CREATE TABLE SubmissionReturn (
    return_id     INT AUTO_INCREMENT PRIMARY KEY,
    submission_id INT          NOT NULL UNIQUE,
    return_date   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    returned_to   INT          NOT NULL,
    authorized_by INT          NOT NULL,
    notes         VARCHAR(255),
    FOREIGN KEY (submission_id) REFERENCES CourtSubmission(submission_id),
    FOREIGN KEY (returned_to)   REFERENCES Officer(officer_id),
    FOREIGN KEY (authorized_by) REFERENCES Officer(officer_id)
);

-- ── MODULE 7: TAMPER & INTEGRITY ──────────────────────────
CREATE TABLE TamperIncident (
    incident_id       INT AUTO_INCREMENT PRIMARY KEY,
    evidence_id       INT          NOT NULL,
    reported_by       INT          NOT NULL,
    reported_datetime DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description       TEXT         NOT NULL,
    severity          ENUM('Low','Medium','High','Critical') NOT NULL,
    resolution_status ENUM('Open','Under Investigation','Resolved') NOT NULL DEFAULT 'Open',
    resolved_on       DATE,
    FOREIGN KEY (evidence_id) REFERENCES Evidence(evidence_id),
    FOREIGN KEY (reported_by) REFERENCES Officer(officer_id)
);

CREATE TABLE AlertLog (
    alert_id        INT AUTO_INCREMENT PRIMARY KEY,
    alert_type      ENUM('Expiry','Tamper','Overdue','Escalation','HashMismatch','DeadManSwitch') NOT NULL,
    evidence_id     INT,
    officer_id      INT,
    generated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    message         TEXT         NOT NULL,
    is_acknowledged TINYINT(1)   NOT NULL DEFAULT 0,
    FOREIGN KEY (evidence_id) REFERENCES Evidence(evidence_id),
    FOREIGN KEY (officer_id)  REFERENCES Officer(officer_id)
);

CREATE TABLE EscalationLog (
    esc_id       INT AUTO_INCREMENT PRIMARY KEY,
    incident_id  INT          NOT NULL,
    escalated_to INT          NOT NULL,
    escalated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reason       TEXT         NOT NULL,
    FOREIGN KEY (incident_id)  REFERENCES TamperIncident(incident_id),
    FOREIGN KEY (escalated_to) REFERENCES Officer(officer_id)
);

-- ── MODULE 8: OFFICER MANAGEMENT ─────────────────────────
CREATE TABLE Posting (
    posting_id INT AUTO_INCREMENT PRIMARY KEY,
    officer_id INT  NOT NULL,
    station_id INT  NOT NULL,
    from_date  DATE NOT NULL,
    to_date    DATE,
    FOREIGN KEY (officer_id) REFERENCES Officer(officer_id),
    FOREIGN KEY (station_id) REFERENCES PoliceStation(station_id)
);

CREATE TABLE SessionLog (
    session_id  INT AUTO_INCREMENT PRIMARY KEY,
    officer_id  INT          NOT NULL,
    login_time  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    logout_time DATETIME,
    ip_address  VARCHAR(45)  NOT NULL,
    FOREIGN KEY (officer_id) REFERENCES Officer(officer_id)
);

-- Full text indexes
ALTER TABLE ExaminationReport ADD FULLTEXT INDEX ft_report_text (report_text);
ALTER TABLE Evidence          ADD FULLTEXT INDEX ft_evidence_desc (description);

-- ============================================================
--  SECTION 2 — SAMPLE DATA
-- ============================================================

INSERT INTO PoliceStation VALUES
(1,'Shivajinagar Police Station','Pune','Pune City','02025543210'),
(2,'Andheri Police Station','Mumbai','Mumbai West','02226735421'),
(3,'Koregaon Park Police Station','Pune','Pune City','02025612345'),
(4,'Baner Police Station','Pune','Pune Rural','02027432100'),
(5,'Dadar Police Station','Mumbai','Mumbai Central','02224321987');

INSERT INTO CaseType VALUES
(1,'Murder','Intentional killing of a person'),
(2,'Theft','Unlawful taking of property'),
(3,'Cybercrime','Crimes involving computers or digital networks'),
(4,'Narcotics','Drug related offences'),
(5,'Kidnapping','Unlawful confinement or abduction'),
(6,'Fraud','Deception for personal gain');

INSERT INTO CaseStatus VALUES
(1,'Investigation'),(2,'Trial'),(3,'Closed'),(4,'Acquitted');

INSERT INTO Court VALUES
(1,'Pune Sessions Court','Pune','Pune District'),
(2,'Bombay High Court','Mumbai','Maharashtra'),
(3,'Mumbai Sessions Court','Mumbai','Mumbai District'),
(4,'Pune District Court','Pune','Pune District'),
(5,'Pimpri Chinchwad Court','Pimpri','Pimpri Chinchwad');

INSERT INTO Department VALUES
(1,'Pune Crime Branch','Police'),
(2,'Mumbai Crime Branch','Police'),
(3,'State Forensic Science Lab','Forensic'),
(4,'Digital Forensics Unit','Forensic'),
(5,'Pune Court Evidence Room','Court'),
(6,'Central Evidence Storage','Storage'),
(7,'Biological Sample Storage','Storage'),
(8,'Mumbai FSL','Forensic');

INSERT INTO Designation VALUES
(1,'Constable',1,'Junior'),
(2,'Head Constable',2,'Junior'),
(3,'Assistant Sub Inspector',3,'Senior'),
(4,'Sub Inspector',4,'Senior'),
(5,'Inspector',5,'Senior'),
(6,'Deputy Superintendent',6,'Supervisor'),
(7,'Superintendent of Police',7,'Supervisor'),
(8,'Forensic Examiner',4,'Senior'),
(9,'Senior Forensic Examiner',5,'Supervisor'),
(10,'Commissioner',8,'Admin');

INSERT INTO Officer VALUES
(1,'MH-2301','Rajesh Kumar Sharma',5,1,'2010-06-15',1),
(2,'MH-2302','Priya Anand Desai',4,1,'2013-03-22',1),
(3,'MH-2303','Vikram Singh Patil',6,2,'2008-11-01',1),
(4,'MH-2304','Sunita Ramesh Joshi',8,3,'2015-07-10',1),
(5,'MH-2305','Arjun Mahesh Kulkarni',9,3,'2012-04-18',1),
(6,'MH-2306','Neha Prakash Nair',8,4,'2016-09-05',1),
(7,'MH-2307','Suresh Babu Reddy',5,2,'2009-02-14',1),
(8,'MH-2308','Kavitha Mohan Iyer',4,1,'2018-01-30',1),
(9,'MH-2309','Deepak Rajan Mehta',7,1,'2005-12-20',1),
(10,'MH-2310','Anita Suresh Bhosale',3,2,'2020-06-01',1);

INSERT INTO CriminalCase VALUES
(1,'FIR/2024/PUN/001',1,1,1,1,2,'2024-01-10','Murder case — body found at Koregaon Park. Victim: Ramesh Tiwari.'),
(2,'FIR/2024/MUM/002',2,3,7,3,1,'2024-02-14','Cybercrime — large scale banking fraud using cloned SIM cards.'),
(3,'FIR/2024/PUN/003',3,4,2,4,1,'2024-03-05','Narcotics — 5kg heroin seized from abandoned warehouse.'),
(4,'FIR/2023/MUM/004',2,2,7,3,3,'2023-11-20','Theft — jewellery worth 15 lakhs stolen from residence.'),
(5,'FIR/2024/PUN/005',4,5,1,1,1,'2024-04-18','Kidnapping — minor child abducted near school.');

INSERT INTO EvidenceType VALUES
(1,'Biological','Refrigerated -4C to 4C',90),
(2,'Digital','Climate controlled room',NULL),
(3,'Physical','Dry secure vault',NULL),
(4,'Documentary','Archival dry storage',NULL),
(5,'Chemical','Hazmat sealed storage',180),
(6,'Ballistic','Dry secure vault',NULL);

INSERT INTO CrimeScene VALUES
(1,1,'Flat 4B, Rose Apartments, Koregaon Park, Pune',18.5362,73.8938,'Indoor Residence'),
(2,2,'Cyber Cafe, Link Road, Andheri West, Mumbai',19.1334,72.8286,'Commercial Premises'),
(3,3,'Warehouse No. 7, MIDC Industrial Area, Pune',18.6298,73.7997,'Warehouse'),
(4,4,'12 Silver Oak Society, Bandra, Mumbai',19.0548,72.8402,'Indoor Residence'),
(5,5,'Near St. Marys School Gate, Baner Road, Pune',18.5590,73.7868,'Outdoor Public Area');

INSERT INTO Evidence VALUES
(1,1,'Blood sample collected from bedroom floor',1,'2024-01-10 14:30:00',1,2,NULL,'SHA-256','Collected',DATE_ADD(CURDATE(), INTERVAL 3 DAY),NULL,1),
(2,1,'Kitchen knife with suspected bloodstains',3,'2024-01-10 14:45:00',1,2,NULL,'SHA-256','In Lab',NULL,NULL,1),
(3,2,'Laptop seized from suspect — contains fraud data',2,'2024-02-14 11:00:00',2,8,'a3f5c7d9e2b1f4a8c6d0e9b3f7a2c5d8e1f6b9a4c7d2e5f8b1a3c6d9e2f5b8a1','SHA-256','In Storage',NULL,NULL,1),
(4,2,'SIM cloning device seized',2,'2024-02-14 11:15:00',2,8,'b4e6a8c2d5f7b9e1a3c6d8f2b5e7a9c1d4f6b8e0a2c5d7f9b1e3a6c8d0f2b4e6','SHA-256','In Storage',NULL,NULL,1),
(5,3,'Heroin sample 500g — lab analysis required',5,'2024-03-05 09:00:00',3,1,NULL,'SHA-256','In Lab',DATE_ADD(CURDATE(), INTERVAL 5 DAY),NULL,1),
(6,3,'Polythene packaging with fingerprints',3,'2024-03-05 09:15:00',3,1,NULL,'SHA-256','In Storage',NULL,NULL,1),
(7,1,'DNA swab taken from knife handle',1,'2024-01-11 10:00:00',1,4,NULL,'SHA-256','In Lab',DATE_ADD(CURDATE(), INTERVAL 6 DAY),2,1),
(8,4,'Jewellery box recovered from pawn shop',3,'2023-11-25 16:00:00',4,7,NULL,'SHA-256','In Court',NULL,NULL,1),
(9,5,'CCTV footage from school gate camera',2,'2024-04-18 08:00:00',5,1,'c5f7b9d1e3a6c8f0b2e4a7c9d1f3b5e7a0c2d4f6b8e1a3c5d7f9b2e4a6c8d0f2','SHA-256','In Storage',NULL,NULL,1),
(10,1,'Fingerprint lifted from window sill',3,'2024-01-10 15:00:00',1,2,NULL,'SHA-256','In Lab',NULL,NULL,1);

-- Evidence Media with placeholder paths (will show placeholder image if file missing)
INSERT INTO EvidenceMedia VALUES
(1,1,'evidence_photos/placeholder.png','blood_sample_collection.jpg','photo','Collection','2024-01-10 14:30:00',2,'Blood pool approximately 30cm diameter'),
(2,2,'evidence_photos/placeholder.png','knife_collection.jpg','photo','Collection','2024-01-10 14:45:00',2,'Knife sealed in evidence bag'),
(3,3,'evidence_photos/placeholder.png','laptop_collection.jpg','photo','Collection','2024-02-14 11:00:00',8,'Laptop placed in anti-static bag'),
(4,5,'evidence_photos/placeholder.png','heroin_collection.jpg','photo','Collection','2024-03-05 09:00:00',1,'White powder in sealed polythene'),
(5,8,'evidence_photos/placeholder.png','jewellery_collection.jpg','photo','Collection','2023-11-25 16:00:00',7,'Jewellery box with broken lock'),
(6,2,'evidence_photos/placeholder.png','knife_tamper.jpg','photo','Tamper','2024-01-20 09:00:00',4,'Scratch marks observed on blade'),
(7,9,'evidence_photos/placeholder.png','cctv_footage.mp4','video','Collection','2024-04-18 08:00:00',1,'CCTV video from school gate camera');

INSERT INTO ForensicLab VALUES
(1,'Maharashtra State FSL','Kalina, Santacruz, Mumbai','NABL-FSL-2019-001','General Forensics','02226531200'),
(2,'Pune Regional FSL','Shivajinagar, Pune','NABL-FSL-2018-002','Biology & Chemistry','02025541300'),
(3,'Digital Forensics Lab Pune','Aundh IT Park, Pune','NABL-DFL-2020-003','Digital Evidence','02027891234'),
(4,'Ballistics Division Mumbai','Crawford Market, Mumbai','NABL-BAL-2017-004','Ballistics & Weapons','02223451678');

INSERT INTO Examiner VALUES
(1,'Dr. Meera Krishnan',2,'DNA Analysis','PhD Forensic Biology'),
(2,'Dr. Suresh Pawar',2,'Chemical Analysis','PhD Chemistry'),
(3,'Mr. Kiran Deshmukh',3,'Digital Forensics','MSc Cyber Security'),
(4,'Dr. Ananya Roy',1,'Fingerprint Analysis','MSc Forensic Science'),
(5,'Mr. Rajiv Agarwal',4,'Ballistics','BE Mechanical, FSL Certified');

INSERT INTO ExaminationType VALUES
(1,'DNA Analysis',21,'PCR Machine, Electrophoresis'),
(2,'Chemical Composition',14,'GC-MS, HPLC'),
(3,'Digital Forensics',10,'Forensic Workstation, Write Blocker'),
(4,'Fingerprint Analysis',7,'AFIS System, Comparison Microscope'),
(5,'Ballistics Analysis',14,'Comparison Microscope, Test Firing Range'),
(6,'Serology',10,'Luminol, Blood Typing Kit');

INSERT INTO Examination VALUES
(1,1,1,1,'2024-01-15','2024-02-05','Completed','Blood type AB+ confirmed. DNA profile extracted successfully.'),
(2,2,4,4,'2024-01-15','2024-01-22','Completed','Three distinct fingerprint sets identified on blade and handle.'),
(3,3,3,3,'2024-02-18',NULL,'In Progress','Encrypted partition found. Decryption in progress.'),
(4,5,2,2,'2024-03-10','2024-03-24','Completed','Substance confirmed as heroin — 78% purity.'),
(5,7,1,1,'2024-01-16',NULL,'Overdue',NULL),
(6,10,4,4,'2024-01-16','2024-01-23','Completed','Fingerprint matched to suspect Rajesh Verma on AFIS.');

INSERT INTO ExaminationReport VALUES
(1,1,'DNA analysis of blood sample (E001) confirms blood type AB+. DNA profile extracted and entered into database. Profile matches sample taken from suspect in custody. Conclusion: Blood is from victim Ramesh Tiwari.','2024-02-05 16:00:00',4,1),
(2,2,'Fingerprint analysis of kitchen knife (E002). Three fingerprint sets identified. Set 1 matches victim. Set 2 matches suspect Rajesh Verma. Set 3 unidentified. Conclusion: Knife handled by suspect.','2024-01-22 14:30:00',4,1),
(3,4,'Chemical analysis confirms substance is diacetylmorphine (heroin) with 78.3% purity. Weight: 498.6g after moisture correction. Conclusion: Controlled substance under NDPS Act.','2024-03-24 11:00:00',5,1),
(4,6,'Fingerprint from window sill (E010) matched to Rajesh Verma (AFIS ID: MH-2024-RV-001). Confidence level: 98.7%. Conclusion: Suspect was present at crime scene.','2024-01-23 15:00:00',4,1);

INSERT INTO StorageFacility VALUES
(1,'Pune Central Evidence Store','Shivajinagar Police HQ, Pune','Police Vault',6),
(2,'Mumbai FSL Storage','Kalina Campus, Mumbai','Forensic Storage',8),
(3,'Pune Biological Store','Aundh Road, Pune','Biohazard Cold Storage',7),
(4,'Court Archive Pune','Sessions Court Compound, Pune','Court Archive',5),
(5,'Digital Evidence Vault','Aundh IT Park, Pune','Digital Secure Room',3);

INSERT INTO StorageUnit VALUES
(1,1,'PCS-V01','Secure Vault',50,'Ambient',8),
(2,1,'PCS-V02','Weapons Locker',30,'Ambient',4),
(3,2,'MFS-F01','Freezer Unit',20,'-20C to -4C',3),
(4,3,'PBS-F01','Biological Freezer',25,'-4C to 4C',5),
(5,4,'CAP-A01','Document Archive',100,'Ambient',12),
(6,5,'DEV-S01','Digital Server Room',40,'18C to 22C',6);

INSERT INTO StorageLog VALUES
(1,3,6,'2024-02-14 13:00:00',NULL,8),
(2,4,6,'2024-02-14 13:10:00',NULL,8),
(3,6,1,'2024-03-05 11:00:00',NULL,1),
(4,8,5,'2023-11-25 18:00:00',NULL,7),
(5,9,6,'2024-04-18 10:00:00',NULL,1),
(6,2,2,'2024-01-10 16:00:00','2024-01-15 09:00:00',2),
(7,1,4,'2024-01-10 16:00:00','2024-01-15 09:00:00',2);

INSERT INTO CustodyLog VALUES
(1,1,2,2,'2024-01-10 14:30:00','2024-01-10 14:35:00','Initial collection at crime scene','Sealed in sterile container, labelled',NULL),
(2,2,2,2,'2024-01-10 14:45:00','2024-01-10 14:50:00','Initial collection at crime scene','Sealed in evidence bag, labelled',NULL),
(3,1,2,4,'2024-01-15 09:00:00','2024-01-15 09:10:00','Transfer to forensic lab for DNA analysis','Intact, sealed, no damage',1),
(4,2,2,4,'2024-01-15 09:00:00','2024-01-15 09:10:00','Transfer to forensic lab for fingerprints','Sealed, condition good',2),
(5,3,8,3,'2024-02-14 12:00:00','2024-02-14 12:05:00','Transfer to digital forensics unit','Sealed in anti-static bag, intact',NULL),
(6,5,1,2,'2024-03-05 09:00:00','2024-03-05 09:05:00','Initial collection — narcotics seizure','Sealed polythene, weight tagged',NULL),
(7,5,2,5,'2024-03-10 10:00:00','2024-03-10 10:08:00','Transfer to FSL for chemical analysis','Intact sealed bag, weight 500g',6),
(8,8,7,9,'2024-01-10 16:00:00','2024-01-10 16:05:00','Initial collection — recovered from pawnshop','Box sealed with tape, condition fair',NULL),
(9,8,9,9,'2024-02-01 10:00:00','2024-02-01 10:30:00','Transfer to court for hearing','Sealed, no damage',8);

INSERT INTO CustodyTransfer VALUES
(1,3,1,3,'Hand Delivery with Receipt',9),
(2,4,1,3,'Hand Delivery with Receipt',9),
(3,5,2,4,'Sealed Courier',3),
(4,7,1,3,'Hand Delivery with Receipt',1),
(5,9,1,5,'Court Order Transfer',9);

INSERT INTO Judge VALUES
(1,'Hon. Justice Ramesh Kulkarni',1,'Additional Sessions Judge'),
(2,'Hon. Justice Priya Mehta',3,'Metropolitan Magistrate'),
(3,'Hon. Justice Anil Sharma',1,'Sessions Judge'),
(4,'Hon. Justice Sunita Iyer',2,'High Court Judge');

INSERT INTO Hearing VALUES
(1,1,1,3,'2024-03-15','Charge framing','Charges framed against accused','2024-05-10'),
(2,1,1,3,'2024-05-10','Evidence presentation','Evidence E002 and E010 presented','2024-07-20'),
(3,2,3,2,'2024-04-20','Bail hearing','Bail rejected','2024-06-15'),
(4,4,3,2,'2024-01-10','Final arguments','Case closed — accused acquitted',NULL),
(5,3,4,1,'2024-05-25','Evidence presentation',NULL,NULL);

INSERT INTO CourtSubmission VALUES
(1,2,1,2,1,'2024-05-10 10:00:00','Submitted'),
(2,10,1,2,1,'2024-05-10 10:05:00','Submitted'),
(3,8,4,4,7,'2024-01-10 11:00:00','Returned');

INSERT INTO SubmissionReturn VALUES
(1,3,'2024-01-10 17:00:00',7,9,'Returned after final arguments. Case closed.');

INSERT INTO TamperIncident VALUES
(1,2,4,'2024-01-20 09:00:00','Scratch marks observed on knife blade during examination. Possible post-collection damage.','Medium','Under Investigation',NULL),
(2,3,3,'2024-02-20 11:00:00','Anti-static bag seal appears to have been opened and resealed. Hash verification pending.','Critical','Open',NULL),
(3,5,2,'2024-03-11 14:00:00','Weight discrepancy noted — recorded 500g at collection but current weight is 492g.','High','Open',NULL);

INSERT INTO AlertLog VALUES
(1,'Tamper',2,9,'2024-01-20 09:05:00','TAMPER ALERT: Evidence E002 (Kitchen knife) has been flagged for possible tampering. Immediate review required.',0),
(2,'HashMismatch',3,9,'2024-02-20 11:05:00','HASH MISMATCH: Evidence E003 (Laptop) SHA-256 hash does not match stored value. Evidence may have been altered.',0),
(3,'Tamper',5,9,'2024-03-11 14:05:00','TAMPER ALERT: Evidence E005 (Heroin sample) weight discrepancy detected. 8g unaccounted for.',0),
(4,'Expiry',1,2,'2024-04-03 08:00:00','EXPIRY WARNING: Evidence E001 (Blood sample) expires soon. Immediate action required.',0),
(5,'Overdue',7,5,'2024-02-13 08:00:00','OVERDUE: Evidence E007 (DNA swab) examination has been pending for 28 days with no report filed.',0);

INSERT INTO EscalationLog VALUES
(1,2,9,'2024-02-21 09:00:00','Hash mismatch on digital evidence is a critical integrity failure. Requires SP level authorization.'),
(2,3,9,'2024-03-12 10:00:00','Weight discrepancy in narcotics evidence is potentially criminal. Escalated for internal inquiry.');

-- ============================================================
--  SECTION 3 — TRIGGERS
-- ============================================================
DELIMITER //

CREATE TRIGGER trg_transfer_lock
BEFORE INSERT ON CustodyLog
FOR EACH ROW
BEGIN
    DECLARE last_receiver INT;
    DECLARE last_log_id   INT;
    SELECT received_by, log_id INTO last_receiver, last_log_id
    FROM CustodyLog WHERE evidence_id = NEW.evidence_id
    ORDER BY transfer_datetime DESC LIMIT 1;
    IF last_receiver IS NOT NULL AND last_receiver != NEW.transferred_by THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'TRANSFER BLOCKED: Evidence is currently held by another officer. Chain of custody violation.';
    END IF;
    SET NEW.parent_log_id = last_log_id;
END //

CREATE TRIGGER trg_expiry_alert
AFTER UPDATE ON Evidence
FOR EACH ROW
BEGIN
    IF NEW.expiry_date IS NOT NULL
       AND DATEDIFF(NEW.expiry_date, CURDATE()) <= 7
       AND DATEDIFF(NEW.expiry_date, CURDATE()) >= 0
       AND NEW.current_status NOT IN ('Archived','Expired') THEN
        INSERT INTO AlertLog (alert_type, evidence_id, officer_id, message)
        VALUES ('Expiry', NEW.evidence_id, NEW.collected_by,
                CONCAT('EXPIRY WARNING: Evidence E', LPAD(NEW.evidence_id,3,'0'),
                       ' (', NEW.description, ') expires on ',
                       DATE_FORMAT(NEW.expiry_date,'%d-%m-%Y'),
                       '. Only ', DATEDIFF(NEW.expiry_date, CURDATE()), ' days remaining.'));
    END IF;
END //

CREATE TRIGGER trg_tamper_cascade
AFTER UPDATE ON Evidence
FOR EACH ROW
BEGIN
    IF NEW.current_status = 'Compromised' AND OLD.current_status != 'Compromised' THEN
        UPDATE Evidence SET current_status = 'Compromised'
        WHERE parent_evidence_id = NEW.evidence_id AND current_status != 'Compromised';
        INSERT INTO AlertLog (alert_type, evidence_id, message)
        VALUES ('Tamper', NEW.evidence_id,
                CONCAT('TAMPER CASCADE: Evidence E', LPAD(NEW.evidence_id,3,'0'),
                       ' marked Compromised. All derived evidence auto-flagged.'));
        INSERT INTO AuditLog (table_name, record_id, old_values, new_values)
        VALUES ('Evidence', NEW.evidence_id,
                CONCAT('{"status":"', OLD.current_status, '"}'),
                CONCAT('{"status":"', NEW.current_status, '"}'));
    END IF;
END //

CREATE TRIGGER trg_audit_evidence
AFTER UPDATE ON Evidence
FOR EACH ROW
BEGIN
    IF OLD.current_status != NEW.current_status THEN
        INSERT INTO AuditLog (table_name, record_id, old_values, new_values)
        VALUES ('Evidence', NEW.evidence_id,
                CONCAT('{"status":"', OLD.current_status, '","version":', OLD.version_number, '}'),
                CONCAT('{"status":"', NEW.current_status, '","version":', NEW.version_number, '}'));
    END IF;
END //

CREATE TRIGGER trg_optimistic_lock
BEFORE UPDATE ON Evidence
FOR EACH ROW
BEGIN
    IF NEW.version_number != OLD.version_number + 1 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'CONCURRENT UPDATE CONFLICT: Record was modified by another user. Refresh and retry.';
    END IF;
    SET NEW.version_number = OLD.version_number + 1;
END //

DELIMITER ;

-- ============================================================
--  SECTION 4 — STORED PROCEDURES
-- ============================================================
DELIMITER //

CREATE PROCEDURE register_evidence(
    IN p_case_id      INT, IN p_description VARCHAR(255),
    IN p_type_id      INT, IN p_scene_id    INT,
    IN p_collected_by INT, IN p_hash_value  VARCHAR(64),
    IN p_expiry_date  DATE,IN p_unit_id     INT,
    IN p_media_path   VARCHAR(500), IN p_media_type VARCHAR(10),
    OUT p_evidence_id INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
    START TRANSACTION;
        INSERT INTO Evidence (case_id, description, type_id, collection_datetime, scene_id, collected_by, hash_value, expiry_date, current_status)
        VALUES (p_case_id, p_description, p_type_id, NOW(), p_scene_id, p_collected_by, p_hash_value, p_expiry_date, 'Collected');
        SET p_evidence_id = LAST_INSERT_ID();
        INSERT INTO CustodyLog (evidence_id, transferred_by, received_by, transfer_datetime, reason, condition_at_transfer)
        VALUES (p_evidence_id, p_collected_by, p_collected_by, NOW(), 'Initial collection at crime scene', 'Newly collected, sealed and labelled');
        IF p_unit_id IS NOT NULL THEN
            INSERT INTO StorageLog (evidence_id, unit_id, stored_by) VALUES (p_evidence_id, p_unit_id, p_collected_by);
            UPDATE StorageUnit SET current_count = current_count + 1 WHERE unit_id = p_unit_id;
            UPDATE Evidence SET current_status = 'In Storage', version_number = version_number + 1 WHERE evidence_id = p_evidence_id;
        END IF;
        IF p_media_path IS NOT NULL AND p_media_path != '' THEN
            INSERT INTO EvidenceMedia (evidence_id, file_path, file_name, media_type, event_type, taken_by)
            VALUES (p_evidence_id, p_media_path, p_media_path, IFNULL(p_media_type,'photo'), 'Collection', p_collected_by);
        END IF;
    COMMIT;
END //

CREATE PROCEDURE transfer_custody(
    IN p_evidence_id INT, IN p_transferred_by INT, IN p_received_by INT,
    IN p_reason VARCHAR(255), IN p_condition VARCHAR(255),
    IN p_from_dept INT, IN p_to_dept INT, IN p_authorized_by INT,
    IN p_transfer_datetime DATETIME, IN p_new_status VARCHAR(30)
)
BEGIN
    DECLARE v_log_id INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
    START TRANSACTION;
        INSERT INTO CustodyLog (evidence_id, transferred_by, received_by, transfer_datetime, reason, condition_at_transfer)
        VALUES (p_evidence_id, p_transferred_by, p_received_by, p_transfer_datetime, p_reason, p_condition);
        SET v_log_id = LAST_INSERT_ID();
        INSERT INTO CustodyTransfer (log_id, from_department_id, to_department_id, transfer_mode, authorized_by)
        VALUES (v_log_id, p_from_dept, p_to_dept, 'Hand Delivery with Receipt', p_authorized_by);
        UPDATE Evidence SET current_status = p_new_status, version_number = version_number + 1 WHERE evidence_id = p_evidence_id;
        UPDATE StorageLog SET retrieved_on = NOW() WHERE evidence_id = p_evidence_id AND retrieved_on IS NULL;
    COMMIT;
END //

CREATE PROCEDURE generate_custody_report(IN p_evidence_id INT)
BEGIN
    SELECT e.evidence_id, e.description, et.type_name, e.collection_datetime, e.current_status, cc.fir_number
    FROM Evidence e JOIN EvidenceType et ON e.type_id=et.type_id JOIN CriminalCase cc ON e.case_id=cc.case_id
    WHERE e.evidence_id = p_evidence_id;

    SELECT cl.log_id, o1.full_name AS transferred_by, o2.full_name AS received_by,
           COALESCE(d1.dept_name,'Crime Scene') AS from_dept, COALESCE(d2.dept_name,'Same Unit') AS to_dept,
           cl.transfer_datetime, cl.recorded_datetime,
           TIMESTAMPDIFF(HOUR, cl.transfer_datetime, cl.recorded_datetime) AS delay_hours,
           cl.reason, cl.condition_at_transfer
    FROM CustodyLog cl JOIN Officer o1 ON cl.transferred_by=o1.officer_id JOIN Officer o2 ON cl.received_by=o2.officer_id
    LEFT JOIN CustodyTransfer ct ON ct.log_id=cl.log_id
    LEFT JOIN Department d1 ON ct.from_department_id=d1.dept_id LEFT JOIN Department d2 ON ct.to_department_id=d2.dept_id
    WHERE cl.evidence_id = p_evidence_id ORDER BY cl.transfer_datetime;

    SELECT em.file_path, em.file_name, em.media_type, em.event_type, em.taken_at, o.full_name AS taken_by, em.notes
    FROM EvidenceMedia em JOIN Officer o ON em.taken_by=o.officer_id
    WHERE em.evidence_id = p_evidence_id ORDER BY em.taken_at;
END //

CREATE PROCEDURE verify_evidence_hash(IN p_evidence_id INT, IN p_current_hash VARCHAR(64), OUT p_result VARCHAR(50))
BEGIN
    DECLARE v_stored_hash VARCHAR(64);
    DECLARE v_description VARCHAR(255);
    SELECT hash_value, description INTO v_stored_hash, v_description FROM Evidence WHERE evidence_id = p_evidence_id;
    IF v_stored_hash IS NULL THEN
        SET p_result = 'NO_HASH_STORED';
    ELSEIF v_stored_hash = p_current_hash THEN
        SET p_result = 'HASH_VERIFIED_INTACT';
    ELSE
        SET p_result = 'HASH_MISMATCH_TAMPERED';
        INSERT INTO TamperIncident (evidence_id, reported_by, description, severity)
        VALUES (p_evidence_id, 1, CONCAT('SHA-256 hash mismatch for: ', v_description, '. Evidence may have been altered.'), 'Critical');
        UPDATE Evidence SET current_status='Compromised', version_number=version_number+1 WHERE evidence_id=p_evidence_id;
        INSERT INTO AlertLog (alert_type, evidence_id, message)
        VALUES ('HashMismatch', p_evidence_id, CONCAT('CRITICAL: Hash mismatch on evidence E', LPAD(p_evidence_id,3,'0'), '. Digital evidence integrity compromised.'));
    END IF;
END //

CREATE PROCEDURE close_case(IN p_case_id INT, IN p_closed_by INT, IN p_outcome VARCHAR(255))
BEGIN
    DECLARE v_status_id INT;
    SELECT status_id INTO v_status_id FROM CaseStatus WHERE label = p_outcome;
    START TRANSACTION;
        UPDATE Evidence SET current_status='Archived', version_number=version_number+1
        WHERE case_id=p_case_id AND current_status NOT IN ('Compromised','Expired');
        UPDATE CriminalCase SET status_id=v_status_id WHERE case_id=p_case_id;
        INSERT INTO AuditLog (table_name, record_id, old_values, new_values, changed_by)
        VALUES ('CriminalCase', p_case_id, '{"status":"Trial"}', CONCAT('{"status":"', p_outcome, '"}'), p_closed_by);
    COMMIT;
    SELECT CONCAT('Case ', p_case_id, ' closed. Outcome: ', p_outcome) AS result;
END //

CREATE PROCEDURE dead_man_switch()
BEGIN
    INSERT INTO AlertLog (alert_type, evidence_id, officer_id, message)
    SELECT 'DeadManSwitch', e.evidence_id, e.collected_by,
           CONCAT('DEAD MAN SWITCH: Evidence E', LPAD(e.evidence_id,3,'0'),
                  ' (', e.description, ') has had NO activity for 30+ days. Last activity: ',
                  DATE(MAX(cl.transfer_datetime)), '. Immediate review required.')
    FROM Evidence e
    JOIN CriminalCase cc ON e.case_id=cc.case_id
    JOIN CaseStatus cs ON cc.status_id=cs.status_id
    JOIN CustodyLog cl ON cl.evidence_id=e.evidence_id
    WHERE cs.label NOT IN ('Closed','Acquitted')
      AND e.current_status NOT IN ('Archived','Expired','Compromised')
    GROUP BY e.evidence_id, e.description, e.collected_by
    HAVING DATEDIFF(CURDATE(), MAX(cl.transfer_datetime)) > 30;
    SELECT CONCAT(ROW_COUNT(), ' dead man switch alerts generated.') AS result;
END //

DELIMITER ;

-- ============================================================
--  SECTION 5 — VIEWS
-- ============================================================
CREATE VIEW CurrentCustodyView AS
SELECT e.evidence_id, e.description, et.type_name, e.current_status,
       o.full_name AS currently_with, d.dept_name,
       cl.transfer_datetime AS since,
       DATEDIFF(NOW(), cl.transfer_datetime) AS days_with_holder,
       cc.fir_number
FROM Evidence e JOIN EvidenceType et ON e.type_id=et.type_id
JOIN CriminalCase cc ON e.case_id=cc.case_id
JOIN CustodyLog cl ON cl.evidence_id=e.evidence_id
JOIN Officer o ON cl.received_by=o.officer_id
LEFT JOIN CustodyTransfer ct ON ct.log_id=cl.log_id
LEFT JOIN Department d ON ct.to_department_id=d.dept_id
WHERE cl.log_id=(SELECT MAX(log_id) FROM CustodyLog WHERE evidence_id=e.evidence_id);

CREATE VIEW OverdueExaminationView AS
SELECT e.evidence_id, e.description, ex.exam_id, ext.type_name AS exam_type,
       exr.full_name AS examiner, fl.lab_name, ex.start_date,
       DATEDIFF(CURDATE(), ex.start_date) AS days_pending,
       ext.typical_duration_days AS sla_days
FROM Examination ex JOIN Evidence e ON ex.evidence_id=e.evidence_id
JOIN Examiner exr ON ex.examiner_id=exr.examiner_id
JOIN ForensicLab fl ON exr.lab_id=fl.lab_id
JOIN ExaminationType ext ON ex.exam_type_id=ext.type_id
LEFT JOIN ExaminationReport er ON er.exam_id=ex.exam_id
WHERE er.report_id IS NULL AND DATEDIFF(CURDATE(), ex.start_date) > ext.typical_duration_days;

CREATE VIEW ExpiringEvidenceView AS
SELECT e.evidence_id, e.description, e.expiry_date,
       DATEDIFF(e.expiry_date, CURDATE()) AS days_remaining,
       su.unit_code, sf.facility_name, o.full_name AS collected_by, cc.fir_number
FROM Evidence e JOIN CriminalCase cc ON e.case_id=cc.case_id
JOIN Officer o ON e.collected_by=o.officer_id
JOIN StorageLog sl ON sl.evidence_id=e.evidence_id AND sl.retrieved_on IS NULL
JOIN StorageUnit su ON sl.unit_id=su.unit_id JOIN StorageFacility sf ON su.facility_id=sf.facility_id
WHERE e.expiry_date IS NOT NULL
  AND e.expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
  AND e.current_status NOT IN ('Archived','Expired');

CREATE VIEW EvidenceInCourtView AS
SELECT cs.submission_id, e.evidence_id, e.description, cc.fir_number,
       h.hearing_date, h.hearing_purpose, j.full_name AS judge,
       o.full_name AS submitted_by, cs.submission_date,
       DATEDIFF(CURDATE(), cs.submission_date) AS days_in_court
FROM CourtSubmission cs JOIN Evidence e ON cs.evidence_id=e.evidence_id
JOIN CriminalCase cc ON cs.case_id=cc.case_id JOIN Hearing h ON cs.hearing_id=h.hearing_id
JOIN Judge j ON h.judge_id=j.judge_id JOIN Officer o ON cs.submitted_by=o.officer_id
LEFT JOIN SubmissionReturn sr ON sr.submission_id=cs.submission_id
WHERE sr.return_id IS NULL AND cs.status='Submitted';

CREATE VIEW UnresolvedTamperView AS
SELECT ti.incident_id, e.evidence_id, e.description AS evidence_description,
       e.current_status, ti.severity, ti.description AS incident_description,
       ti.reported_datetime, o.full_name AS reported_by,
       DATEDIFF(CURDATE(), ti.reported_datetime) AS days_unresolved, cc.fir_number
FROM TamperIncident ti JOIN Evidence e ON ti.evidence_id=e.evidence_id
JOIN Officer o ON ti.reported_by=o.officer_id JOIN CriminalCase cc ON e.case_id=cc.case_id
WHERE ti.resolution_status IN ('Open','Under Investigation')
ORDER BY ti.severity DESC;

CREATE VIEW TemporalAnomalyView AS
SELECT cl.log_id, e.evidence_id, e.description,
       o1.full_name AS transferred_by, o2.full_name AS received_by,
       cl.transfer_datetime, cl.recorded_datetime,
       TIMESTAMPDIFF(HOUR, cl.transfer_datetime, cl.recorded_datetime) AS delay_hours,
       CAST(CASE WHEN TIMESTAMPDIFF(HOUR, cl.transfer_datetime, cl.recorded_datetime) > 4
            THEN 'SUSPICIOUS GAP' ELSE 'Normal' END AS CHAR(20)) AS temporal_flag
FROM CustodyLog cl JOIN Evidence e ON cl.evidence_id=e.evidence_id
JOIN Officer o1 ON cl.transferred_by=o1.officer_id JOIN Officer o2 ON cl.received_by=o2.officer_id
ORDER BY delay_hours DESC;

-- ============================================================
--  SECTION 6 — QUERIES (run these in MySQL Workbench)
-- ============================================================
-- Q1: Complete Chain of Custody for Evidence 1
-- SELECT cl.log_id, o1.full_name AS from_officer, o2.full_name AS to_officer, cl.transfer_datetime, cl.reason FROM CustodyLog cl JOIN Officer o1 ON cl.transferred_by=o1.officer_id JOIN Officer o2 ON cl.received_by=o2.officer_id WHERE cl.evidence_id=1 ORDER BY cl.transfer_datetime;

-- Q2: Cases with Compromised Evidence
-- SELECT cc.fir_number, COUNT(ti.incident_id) AS tamper_count FROM TamperIncident ti JOIN Evidence e ON ti.evidence_id=e.evidence_id JOIN CriminalCase cc ON e.case_id=cc.case_id GROUP BY cc.case_id ORDER BY tamper_count DESC;

-- Q3: Overdue Examinations
-- SELECT * FROM OverdueExaminationView;

-- Q4: Expiring Evidence
-- SELECT * FROM ExpiringEvidenceView;

-- Q5: Officer with most transfers this month
-- SELECT o.full_name, COUNT(*) AS transfers FROM CustodyLog cl JOIN Officer o ON cl.received_by=o.officer_id WHERE MONTH(cl.transfer_datetime)=MONTH(CURDATE()) GROUP BY o.officer_id ORDER BY transfers DESC;

-- Q6: Month-wise evidence count
-- SELECT MONTHNAME(collection_datetime) AS month, COUNT(*) AS total FROM Evidence WHERE YEAR(collection_datetime)=YEAR(CURDATE()) GROUP BY MONTH(collection_datetime);

-- Q7: Current storage locations
-- SELECT * FROM CurrentCustodyView;

-- Q8: Hearings for Case 1
-- SELECT h.hearing_date, h.hearing_purpose, j.full_name AS judge, h.outcome FROM Hearing h JOIN Judge j ON h.judge_id=j.judge_id WHERE h.case_id=1;

-- Q9: Examiner admissibility rate
-- SELECT exr.full_name, COUNT(er.report_id) AS reports, SUM(er.is_admissible) AS admissible FROM ExaminationReport er JOIN Examination ex ON er.exam_id=ex.exam_id JOIN Examiner exr ON ex.examiner_id=exr.examiner_id GROUP BY exr.examiner_id;

-- Q10: Clean cases (no tamper incidents)
-- SELECT cc.fir_number, ct.type_name FROM CriminalCase cc JOIN CaseType ct ON cc.case_type_id=ct.type_id LEFT JOIN Evidence e ON e.case_id=cc.case_id LEFT JOIN TamperIncident ti ON ti.evidence_id=e.evidence_id WHERE ti.incident_id IS NULL GROUP BY cc.case_id;

SELECT 'DATABASE SETUP COMPLETE!' AS status,
       '31 Tables | 5 Triggers | 6 Procedures | 6 Views | 10 Queries' AS summary;
