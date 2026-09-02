import mysql.connector
import os

c = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'forensic_coc')
)
cur = c.cursor()
cur.execute("UPDATE EvidenceMedia SET file_path = CONCAT('evidence_photos/', file_name) WHERE file_name IS NOT NULL")
c.commit()
print("Updated database records successfully!")
