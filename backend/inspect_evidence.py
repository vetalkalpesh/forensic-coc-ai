import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

def inspect():
    db_pass = os.getenv('DB_PASSWORD', '')
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=db_pass,
            database=os.getenv('DB_NAME', 'forensic_coc')
        )
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT e.evidence_id, e.description, et.type_name, e.current_status, e.case_id, cc.fir_number
            FROM Evidence e
            JOIN EvidenceType et ON e.type_id = et.type_id
            JOIN CriminalCase cc ON e.case_id = cc.case_id
            ORDER BY e.evidence_id
        """)
        rows = cur.fetchall()
        print(f"=== TOTAL EVIDENCE RECORDS: {len(rows)} ===")
        for r in rows:
            print(f"E{r['evidence_id']:03d} (ID: {r['evidence_id']}): {r['description']} | Type: {r['type_name']} | FIR: {r['fir_number']} | Status: {r['current_status']}")
            
        cur.execute("SELECT * FROM EvidenceMedia")
        media = cur.fetchall()
        print(f"\n=== EXISTING EVIDENCE MEDIA ({len(media)} items) ===")
        for m in media:
            print(m)
        cur.close()
        conn.close()
    except Exception as e:
        print("DB Connection error:", e)

if __name__ == "__main__":
    inspect()
