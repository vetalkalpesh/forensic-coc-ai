from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
import os
import hashlib
import jwt
from functools import wraps
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

# ── PATHS (works on Windows and Mac/Linux) ─────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR  = os.path.dirname(BASE_DIR)
FRONTEND     = os.path.join(PROJECT_DIR, 'frontend')
MEDIA_FOLDER = os.path.join(BASE_DIR, 'static', 'evidence_photos')
os.makedirs(MEDIA_FOLDER, exist_ok=True)

# ── CONFIG — ENVIRONMENT CONFIGURATION ──────────────────────────
try:
    import dotenv
    dotenv.load_dotenv(os.path.join(PROJECT_DIR, '.env'))
    dotenv.load_dotenv(os.path.join(os.path.dirname(PROJECT_DIR), '.env'))
    dotenv.load_dotenv()
except Exception:
    pass

SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-forensic-key")

app = Flask(__name__,
            static_folder=os.path.join(FRONTEND, 'static'),
            static_url_path='/static')
CORS(app)

@app.route('/uploads/<filename>')
def serve_uploads(filename):
    return send_from_directory(MEDIA_FOLDER, filename)

DB = dict(
    host=os.environ.get("DB_HOST", "localhost"),
    user=os.environ.get("DB_USER", "root"),
    password=os.environ.get("DB_PASSWORD", ""),
    database=os.environ.get("DB_NAME", "forensic_coc"),
    charset="utf8mb4"
)

ALLOWED = {'png','jpg','jpeg','gif','mp4','mov','avi','pdf'}

# ── DB HELPERS ─────────────────────────────────────────────────
def conn():
    try:
        return mysql.connector.connect(**DB)
    except mysql.connector.Error as e:
        print(f"\n❌ DATABASE CONNECTION FAILED: {e}")
        print(f"   Check: password in app.py, MySQL running, forensic_coc DB exists\n")
        raise

def qry(sql, p=None, one=False):
    db_conn = conn()
    try:
        db_cur = db_conn.cursor(dictionary=True)
        db_cur.execute(sql, p or ())
        r = db_cur.fetchone() if one else db_cur.fetchall()
        db_cur.close()
        return r
    finally:
        db_conn.close()

def exe(sql, p=None):
    db_conn = conn()
    try:
        db_cur = db_conn.cursor()
        db_cur.execute(sql, p or ())
        db_conn.commit()
        lid = db_cur.lastrowid
        db_cur.close()
        return lid
    finally:
        db_conn.close()

def allowed(fn):
    return '.' in fn and fn.rsplit('.',1)[1].lower() in ALLOWED

def is_video(fn):
    return fn.rsplit('.',1)[-1].lower() in {'mp4','mov','avi','mkv'}

def cascade_compromise(eid):
    children = qry("SELECT evidence_id FROM Evidence WHERE parent_evidence_id=%s AND current_status!='Compromised'", (eid,))
    for c in children:
        cid = c['evidence_id']
        exe("UPDATE Evidence SET current_status='Compromised', version_number=version_number+1 WHERE evidence_id=%s", (cid,))
        cascade_compromise(cid)

# ── SERVE FRONTEND ─────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory(FRONTEND, 'index.html')

@app.route('/<path:path>')
def front(path):
    # Serve API routes normally
    if path.startswith('api/') or path.startswith('uploads/'):
        return {'error': 'not found'}, 404
    fp = os.path.join(FRONTEND, path)
    if os.path.isfile(fp):
        return send_from_directory(FRONTEND, path)
    return send_from_directory(FRONTEND, 'index.html')

# Serve uploaded evidence media files
@app.route('/uploads/<path:filename>')
def uploads(filename):
    return send_from_directory(MEDIA_FOLDER, filename)

# ── AUTHENTICATION ─────────────────────────────────────────────
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
        try:
            data = jwt.decode(token.split(' ')[1], SECRET_KEY, algorithms=['HS256'])
            request.user = data
        except Exception as e:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    c = conn()
    badge = d.get('badge')
    pwd = d.get('password')
    officer = qry("SELECT o.*, d.rank_level AS access_level, d.title AS designation FROM Officer o JOIN Designation d ON o.designation_id=d.designation_id WHERE badge_number=%s", (badge,), one=True)
    if not officer or not check_password_hash(officer.get('password_hash', ''), pwd):
        return jsonify({'error': 'Invalid badge number or password'}), 401
    
    token = jwt.encode({
        'officer_id': officer['officer_id'],
        'full_name': officer['full_name'],
        'access_level': officer['access_level'],
        'exp': datetime.utcnow() + timedelta(hours=12)
    }, SECRET_KEY, algorithm='HS256')
    return jsonify({'success': True, 'token': token, 'officer': {'id': officer['officer_id'], 'name': officer['full_name'], 'access_level': officer['access_level'], 'designation': officer['designation']}})

# ── DASHBOARD ─────────────────────────────────────────────────
@app.route('/api/dashboard')
@require_auth
def dashboard():
    def n(sql): return qry(sql, one=True)['c']
    s = {
        'total_cases':     n("SELECT COUNT(*) c FROM CriminalCase"),
        'active_cases':    n("SELECT COUNT(*) c FROM CriminalCase cc JOIN CaseStatus cs ON cc.status_id=cs.status_id WHERE cs.label IN ('Investigation','Trial')"),
        'total_evidence':  n("SELECT COUNT(*) c FROM Evidence"),
        'in_lab':          n("SELECT COUNT(*) c FROM Evidence WHERE current_status='In Lab'"),
        'in_court':        n("SELECT COUNT(*) c FROM Evidence WHERE current_status='In Court'"),
        'compromised':     n("SELECT COUNT(*) c FROM Evidence WHERE current_status='Compromised'"),
        'open_alerts':     n("SELECT COUNT(*) c FROM AlertLog WHERE is_acknowledged=0"),
        'open_tamper':     n("SELECT COUNT(*) c FROM TamperIncident WHERE resolution_status!='Resolved'"),
        'expiring_soon':   n("SELECT COUNT(*) c FROM Evidence WHERE expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(),INTERVAL 7 DAY) AND current_status NOT IN ('Archived','Expired')"),
        'overdue_reports': n("SELECT COUNT(*) c FROM Examination ex LEFT JOIN ExaminationReport er ON er.exam_id=ex.exam_id WHERE er.report_id IS NULL AND ex.status!='Completed'"),
    }
    recent_cases = qry("""
        SELECT cc.case_id, cc.fir_number, ct.type_name, cs.label AS status,
               o.full_name AS officer, cc.date_filed
        FROM CriminalCase cc JOIN CaseType ct ON cc.case_type_id=ct.type_id
        JOIN CaseStatus cs ON cc.status_id=cs.status_id
        JOIN Officer o ON cc.investigating_officer_id=o.officer_id
        ORDER BY cc.date_filed DESC LIMIT 5""")
    recent_alerts = qry("""
        SELECT al.alert_id, al.alert_type, al.message, al.generated_at,
               al.is_acknowledged, e.description AS evidence_desc
        FROM AlertLog al LEFT JOIN Evidence e ON al.evidence_id=e.evidence_id
        ORDER BY al.generated_at DESC LIMIT 5""")
    return jsonify({'stats': s, 'recent_cases': recent_cases, 'recent_alerts': recent_alerts})

# ── CASES ──────────────────────────────────────────────────────
@app.route('/api/cases')
def cases():
    return jsonify(qry("""
        SELECT cc.case_id, cc.fir_number, ct.type_name, cs.label AS status,
               o.full_name AS officer, ps.name AS station,
               cc.date_filed, cc.description,
               COUNT(e.evidence_id) AS evidence_count
        FROM CriminalCase cc JOIN CaseType ct ON cc.case_type_id=ct.type_id
        JOIN CaseStatus cs ON cc.status_id=cs.status_id
        JOIN Officer o ON cc.investigating_officer_id=o.officer_id
        JOIN PoliceStation ps ON cc.police_station_id=ps.station_id
        LEFT JOIN Evidence e ON e.case_id=cc.case_id
        GROUP BY cc.case_id ORDER BY cc.date_filed DESC"""))

@app.route('/api/cases/<int:cid>')
def case_detail(cid):
    c  = qry("SELECT cc.*, ct.type_name, cs.label AS status_label, o.full_name AS officer_name, ps.name AS station_name, co.court_name FROM CriminalCase cc JOIN CaseType ct ON cc.case_type_id=ct.type_id JOIN CaseStatus cs ON cc.status_id=cs.status_id JOIN Officer o ON cc.investigating_officer_id=o.officer_id JOIN PoliceStation ps ON cc.police_station_id=ps.station_id LEFT JOIN Court co ON cc.court_id=co.court_id WHERE cc.case_id=%s", (cid,), one=True)
    ev = qry("SELECT evidence_id, description, current_status FROM Evidence WHERE case_id=%s", (cid,))
    h  = qry("SELECT h.*, j.full_name AS judge_name, ct.court_name FROM Hearing h JOIN Judge j ON h.judge_id=j.judge_id JOIN Court ct ON h.court_id=ct.court_id WHERE h.case_id=%s ORDER BY h.hearing_date", (cid,))
    return jsonify({'case': c, 'evidence': ev, 'hearings': h})

@app.route('/api/cases', methods=['POST'])
@require_auth
def add_case():
    d = request.json
    lid = exe("""INSERT INTO CriminalCase(fir_number,police_station_id,case_type_id,
        investigating_officer_id,court_id,status_id,date_filed,description)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
        (d['fir_number'],d['police_station_id'],d['case_type_id'],
         request.user['officer_id'],d.get('court_id'),
         d['status_id'],d['date_filed'],d.get('description','')))
    return jsonify({'success': True, 'case_id': lid})

# ── EVIDENCE ───────────────────────────────────────────────────
@app.route('/api/evidence')
@require_auth
def evidence():
    return jsonify(qry("""
        SELECT e.evidence_id, e.description, et.type_name, e.current_status,
               e.collection_datetime, e.expiry_date, cc.fir_number,
               o.full_name AS collected_by, e.hash_value
        FROM Evidence e JOIN EvidenceType et ON e.type_id=et.type_id
        JOIN CriminalCase cc ON e.case_id=cc.case_id
        JOIN Officer o ON e.collected_by=o.officer_id
        ORDER BY e.collection_datetime DESC"""))

@app.route('/api/evidence/<int:eid>')
def evidence_detail(eid):
    ev = qry("SELECT e.*, et.type_name, cc.fir_number, o.full_name AS collected_by_name FROM Evidence e JOIN EvidenceType et ON e.type_id=et.type_id JOIN CriminalCase cc ON e.case_id=cc.case_id JOIN Officer o ON e.collected_by=o.officer_id WHERE e.evidence_id=%s", (eid,), one=True)
    
    # Get all media with correct URL paths and sha256_hash
    media = qry("SELECT media_id, file_path, file_name, media_type, event_type, taken_at, notes, sha256_hash, (SELECT full_name FROM Officer WHERE officer_id=em.taken_by) AS taken_by FROM EvidenceMedia em WHERE evidence_id=%s ORDER BY taken_at", (eid,))
    
    # Fix media paths — prepend absolute host for frontend file:// compatibility & verify byte hashes
    for m in media:
        fname = os.path.basename(m['file_path']) if m['file_path'] else 'placeholder.png'
        m['url'] = f'http://127.0.0.1:5000/uploads/{fname}'
        m['is_video'] = is_video(fname)

        fpath = os.path.join(MEDIA_FOLDER, fname)
        if os.path.isfile(fpath):
            with open(fpath, 'rb') as f:
                curr_h = hashlib.sha256(f.read()).hexdigest()
            m['current_hash'] = curr_h
            m['stored_hash'] = m.get('sha256_hash')
            if m.get('sha256_hash'):
                m['integrity'] = 'INTACT' if curr_h == m['sha256_hash'] else 'COMPROMISED'
            else:
                m['integrity'] = 'UNVERIFIED'
        else:
            m['integrity'] = 'FILE_NOT_FOUND'

    custody = qry("SELECT cl.*, o1.full_name AS from_officer, o2.full_name AS to_officer FROM CustodyLog cl JOIN Officer o1 ON cl.transferred_by=o1.officer_id JOIN Officer o2 ON cl.received_by=o2.officer_id WHERE cl.evidence_id=%s ORDER BY cl.transfer_datetime", (eid,))
    exams = qry("SELECT ex.*, ext.type_name, exr.full_name AS examiner_name, er.report_text, er.is_admissible FROM Examination ex JOIN ExaminationType ext ON ex.exam_type_id=ext.type_id JOIN Examiner exr ON ex.examiner_id=exr.examiner_id LEFT JOIN ExaminationReport er ON er.exam_id=ex.exam_id WHERE ex.evidence_id=%s", (eid,))
    return jsonify({'evidence': ev, 'media': media, 'custody': custody, 'examinations': exams})

@app.route('/api/evidence/<int:eid>/image-integrity', methods=['GET'])
@require_auth
def evidence_image_integrity(eid):
    media = qry("SELECT media_id, file_path, file_name, sha256_hash FROM EvidenceMedia WHERE evidence_id=%s ORDER BY taken_at DESC LIMIT 1", (eid,), one=True)
    if not media or not media.get('file_name'):
        return jsonify({
            'evidence_id': f'E{eid:03d}',
            'integrity': 'NO_IMAGE',
            'message': 'No photographic evidence available for this evidence item.'
        })

    fname = os.path.basename(media['file_path']) if media.get('file_path') else 'placeholder.png'
    fpath = os.path.join(MEDIA_FOLDER, fname)
    stored_hash = media.get('sha256_hash')

    if not os.path.isfile(fpath):
        return jsonify({
            'evidence_id': f'E{eid:03d}',
            'integrity': 'FILE_NOT_FOUND',
            'stored_hash': stored_hash,
            'message': f'Image file {fname} missing from storage server.'
        }), 404

    with open(fpath, 'rb') as f:
        curr_hash = hashlib.sha256(f.read()).hexdigest()

    integrity = 'UNVERIFIED'
    if stored_hash:
        integrity = 'INTACT' if curr_hash == stored_hash else 'COMPROMISED'
    else:
        stored_hash = curr_hash

    return jsonify({
        'evidence_id': f'E{eid:03d}',
        'file_name': fname,
        'file_path': media.get('file_path'),
        'stored_hash': stored_hash,
        'current_hash': curr_hash,
        'integrity': integrity,
        'verification_type': 'Cryptographic SHA-256 Byte Hash'
    })


@app.route('/api/evidence/<int:eid>/vision-analysis', methods=['GET'])
@require_auth
def evidence_vision_analysis(eid):
    """Run Vision AI + Visual Cross-Check for a given evidence item.
    
    Requires authentication. Never fabricates visual observations.
    SHA-256 is kept strictly separate from Vision AI.
    """
    import sys as _sys
    _sys.path.insert(0, os.path.join(BASE_DIR, '..'))
    from ai.vision_inspector import VisionInspector
    from ai.visual_cross_checker import VisualCrossChecker

    # 1. Fetch DB metadata for this evidence
    ev = qry("""
        SELECT e.evidence_id, e.description, et.type_name, e.current_status, e.hash_value
        FROM Evidence e JOIN EvidenceType et ON e.type_id=et.type_id
        WHERE e.evidence_id = %s
    """, (eid,), one=True)
    if not ev:
        return jsonify({'error': f'Evidence E{eid:03d} not found.', 'status': 'NOT_FOUND'}), 404

    # 2. Fetch the most recent photo media record
    media = qry(
        "SELECT media_id, file_path, file_name, sha256_hash FROM EvidenceMedia "
        "WHERE evidence_id=%s AND media_type='photo' ORDER BY taken_at DESC LIMIT 1",
        (eid,), one=True
    )

    if not media or not media.get('file_name'):
        return jsonify({
            'evidence_id': f'E{eid:03d}',
            'status': 'NO_IMAGE',
            'message': 'No photographic evidence available for this evidence item. Visual AI analysis cannot be performed.',
            'vision_analysis': None,
            'visual_cross_check': None,
            'sha256_note': 'SHA-256 verification is separate from Vision AI and requires a file upload.'
        })

    fname = os.path.basename(media.get('file_path', media['file_name']))
    fpath = os.path.join(MEDIA_FOLDER, fname)

    if not os.path.isfile(fpath):
        return jsonify({
            'evidence_id': f'E{eid:03d}',
            'status': 'FILE_NOT_FOUND',
            'message': f'Image file "{fname}" is registered in the database but cannot be found on the server. Cannot perform Vision AI analysis.',
            'vision_analysis': None,
            'visual_cross_check': None
        }), 404

    # 3. Compute byte SHA-256 INDEPENDENTLY (not used for vision — just reported separately)
    stored_hash = media.get('sha256_hash')
    with open(fpath, 'rb') as f:
        curr_hash = hashlib.sha256(f.read()).hexdigest()
    if stored_hash:
        sha_integrity = 'INTACT' if curr_hash == stored_hash else 'COMPROMISED'
    else:
        sha_integrity = 'UNVERIFIED'
        stored_hash = curr_hash

    sha_result = {
        'evidence_id': f'E{eid:03d}',
        'file_name': fname,
        'stored_hash': stored_hash,
        'current_hash': curr_hash,
        'integrity': sha_integrity,
        'note': 'SHA-256 is a cryptographic byte-level integrity check — it is NOT a visual analysis.'
    }

    # 4. Run Vision AI Inspector
    vi = VisionInspector()
    vision_result = vi.analyze_image(fpath, eid, ev.get('description', ''))

    # 5. Run Visual Cross-Checker (against DB metadata)
    vcc = VisualCrossChecker()
    cross_result = vcc.cross_check(eid, ev, vision_result, sha_result)

    return jsonify({
        'evidence_id': f'E{eid:03d}',
        'description': ev.get('description'),
        'status': vision_result.get('status'),
        'vision_analysis': vision_result,
        'sha256_integrity': sha_result,
        'visual_cross_check': cross_result,
        'disclaimer': 'Vision AI provides probabilistic visual observations only. SHA-256 is the authoritative cryptographic integrity verification.'
    })

@app.route('/api/evidence', methods=['POST'])
@require_auth
def register_evidence():
    d     = request.form
    file  = request.files.get('media')
    mpath = ''
    mtype = 'photo'
    calculated_hash = None

    if file and allowed(file.filename):
        content = file.read()
        calculated_hash = hashlib.sha256(content).hexdigest()
        file.seek(0)
        ext      = file.filename.rsplit('.',1)[-1].lower()
        filename = secure_filename(f"E_new_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.{ext}")
        file.save(os.path.join(MEDIA_FOLDER, filename))
        mpath = f'evidence_photos/{filename}'
        mtype = 'video' if is_video(filename) else 'photo'

    c = conn()
    cur = c.cursor()
    try:
        out = [0]
        args = cur.callproc('register_evidence', [
            int(d['case_id']), d['description'], int(d['type_id']),
            int(d['scene_id']), request.user['officer_id'],
            calculated_hash,
            d.get('expiry_date') or None,
            int(d['unit_id']) if d.get('unit_id') else None,
            mpath if mpath else None,
            mtype,
            out[0]
        ])
        c.commit()
        new_eid = args[-1]
        return jsonify({'success': True, 'evidence_id': new_eid})
    except Exception as e:
        c.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        cur.close(); c.close()

@app.route('/api/evidence/<int:eid>/media', methods=['POST'])
@require_auth
def upload_media(eid):
    file = request.files.get('media')
    if not file or not allowed(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    file_bytes = file.read()
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    ext      = file.filename.rsplit('.',1)[-1].lower()
    filename = secure_filename(f"E{eid}_{request.form.get('event_type','other')}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.{ext}")
    
    with open(os.path.join(MEDIA_FOLDER, filename), 'wb') as f:
        f.write(file_bytes)

    mtype = 'video' if is_video(filename) else 'photo'
    exe("""INSERT INTO EvidenceMedia(evidence_id,file_path,file_name,media_type,event_type,taken_by,notes,sha256_hash)
           VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
        (eid, f'evidence_photos/{filename}', filename, mtype,
         request.form.get('event_type','Other'),
         request.user['officer_id'],
         request.form.get('notes',''),
         sha256_hash))
    return jsonify({'success': True, 'url': f'/uploads/{filename}', 'media_type': mtype, 'sha256_hash': sha256_hash})

@app.route('/api/evidence/<int:eid>/verify-hash', methods=['POST'])
@require_auth
def verify_hash(eid):
    file = request.files.get('media')
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    h = hashlib.sha256(file.read()).hexdigest()
    
    c = conn()
    cur = c.cursor()
    args = cur.callproc('verify_evidence_hash', [eid, h, ''])
    c.commit()
    result = args[2]
    cur.close(); c.close()
    if result == 'HASH_MISMATCH_TAMPERED':
        cascade_compromise(eid)
    return jsonify({'result': result, 'calculated_hash': h})

# ── CUSTODY ────────────────────────────────────────────────────
@app.route('/api/custody')
@require_auth
def custody():
    return jsonify(qry("""
        SELECT cl.log_id, cl.evidence_id, e.description AS evidence_desc,
               o1.full_name AS from_officer, o2.full_name AS to_officer,
               cl.transfer_datetime, cl.reason, cl.condition_at_transfer, cc.fir_number
        FROM CustodyLog cl JOIN Evidence e ON cl.evidence_id=e.evidence_id
        JOIN Officer o1 ON cl.transferred_by=o1.officer_id
        JOIN Officer o2 ON cl.received_by=o2.officer_id
        JOIN CriminalCase cc ON e.case_id=cc.case_id
        ORDER BY cl.transfer_datetime DESC LIMIT 60"""))

@app.route('/api/custody/transfer', methods=['POST'])
@require_auth
def transfer():
    d = request.json
    c = conn()
    cur = c.cursor()
    try:
        cur.callproc('transfer_custody', [
            int(d['evidence_id']), request.user['officer_id'], int(d['received_by']),
            d['reason'], d['condition'],
            int(d['from_dept']), int(d['to_dept']), int(d['authorized_by']),
            d.get('transfer_datetime', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            d['new_status']
        ])
        c.commit()
        return jsonify({'success': True})
    except Exception as e:
        c.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        cur.close(); c.close()

@app.route('/api/custody/report/<int:eid>')
def custody_report(eid):
    c = conn()
    cur = c.cursor(dictionary=True)
    cur.callproc('generate_custody_report', [eid])
    results = [list(r.fetchall()) for r in cur.stored_results()]
    cur.close(); c.close()
    media = results[2] if len(results) > 2 else []
    for m in media:
        fname = os.path.basename(m.get('file_path','')) or 'placeholder.png'
        m['url'] = f'/uploads/{fname}'
        m['is_video'] = is_video(fname)
    return jsonify({'evidence': results[0][0] if results else {}, 'chain': results[1] if len(results)>1 else [], 'media': media})

# ── EXAMINATIONS ───────────────────────────────────────────────
@app.route('/api/examinations')
@require_auth
def examinations():
    return jsonify(qry("""
        SELECT ex.exam_id, e.evidence_id, e.description AS evidence,
               exr.full_name AS examiner, fl.lab_name, ext.type_name AS exam_type,
               ex.start_date, ex.end_date, ex.status, ex.findings_summary,
               er.report_id, er.is_admissible, cc.fir_number
        FROM Examination ex JOIN Evidence e ON ex.evidence_id=e.evidence_id
        JOIN Examiner exr ON ex.examiner_id=exr.examiner_id
        JOIN ForensicLab fl ON exr.lab_id=fl.lab_id
        JOIN ExaminationType ext ON ex.exam_type_id=ext.type_id
        JOIN CriminalCase cc ON e.case_id=cc.case_id
        LEFT JOIN ExaminationReport er ON er.exam_id=ex.exam_id
        ORDER BY ex.start_date DESC"""))

@app.route('/api/examinations', methods=['POST'])
@require_auth
def add_exam():
    d = request.json
    lid = exe("INSERT INTO Examination(evidence_id,examiner_id,exam_type_id,start_date,status) VALUES(%s,%s,%s,%s,'Pending')",
              (d['evidence_id'], d['examiner_id'], d['exam_type_id'], d['start_date']))
    exe("UPDATE Evidence SET current_status='In Lab', version_number=version_number+1 WHERE evidence_id=%s", (d['evidence_id'],))
    return jsonify({'success': True, 'exam_id': lid})

@app.route('/api/examinations/<int:exam_id>/report', methods=['POST'])
@require_auth
def file_report(exam_id):
    d = request.json
    exe("""INSERT INTO ExaminationReport(exam_id,report_text,filed_by,is_admissible)
           VALUES(%s,%s,%s,%s) ON DUPLICATE KEY UPDATE report_text=%s, filed_by=%s""",
        (exam_id, d['report_text'], request.user['officer_id'], d.get('is_admissible',1),
         d['report_text'], request.user['officer_id']))
    exe("UPDATE Examination SET status='Completed', end_date=CURDATE() WHERE exam_id=%s", (exam_id,))
    return jsonify({'success': True})

# ── STORAGE ────────────────────────────────────────────────────
@app.route('/api/storage')
def storage():
    units = qry("""SELECT su.unit_id, su.unit_code, su.unit_type, su.capacity, su.current_count,
        su.capacity-su.current_count AS available, sf.facility_name, sf.facility_type, su.temperature_range
        FROM StorageUnit su JOIN StorageFacility sf ON su.facility_id=sf.facility_id ORDER BY sf.facility_name""")
    items = qry("""SELECT sl.log_id, e.evidence_id, e.description, su.unit_code,
        sf.facility_name, sl.stored_on, o.full_name AS stored_by,
        DATEDIFF(CURDATE(),sl.stored_on) AS days_stored
        FROM StorageLog sl JOIN Evidence e ON sl.evidence_id=e.evidence_id
        JOIN StorageUnit su ON sl.unit_id=su.unit_id
        JOIN StorageFacility sf ON su.facility_id=sf.facility_id
        JOIN Officer o ON sl.stored_by=o.officer_id
        WHERE sl.retrieved_on IS NULL ORDER BY sl.stored_on DESC""")
    return jsonify({'units': units, 'current_items': items})

# ── COURT ──────────────────────────────────────────────────────
@app.route('/api/hearings')
@require_auth
def hearings():
    return jsonify(qry("""
        SELECT h.hearing_id, h.hearing_date, h.hearing_purpose, h.outcome, h.next_date,
               cc.fir_number, j.full_name AS judge, ct.court_name,
               COUNT(cs.submission_id) AS evidence_count
        FROM Hearing h JOIN CriminalCase cc ON h.case_id=cc.case_id
        JOIN Judge j ON h.judge_id=j.judge_id JOIN Court ct ON h.court_id=ct.court_id
        LEFT JOIN CourtSubmission cs ON cs.hearing_id=h.hearing_id
        GROUP BY h.hearing_id ORDER BY h.hearing_date DESC"""))

@app.route('/api/court/submit', methods=['POST'])
@require_auth
def court_submit():
    d = request.json
    exe("INSERT INTO CourtSubmission(evidence_id,case_id,hearing_id,submitted_by) VALUES(%s,%s,%s,%s)",
        (d['evidence_id'], d['case_id'], d['hearing_id'], request.user['officer_id']))
    exe("UPDATE Evidence SET current_status='In Court', version_number=version_number+1 WHERE evidence_id=%s", (d['evidence_id'],))
    return jsonify({'success': True})

# ── TAMPER ─────────────────────────────────────────────────────
@app.route('/api/tamper')
@require_auth
def tamper():
    return jsonify(qry("""
        SELECT ti.incident_id, e.evidence_id, e.description AS evidence,
               ti.severity, ti.description AS incident_desc,
               ti.reported_datetime, ti.resolution_status,
               o.full_name AS reported_by, cc.fir_number
        FROM TamperIncident ti JOIN Evidence e ON ti.evidence_id=e.evidence_id
        JOIN Officer o ON ti.reported_by=o.officer_id
        JOIN CriminalCase cc ON e.case_id=cc.case_id
        ORDER BY ti.reported_datetime DESC"""))

@app.route('/api/tamper', methods=['POST'])
@require_auth
def report_tamper():
    d = request.json
    exe("INSERT INTO TamperIncident(evidence_id,reported_by,description,severity) VALUES(%s,%s,%s,%s)",
        (d['evidence_id'], request.user['officer_id'], d['description'], d['severity']))
    exe("UPDATE Evidence SET current_status='Compromised', version_number=version_number+1 WHERE evidence_id=%s", (d['evidence_id'],))
    cascade_compromise(d['evidence_id'])
    return jsonify({'success': True})

@app.route('/api/tamper/<int:tid>/resolve', methods=['POST'])
def resolve_tamper(tid):
    exe("UPDATE TamperIncident SET resolution_status='Resolved', resolved_on=CURDATE() WHERE incident_id=%s", (tid,))
    return jsonify({'success': True})

# ── ALERTS ─────────────────────────────────────────────────────
@app.route('/api/alerts')
@require_auth
def alerts():
    return jsonify(qry("""
        SELECT al.alert_id, al.alert_type, al.message, al.generated_at, al.is_acknowledged,
               e.description AS evidence_desc, o.full_name AS officer_name
        FROM AlertLog al LEFT JOIN Evidence e ON al.evidence_id=e.evidence_id
        LEFT JOIN Officer o ON al.officer_id=o.officer_id
        ORDER BY al.generated_at DESC"""))

@app.route('/api/alerts/<int:aid>/acknowledge', methods=['POST'])
@require_auth
def ack_alert(aid):
    exe("UPDATE AlertLog SET is_acknowledged=1 WHERE alert_id=%s", (aid,))
    return jsonify({'success': True})

# ── OFFICERS ───────────────────────────────────────────────────
@app.route('/api/officers')
@require_auth
def officers():
    return jsonify(qry("""
        SELECT o.officer_id, o.badge_number, o.full_name, d.title AS designation,
               dep.dept_name, o.date_joined, o.is_active
        FROM Officer o JOIN Designation d ON o.designation_id=d.designation_id
        JOIN Department dep ON o.department_id=dep.dept_id ORDER BY o.full_name"""))

# ── DEAD MAN SWITCH ────────────────────────────────────────────
@app.route('/api/dead-man-switch', methods=['POST'])
@require_auth
def dms():
    c = conn()
    cur = c.cursor(dictionary=True)
    cur.callproc('dead_man_switch', [])
    c.commit()
    results = [list(r.fetchall()) for r in cur.stored_results()]
    cur.close(); c.close()
    msg = results[0][0].get('result','Done') if results and results[0] else 'Done'
    return jsonify({'success': True, 'message': msg})

# ── VIEWS ──────────────────────────────────────────────────────
@app.route('/api/views/current-custody')
@require_auth
def v_custody():    return jsonify(qry("SELECT * FROM CurrentCustodyView"))

@app.route('/api/views/overdue-examinations')
def v_overdue():    return jsonify(qry("SELECT * FROM OverdueExaminationView"))

@app.route('/api/views/expiring-evidence')
def v_expiring():   return jsonify(qry("SELECT * FROM ExpiringEvidenceView"))

@app.route('/api/views/evidence-in-court')
def v_court():      return jsonify(qry("SELECT * FROM EvidenceInCourtView"))

@app.route('/api/views/unresolved-tamper')
def v_tamper():     return jsonify(qry("SELECT * FROM UnresolvedTamperView"))

@app.route('/api/views/temporal-anomalies')
def v_temporal():   return jsonify(qry("SELECT * FROM TemporalAnomalyView"))

# ── MAP & GEOSPATIAL ──────────────────────────────────────────
@app.route('/api/map/locations')
@require_auth
def map_locations():
    stations = qry("SELECT 'PoliceStation' as type, name, latitude, longitude, CONCAT(zone, ', ', district) as address FROM PoliceStation WHERE latitude IS NOT NULL")
    labs     = qry("SELECT 'ForensicLab' as type, lab_name as name, latitude, longitude, address FROM ForensicLab WHERE latitude IS NOT NULL")
    courts   = qry("SELECT 'Court' as type, court_name as name, latitude, longitude, city as address FROM Court WHERE latitude IS NOT NULL")
    storage  = qry("SELECT 'StorageFacility' as type, facility_name as name, latitude, longitude, address FROM StorageFacility WHERE latitude IS NOT NULL")
    scenes   = qry("SELECT 'CrimeScene' as type, address as name, latitude, longitude, scene_type as address FROM CrimeScene WHERE latitude IS NOT NULL")
    return jsonify({
        'stations': stations, 'labs': labs, 'courts': courts, 'storage': storage, 'scenes': scenes
    })

@app.route('/api/map/evidence-trail/<int:eid>')
@require_auth
def evidence_trail(eid):
    # 1. Start: Crime Scene
    start = qry("""SELECT cs.latitude, cs.longitude, cs.address, 'Crime Scene' as location_type, 
                          e.collection_datetime as timestamp
                   FROM Evidence e JOIN CrimeScene cs ON e.scene_id=cs.scene_id 
                   WHERE e.evidence_id=%s""", (eid,), one=True)
    
    # 2. Path: Physical Visits (Labs, Storage, Courts)
    
    # Refined logic for trail:
    # A true trail uses the actual coordinates of labs/storage/courts where the evidence was tagged.
    
    trail = []
    if start: trail.append(start)
    
    # Get Lab visits
    labs = qry("""SELECT fl.latitude, fl.longitude, fl.lab_name as address, 'Forensic Lab' as location_type, e.start_date as timestamp
                  FROM Examination e JOIN Examiner ex ON e.examiner_id=ex.examiner_id
                  JOIN ForensicLab fl ON ex.lab_id=fl.lab_id
                  WHERE e.evidence_id=%s""", (eid,))
    trail.extend(labs or [])
    
    # Get Storage visits
    storage = qry("""SELECT sf.latitude, sf.longitude, sf.facility_name as address, 'Storage' as location_type, sl.stored_on as timestamp
                     FROM StorageLog sl JOIN StorageUnit su ON sl.unit_id=su.unit_id
                     JOIN StorageFacility sf ON su.facility_id=sf.facility_id
                     WHERE sl.evidence_id=%s""", (eid,))
    trail.extend(storage or [])
    
    # Get Court visits
    court = qry("""SELECT c.latitude, c.longitude, c.court_name as address, 'Court' as location_type, cs.submission_date as timestamp
                   FROM CourtSubmission cs JOIN Hearing h ON cs.hearing_id=h.hearing_id
                   JOIN Court c ON h.court_id=c.court_id
                   WHERE cs.evidence_id=%s""", (eid,))
    trail.extend(court or [])
    
    # Sort entire trail by timestamp
    trail.sort(key=lambda x: str(x['timestamp']))
    
    return jsonify(trail)

# ── LOOKUPS ────────────────────────────────────────────────────
@app.route('/api/lookup/case-types')
def l_ct():      return jsonify(qry("SELECT * FROM CaseType"))
@app.route('/api/lookup/case-status')
def l_cs():      return jsonify(qry("SELECT * FROM CaseStatus"))
@app.route('/api/lookup/police-stations')
def l_ps():      return jsonify(qry("SELECT * FROM PoliceStation"))
@app.route('/api/lookup/evidence-types')
def l_et():      return jsonify(qry("SELECT * FROM EvidenceType"))
@app.route('/api/lookup/officers')
def l_o():       return jsonify(qry("SELECT officer_id, full_name, badge_number FROM Officer WHERE is_active=1"))
@app.route('/api/lookup/departments')
def l_d():       return jsonify(qry("SELECT * FROM Department"))
@app.route('/api/lookup/storage-units')
def l_su():      return jsonify(qry("SELECT su.unit_id, su.unit_code, su.unit_type, sf.facility_name, su.capacity-su.current_count AS available_slots FROM StorageUnit su JOIN StorageFacility sf ON su.facility_id=sf.facility_id WHERE su.current_count < su.capacity"))
@app.route('/api/lookup/examiners')
def l_ex():      return jsonify(qry("SELECT e.examiner_id, e.full_name, e.specialization, fl.lab_name FROM Examiner e JOIN ForensicLab fl ON e.lab_id=fl.lab_id"))
@app.route('/api/lookup/exam-types')
def l_ext():     return jsonify(qry("SELECT * FROM ExaminationType"))
@app.route('/api/lookup/courts')
def l_courts():  return jsonify(qry("SELECT * FROM Court"))
@app.route('/api/lookup/judges')
def l_judges():  return jsonify(qry("SELECT j.judge_id, j.full_name, j.designation, c.court_name FROM Judge j JOIN Court c ON j.court_id=c.court_id"))
@app.route('/api/lookup/scenes/<int:cid>')
def l_scenes(cid): return jsonify(qry("SELECT * FROM CrimeScene WHERE case_id=%s", (cid,)))
@app.route('/api/lookup/cases-list')
def l_cases():   return jsonify(qry("SELECT case_id, fir_number FROM CriminalCase ORDER BY date_filed DESC"))

# ============================================================
#  HYBRID RAG FORENSIC INTELLIGENCE PLATFORM — AI API ROUTES
# ============================================================
import sys
sys.path.insert(0, PROJECT_DIR)

from ai.hybrid_retriever import HybridRetriever
from ai.why_explainer import WhyExplainer
from ai.ai_audit import AIAuditLogger

ai_orchestrator = HybridRetriever()
why_explainer = WhyExplainer()
audit_logger = AIAuditLogger()

@app.route('/api/ai/query', methods=['POST'])
@require_auth
def ai_query():
    data = request.json or {}
    question = data.get('question', '').strip()
    method = request.args.get('method', data.get('method', 'HYBRID')).upper()

    if not question:
        return jsonify({'error': 'Question is required'}), 400

    officer_id = request.user.get('officer_id', 1)
    access_level = request.user.get('access_level', 1)
    user_role = 'Admin' if access_level >= 8 else ('Supervisor' if access_level >= 6 else 'Junior')

    result = ai_orchestrator.process_query(
        question=question,
        officer_id=officer_id,
        user_role=user_role,
        retrieval_method=method
    )
    return jsonify(result)

@app.route('/api/ai/query/<query_id>/why', methods=['GET'])
@require_auth
def ai_query_why(query_id):
    mode_arg = request.args.get('mode', 'user')
    log_rec = audit_logger.get_query_log(query_id)
    if not log_rec:
        return jsonify({'error': 'Query audit record not found'}), 404

    access_level = request.user.get('access_level', 1)
    user_role = 'Admin' if access_level >= 8 else 'Junior'

    # Re-assemble context package for explanation
    context_pkg = {
        "intent": log_rec.get("detected_intent", "GENERAL_SEARCH"),
        "entities": log_rec.get("extracted_entities", {}),
        "sources": log_rec.get("sql_sources", []),
        "conflict_warning": log_rec.get("conflict_details", ""),
    }

    explanation = why_explainer.explain(log_rec, context_pkg, user_role=user_role)
    return jsonify(explanation)

@app.route('/api/ai/investigate/<int:eid>', methods=['POST'])
@require_auth
def ai_investigate_evidence(eid):
    officer_id = request.user.get('officer_id', 1)
    question = f"Investigate evidence E{eid:03d}."
    result = ai_orchestrator.process_query(question=question, officer_id=officer_id, retrieval_method="HYBRID")
    return jsonify(result)

@app.route('/api/ai/summarize/<int:cid>', methods=['POST'])
@require_auth
def ai_summarize_case(cid):
    officer_id = request.user.get('officer_id', 1)
    c_info = qry("SELECT fir_number FROM CriminalCase WHERE case_id=%s", (cid,), one=True)
    fir = c_info['fir_number'] if c_info else f"Case {cid}"
    question = f"Summarize case {fir}."
    result = ai_orchestrator.process_query(question=question, officer_id=officer_id, retrieval_method="HYBRID")
    return jsonify(result)

@app.route('/api/ai/anomalies', methods=['GET'])
@require_auth
def ai_anomalies():
    delays = qry("SELECT * FROM TemporalAnomalyView WHERE temporal_flag = 'SUSPICIOUS GAP'")
    overdue = qry("SELECT * FROM OverdueExaminationView")
    expiring = qry("SELECT * FROM ExpiringEvidenceView")
    tamper = qry("SELECT * FROM UnresolvedTamperView")
    return jsonify({
        'custody_delays': delays,
        'overdue_examinations': overdue,
        'expiring_evidence': expiring,
        'unresolved_tamper': tamper
    })

@app.route('/api/ai/evidence/<int:eid>/anomalies', methods=['GET'])
@require_auth
def ai_evidence_anomalies(eid):
    """
    Deterministic temporal/geospatial anomaly detection for a specific evidence item.
    Uses Haversine distance and actual custody transfer timestamps.
    Returns structured anomaly findings — not proof of fraud or misconduct.
    """
    try:
        # Verify evidence exists and user has access
        ev = qry("SELECT evidence_id, description, case_id FROM Evidence WHERE evidence_id=%s", (eid,), one=True)
        if not ev:
            return jsonify({'error': f'Evidence E{eid:03d} not found'}), 404

        from ai.fact_calculator import FactCalculator
        from ai.anomaly_detector import detect_custody_anomalies

        fc = FactCalculator()
        # Fetch transfers with department coordinates
        import mysql.connector
        conn_obj = conn()
        cur = conn_obj.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT cl.log_id, cl.evidence_id, cl.transfer_datetime,
                       d1.dept_name AS from_dept_name, d2.dept_name AS to_dept_name,
                       d1.latitude AS from_lat, d1.longitude AS from_lon,
                       d2.latitude AS to_lat, d2.longitude AS to_lon
                FROM CustodyLog cl
                JOIN CustodyTransfer ct ON cl.log_id = ct.log_id
                LEFT JOIN Department d1 ON ct.from_department_id = d1.dept_id
                LEFT JOIN Department d2 ON ct.to_department_id = d2.dept_id
                WHERE cl.evidence_id = %s
                ORDER BY cl.transfer_datetime ASC
            """, (eid,))
            transfers = cur.fetchall()
        finally:
            cur.close()
            conn_obj.close()

        result = detect_custody_anomalies(transfers, evidence_id=eid)

        return jsonify({
            'success': True,
            'evidence_id': f'E{eid:03d}',
            'anomaly_detection': result,
            'threshold_kmh': 120.0,
            'coordinate_source': 'Department table — coordinates derived from authoritative facility locations (PoliceStation, ForensicLab, StorageFacility, Court)',
            'disclaimer': 'Anomalies are deterministic calculations based on recorded timestamps and geographic coordinates. They do not establish fraud or misconduct.',
        })
    except Exception as e:
        print(f"[AI Anomaly Error] {e}")
        return jsonify({'error': f'Failed to calculate anomalies: {str(e)}'}), 500


@app.route('/api/ai/evidence/<int:eid>/cross-case-links', methods=['GET'])
@require_auth
def ai_cross_case_links(eid):
    """
    RBAC-guarded cross-case evidence linkage via ChromaDB vector search.
    Returns potential semantic links — NOT definitive forensic identification.
    Verifies all results against MySQL before returning.
    Never exposes unauthorized case data.
    """
    try:
        # Verify evidence exists
        ev = qry("SELECT evidence_id, description, case_id FROM Evidence WHERE evidence_id=%s", (eid,), one=True)
        if not ev:
            return jsonify({'error': f'Evidence E{eid:03d} not found'}), 404

        officer_id = request.user.get('officer_id', 1)
        access_level = request.user.get('access_level', 1)
        user_role = 'Admin' if access_level >= 8 else ('Supervisor' if access_level >= 6 else 'Junior')

        from ai.vector_retriever import VectorRetriever
        from ai.hybrid_retriever import HybridRetriever

        vr = VectorRetriever()

        # Determine authorized case IDs for this user role
        hr = HybridRetriever()
        authorized_case_ids = hr._get_authorized_case_ids(officer_id, user_role)

        # Build search text from ExaminationReport (if available) or evidence description
        rpt = qry("""
            SELECT er.report_text FROM ExaminationReport er
            JOIN Examination ex ON er.exam_id = ex.exam_id
            WHERE ex.evidence_id = %s LIMIT 1
        """, (eid,), one=True)

        search_text = (rpt.get('report_text') if rpt else None) or ev.get('description', f'Evidence E{eid:03d}')
        threshold_arg = float(request.args.get('threshold', 0.70))

        links = vr.find_potential_links(
            evidence_id=eid,
            text_chunk=search_text,
            top_k=5,
            similarity_threshold=threshold_arg,
            authorized_case_ids=authorized_case_ids,
        )

        # Strip authorized_scope from non-admin responses
        if user_role not in ('Admin', 'Supervisor'):
            for link in links:
                link.pop('authorized_scope', None)

        return jsonify({
            'success': True,
            'evidence_id': f'E{eid:03d}',
            'links': links,
            'link_count': len(links),
            'similarity_threshold': 0.70,
            'disclaimer': 'These are POTENTIAL SEMANTIC LINKS based on vector similarity of forensic report content. They are supporting signals only and do not constitute forensic proof of a case connection.',
        })
    except Exception as e:
        print(f"[AI Cross-Case Links Error] {e}")
        return jsonify({'error': f'Failed to find cross-case links: {str(e)}'}), 500


@app.route('/api/ai/suggested-queries', methods=['GET'])
def ai_suggested_queries():
    queries = [
        "Give me the complete history of evidence E001.",
        "Where is evidence E003 currently located?",
        "Was evidence E002 tampered with?",
        "Summarize case FIR/2024/PUN/001.",
        "Which evidence has custody delays greater than 2 hours?",
        "Which biological samples are expiring soon?",
        "Which forensic examinations are overdue?",
        "Explain why evidence E003 was marked as compromised."
    ]
    return jsonify(queries)

@app.route('/api/ai/audit', methods=['GET'])
@require_auth
def ai_audit_logs():
    access_level = request.user.get('access_level', 1)
    if access_level < 6:
        return jsonify({'error': 'Unauthorized — Supervisor/Admin only'}), 403
    logs = qry("SELECT * FROM AIQueryAuditLog ORDER BY queried_at DESC LIMIT 50")
    return jsonify(logs)

if __name__ == '__main__':
    print("="*55)
    print("  Forensic Evidence Chain of Custody System")
    print("  Hybrid RAG Intelligence Platform Active")
    print("  Running at http://localhost:5000")
    print("="*55)
    app.run(debug=True, port=5000)


