import mysql.connector
import os
import hashlib
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

def run_migration():
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'forensic_coc')
    )
    cur = conn.cursor(dictionary=True)

    # 1. Add sha256_hash column if missing
    cur.execute("""
        SELECT COUNT(*) AS cnt FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'EvidenceMedia'
          AND COLUMN_NAME = 'sha256_hash'
    """)
    res = cur.fetchone()
    if res['cnt'] == 0:
        cur.execute("ALTER TABLE EvidenceMedia ADD COLUMN sha256_hash VARCHAR(64) NULL AFTER notes;")
        conn.commit()
        print("[MIGRATION] Added sha256_hash column to EvidenceMedia.")
    else:
        print("[MIGRATION] sha256_hash column already exists.")

    # 2. Fix file_path
    cur.execute("""
        UPDATE EvidenceMedia 
        SET file_path = CONCAT('evidence_photos/', file_name) 
        WHERE file_name IS NOT NULL 
          AND (file_path IS NULL OR file_path = 'evidence_photos/placeholder.png')
    """)
    conn.commit()

    # 3. Calculate SHA-256 for all existing media files
    cur.execute("SELECT media_id, file_name, file_path FROM EvidenceMedia")
    media_rows = cur.fetchall()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    photos_dir = os.path.join(base_dir, 'static', 'evidence_photos')

    for r in media_rows:
        fname = r['file_name']
        fp = os.path.join(photos_dir, fname)
        if os.path.isfile(fp):
            with open(fp, 'rb') as f:
                h = hashlib.sha256(f.read()).hexdigest()
            cur.execute("UPDATE EvidenceMedia SET sha256_hash = %s WHERE media_id = %s", (h, r['media_id']))
            print(f"[MIGRATION] Updated Media ID {r['media_id']} ({fname}) -> SHA256: {h[:16]}...")
        else:
            print(f"[MIGRATION] File not found for Media ID {r['media_id']}: {fp}")

    conn.commit()
    cur.close()
    conn.close()
    print("[MIGRATION] Complete.")

if __name__ == "__main__":
    run_migration()
