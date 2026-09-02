===============================================================
  FORENSIC EVIDENCE CHAIN OF CUSTODY SYSTEM
  Complete DBMS Project — Setup & Run Instructions
===============================================================

STEP 1 — SETUP DATABASE
────────────────────────
1. Open MySQL Workbench
2. Open: database/complete_database.sql
3. Click ⚡ (Run All) — wait for "DATABASE SETUP COMPLETE!"

STEP 2 — SET YOUR PASSWORD
────────────────────────────
1. Open: backend/app.py
2. Line ~10: change 'password': 'root' to your MySQL password
3. Save the file

STEP 3 — INSTALL LIBRARIES
────────────────────────────
Open terminal in the backend/ folder and run:
    pip install -r requirements.txt

STEP 4 — RUN
─────────────
In terminal (backend/ folder):
    python app.py

Open browser: http://localhost:5000

===============================================================
FEATURES
===============================================================
Pages:    Dashboard, Cases, Evidence, Custody, Forensic Lab,
          Storage, Court, Tamper, Alerts, Officers

Database: 31 Tables | 5 Triggers | 6 Stored Procedures |
          6 Views | 10 Queries | 7 Advanced Features

Photos/Videos: Upload from Evidence page → files saved in
               backend/static/evidence_photos/
               Click any photo/video to open fullscreen

PHOTO/VIDEO TROUBLESHOOTING
────────────────────────────
If photos don't show: check backend/static/evidence_photos/
folder exists and Flask server is running.
Placeholder image shows automatically when no photo uploaded.

===============================================================
