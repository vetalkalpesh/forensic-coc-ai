import mysql.connector
import sys
import os

DB = dict(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'forensic_coc'),
    charset='utf8mb4'
)

def run_migration():
    try:
        conn = mysql.connector.connect(**DB)
        cur = conn.cursor()
        
        print("--- SAFE MIGRATION: Adding Geospatial Coordinates ---")
        
        # 1. Add columns if they don't exist
        tables = ['PoliceStation', 'ForensicLab', 'Court', 'StorageFacility']
        for table in tables:
            print(f"Checking {table}...")
            cur.execute(f"SHOW COLUMNS FROM {table} LIKE 'latitude'")
            if not cur.fetchone():
                print(f"Adding latitude/longitude to {table}...")
                cur.execute(f"ALTER TABLE {table} ADD COLUMN latitude DECIMAL(10,7), ADD COLUMN longitude DECIMAL(10,7)")
            else:
                print(f"Columns already exist in {table}.")
        
        # 2. Update Sample Data with realistic coordinates
        print("Updating coordinates for facilities...")
        
        updates = [
            # Police Stations
            ("UPDATE PoliceStation SET latitude=18.5314, longitude=73.8446 WHERE station_id=1",), # Shivajinagar
            ("UPDATE PoliceStation SET latitude=19.1136, longitude=72.8697 WHERE station_id=2",), # Andheri
            ("UPDATE PoliceStation SET latitude=18.5385, longitude=73.8875 WHERE station_id=3",), # Koregaon Park
            ("UPDATE PoliceStation SET latitude=18.5596, longitude=73.7797 WHERE station_id=4",), # Baner
            ("UPDATE PoliceStation SET latitude=19.0178, longitude=72.8478 WHERE station_id=5",), # Dadar
            
            # Forensic Labs
            ("UPDATE ForensicLab SET latitude=19.0722, longitude=72.8644 WHERE lab_id=1",), # Mah FSL Kalina
            ("UPDATE ForensicLab SET latitude=18.5308, longitude=73.8475 WHERE lab_id=2",), # Pune Regional FSL
            ("UPDATE ForensicLab SET latitude=18.5574, longitude=73.8016 WHERE lab_id=3",), # Digital FSL Pune
            ("UPDATE ForensicLab SET latitude=18.9475, longitude=72.8333 WHERE lab_id=4",), # Ballistics Mumbai
            
            # Courts
            ("UPDATE Court SET latitude=18.5258, longitude=73.8504 WHERE court_id=1",), # Pune Sessions
            ("UPDATE Court SET latitude=18.9304, longitude=72.8311 WHERE court_id=2",), # Bombay High Court
            ("UPDATE Court SET latitude=18.9284, longitude=72.8319 WHERE court_id=3",), # Mumbai Sessions
            ("UPDATE Court SET latitude=18.5285, longitude=73.8512 WHERE court_id=4",), # Pune District
            
            # Storage Facilities
            ("UPDATE StorageFacility SET latitude=18.5332, longitude=73.8455 WHERE facility_id=1",), # Pune HQ Store
            ("UPDATE StorageFacility SET latitude=19.0725, longitude=72.8640 WHERE facility_id=2",), # Mumbai FSL Storage
            ("UPDATE StorageFacility SET latitude=18.5582, longitude=73.8055 WHERE facility_id=3",), # Pune Bio Store
            ("UPDATE StorageFacility SET latitude=18.5265, longitude=73.8510 WHERE facility_id=4",), # Court Archive Pune
            ("UPDATE StorageFacility SET latitude=18.5568, longitude=73.8022 WHERE facility_id=5",), # Digital Vault
        ]
        
        for up in updates:
            cur.execute(up[0])
            
        conn.commit()
        print("✅ Migration successful!")
        
    except mysql.connector.Error as e:
        print(f"❌ Error during migration: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals() and conn.is_connected():
            cur.close()
            conn.close()

if __name__ == "__main__":
    run_migration()
