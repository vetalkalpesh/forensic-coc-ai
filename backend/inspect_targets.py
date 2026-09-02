import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'forensic_coc')
)
cur = conn.cursor(dictionary=True)

target_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 100, 101, 102]
format_strings = ','.join(['%s'] * len(target_ids))

cur.execute(f"""
    SELECT e.evidence_id, e.description, et.type_name, e.current_status, e.case_id, cc.fir_number
    FROM Evidence e
    JOIN EvidenceType et ON e.type_id = et.type_id
    JOIN CriminalCase cc ON e.case_id = cc.case_id
    WHERE e.evidence_id IN ({format_strings})
    ORDER BY e.evidence_id
""", tuple(target_ids))

print("=== SPECIFIC EVIDENCE RECORDS FOR DEMO SUBSET ===")
for r in cur.fetchall():
    print(f"ID {r['evidence_id']} (E{r['evidence_id']:03d}): Description='{r['description']}' | Type='{r['type_name']}' | FIR='{r['fir_number']}' | Status='{r['current_status']}'")

cur.close()
conn.close()
