import mysql.connector, os
c = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'forensic_coc')
)
cur = c.cursor(dictionary=True)
cur.execute('SELECT o.badge_number, o.full_name, d.title, d.rank_level FROM Officer o JOIN Designation d ON o.designation_id=d.designation_id')
for row in cur.fetchall():
    print(f"{row['badge_number']}: {row['title']} (Rank: {row['rank_level']})")
