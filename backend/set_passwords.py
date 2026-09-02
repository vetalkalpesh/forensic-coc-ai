import mysql.connector
import os
from werkzeug.security import generate_password_hash

DB = dict(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'forensic_coc'),
    charset='utf8mb4'
)

c = mysql.connector.connect(**DB)
cur = c.cursor()

# Add column if not exists
try:
    cur.execute("ALTER TABLE Officer ADD COLUMN password_hash VARCHAR(255)")
    print("Column added")
except Exception as e:
    print("Column may exist:", e)

# Update passwords
pwd = generate_password_hash('password123')
cur.execute("UPDATE Officer SET password_hash = %s", (pwd,))
c.commit()
print("Updated all passwords to password123")

cur.close()
c.close()
