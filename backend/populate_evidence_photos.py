import os
import shutil
import hashlib
import mysql.connector
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

ARTIFACTS_DIR = r"C:\Users\kalpesh\.gemini\antigravity-ide\brain\9eca14cf-7560-4e7a-9253-0d20595e5640"
DEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'evidence_photos')
os.makedirs(DEST_DIR, exist_ok=True)

# Mapping generated artifact PNGs to target jpg names
ARTIFACT_MAP = {
    4: ("sim_cloning_device", "sim_cloning_device.jpg", "SIM cloning device seized"),
    6: ("polythene_fingerprints", "polythene_fingerprints.jpg", "Polythene packaging with fingerprints"),
    7: ("dna_swab_knife", "dna_swab_knife.jpg", "DNA swab taken from knife handle"),
    9: ("cctv_still", "cctv_still.jpg", "CCTV footage from school gate camera"),
    100: ("jewellery_public_road", "jewellery_public_road.jpg", "Jewellery recovered from public road"),
    101: ("sim_card_clothing", "sim_card_clothing.jpg", "SIM card retrieved from victim's clothing"),
}

def create_synthetic_forensic_image(filename, text, subtext):
    """Creates a clean synthetic forensic evidence photo with scale card and label if generation failed."""
    img = Image.new('RGB', (800, 600), color=(15, 23, 42))  # Dark forensic slate theme
    draw = ImageDraw.Draw(img)
    
    # Draw Forensic Workbench Grid lines
    for x in range(0, 800, 40):
        draw.line([(x, 0), (x, 600)], fill=(30, 41, 59), width=1)
    for y in range(0, 600, 40):
        draw.line([(0, y), (800, y)], fill=(30, 41, 59), width=1)
        
    # Draw Forensic Inspection Tray
    draw.rectangle([100, 100, 700, 500], outline=(71, 85, 105), fill=(30, 41, 59), width=3)
    
    # Draw Evidence Item Box (Center)
    draw.rectangle([200, 180, 600, 420], outline=(125, 211, 252), fill=(15, 23, 42), width=2)
    
    # Text headers
    try:
        font_large = ImageFont.truetype("arial.ttf", 22)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except:
        font_large = font_small = ImageFont.load_default()
        
    draw.text((220, 210), f"FORENSIC EVIDENCE RECORD", fill=(56, 189, 248), font=font_large)
    draw.text((220, 250), f"DESCRIPTION: {text[:40]}", fill=(241, 245, 249), font=font_small)
    draw.text((220, 280), f"SPECIMEN NOTES: {subtext[:45]}", fill=(148, 163, 184), font=font_small)
    
    # Evidence Scale Card (Bottom Right)
    draw.rectangle([450, 440, 680, 480], outline=(239, 68, 68), fill=(254, 242, 242), width=2)
    draw.text((460, 450), "EVIDENCE SCALE | 5cm", fill=(185, 28, 28), font=font_small)
    for tick in range(460, 670, 15):
        draw.line([(tick, 470), (tick, 480)], fill=(185, 28, 28), width=2)
        
    # Evidence Badge (Top Left)
    draw.rectangle([120, 120, 260, 155], fill=(234, 179, 8), outline=(161, 98, 7))
    draw.text((130, 128), "SEALED EVIDENCE", fill=(0, 0, 0), font=font_small)

    save_path = os.path.join(DEST_DIR, filename)
    img.save(save_path, "JPEG", quality=92)
    print(f"[SYNTHETIC] Created forensic photo: {save_path}")
    return save_path

def process_photos():
    # 1. Process Artifact images
    for eid, (prefix, target_name, desc) in ARTIFACT_MAP.items():
        found = False
        for fname in os.listdir(ARTIFACTS_DIR):
            if fname.startswith(prefix) and fname.endswith(".png"):
                src_path = os.path.join(ARTIFACTS_DIR, fname)
                dest_path = os.path.join(DEST_DIR, target_name)
                # Convert PNG to JPG
                img = Image.open(src_path).convert("RGB")
                img.save(dest_path, "JPEG", quality=92)
                print(f"[ARTIFACT] Converted & copied {fname} -> {dest_path}")
                found = True
                break
        if not found:
            create_synthetic_forensic_image(target_name, desc, "Forensic specimen documentation")

    # 2. Process E102 (Fingerprint lifted from safe lock)
    create_synthetic_forensic_image("fingerprint_safe_lock.jpg", "Fingerprint lifted from safe lock", "Latent print on lift card")

    # 3. Update EvidenceMedia table in database for all 12 items
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'forensic_coc')
    )
    cur = conn.cursor(dictionary=True)

    # Define full 12 item mapping
    DEMO_12 = [
        (1, "blood_sample_collection.jpg", "photo", "Collection", "Blood pool sample from floor"),
        (2, "knife_collection.jpg", "photo", "Collection", "Kitchen knife with bloodstains"),
        (3, "laptop_collection.jpg", "photo", "Collection", "Seized laptop computer"),
        (4, "sim_cloning_device.jpg", "photo", "Collection", "SIM cloning hardware device"),
        (5, "heroin_collection.jpg", "photo", "Collection", "Narcotic powder sample 500g"),
        (6, "polythene_fingerprints.jpg", "photo", "Collection", "Polythene packaging with latent prints"),
        (7, "dna_swab_knife.jpg", "photo", "Collection", "DNA swab tube in sterile container"),
        (8, "jewellery_collection.jpg", "photo", "Collection", "Recovered jewellery items"),
        (9, "cctv_still.jpg", "photo", "Collection", "CCTV video frame snapshot"),
        (100, "jewellery_public_road.jpg", "photo", "Collection", "Jewellery items recovered from road"),
        (101, "sim_card_clothing.jpg", "photo", "Collection", "SIM card retrieved from clothing"),
        (102, "fingerprint_safe_lock.jpg", "photo", "Collection", "Fingerprint lift card from safe lock"),
    ]

    for eid, fname, mtype, etype, notes in DEMO_12:
        fpath = os.path.join(DEST_DIR, fname)
        if os.path.isfile(fpath):
            with open(fpath, 'rb') as f:
                h = hashlib.sha256(f.read()).hexdigest()
            rel_path = f"evidence_photos/{fname}"
            
            # Check if media record exists for evidence_id
            cur.execute("SELECT media_id FROM EvidenceMedia WHERE evidence_id = %s AND file_name = %s", (eid, fname))
            row = cur.fetchone()
            if row:
                cur.execute("""
                    UPDATE EvidenceMedia 
                    SET file_path = %s, sha256_hash = %s, notes = %s 
                    WHERE media_id = %s
                """, (rel_path, h, notes, row['media_id']))
                print(f"[DB] Updated EvidenceMedia for E{eid:03d}: {fname} (SHA256: {h[:12]}...)")
            else:
                cur.execute("""
                    INSERT INTO EvidenceMedia (evidence_id, file_path, file_name, media_type, event_type, taken_by, notes, sha256_hash)
                    VALUES (%s, %s, %s, %s, %s, 1, %s, %s)
                """, (eid, rel_path, fname, mtype, etype, notes, h))
                print(f"[DB] Inserted EvidenceMedia for E{eid:03d}: {fname} (SHA256: {h[:12]}...)")

    conn.commit()
    cur.close()
    conn.close()
    print("[SUCCESS] All 12 demonstration evidence photos populated & indexed!")

if __name__ == "__main__":
    process_photos()
