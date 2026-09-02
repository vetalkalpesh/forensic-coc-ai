import os

# 1. Update app.py
app_path = r'c:\Users\kalpesh\Downloads\forensic\forensic_coc\backend\app.py'
with open(app_path, 'r', encoding='utf-8') as f:
    app_code = f.read()

app_code = app_code.replace(
    'officer = qry("SELECT * FROM Officer WHERE badge_number=%s", (badge,), one=True)',
    'officer = qry("SELECT o.*, d.access_level, d.title AS designation FROM Officer o JOIN Designation d ON o.designation_id=d.designation_id WHERE badge_number=%s", (badge,), one=True)'
)
app_code = app_code.replace(
    """    token = jwt.encode({
        'officer_id': officer['officer_id'],
        'full_name': officer['full_name'],
        'exp': datetime.utcnow() + timedelta(hours=12)
    }, SECRET_KEY, algorithm='HS256')
    return jsonify({'success': True, 'token': token, 'officer': {'id': officer['officer_id'], 'name': officer['full_name']}})""",
    """    token = jwt.encode({
        'officer_id': officer['officer_id'],
        'full_name': officer['full_name'],
        'access_level': officer['access_level'],
        'exp': datetime.utcnow() + timedelta(hours=12)
    }, SECRET_KEY, algorithm='HS256')
    return jsonify({'success': True, 'token': token, 'officer': {'id': officer['officer_id'], 'name': officer['full_name'], 'access_level': officer['access_level'], 'designation': officer['designation']}})"""
)
with open(app_path, 'w', encoding='utf-8') as f:
    f.write(app_code)

# 2. Update app.js
appjs_path = r'c:\Users\kalpesh\Downloads\forensic\forensic_coc\frontend\static\js\app.js'
with open(appjs_path, 'r', encoding='utf-8') as f:
    appjs_code = f.read()

appjs_code = appjs_code.replace(
    """document.addEventListener('DOMContentLoaded',()=>{
    if(!localStorage.getItem('auth_token') && !window.location.pathname.endsWith('login.html')){
        window.location.href = 'login.html';
        return;
    }
    const app=document.getElementById('app');
    if(app) app.insertAdjacentHTML('afterbegin',SIDEBAR_HTML);""",
    """document.addEventListener('DOMContentLoaded',()=>{
    if(!localStorage.getItem('auth_token') && !window.location.pathname.endsWith('login.html')){
        window.location.href = 'login.html';
        return;
    }
    const o_data = JSON.parse(localStorage.getItem('officer') || '{}');
    if (o_data.access_level && o_data.access_level < 3) {
        document.body.classList.add('is-junior');
    }
    const app=document.getElementById('app');
    if(app) app.insertAdjacentHTML('afterbegin',SIDEBAR_HTML);
    
    // Inject user identity into sidebar
    const ui = document.createElement('div');
    ui.style.cssText = 'padding: 15px; font-size: 13px; color: #aaa; border-bottom: 1px solid var(--border); margin-bottom: 10px; background: rgba(0,0,0,0.2)';
    ui.innerHTML = `<div>Logged in as: <strong>${o_data.name}</strong></div><div style="font-size: 11px; margin-top: 4px; color: var(--text3)">Rank: ${o_data.designation} (${o_data.access_level < 3 ? 'Read-Only' : 'Full Access'})</div>`;
    const nav = document.querySelector('.sidebar-nav');
    if(nav) nav.insertBefore(ui, nav.firstChild);
    """
)
with open(appjs_path, 'w', encoding='utf-8') as f:
    f.write(appjs_code)

# 3. Update style.css
css_path = r'c:\Users\kalpesh\Downloads\forensic\forensic_coc\frontend\static\css\style.css'
with open(css_path, 'a', encoding='utf-8') as f:
    f.write('\nbody.is-junior .req-senior { display: none !important; }\n')

# 4. Update HTML templates
html_patches = [
    (r'c:\Users\kalpesh\Downloads\forensic\forensic_coc\frontend\cases.html', 
     'class="btn btn-primary" onclick="openModal(\'addModal\')"',
     'class="btn btn-primary req-senior" onclick="openModal(\'addModal\')"'),
     
    (r'c:\Users\kalpesh\Downloads\forensic\forensic_coc\frontend\evidence.html',
     'class="btn btn-primary" onclick="openModal(\'addModal\')"',
     'class="btn btn-primary req-senior" onclick="openModal(\'addModal\')"'),
     
    (r'c:\Users\kalpesh\Downloads\forensic\forensic_coc\frontend\evidence.html',
     '<button class="btn btn-outline btn-sm" onclick="openUploadMore(${e.evidence_id})">',
     '<button class="btn btn-outline btn-sm req-senior" onclick="openUploadMore(${e.evidence_id})">'),
     
    (r'c:\Users\kalpesh\Downloads\forensic\forensic_coc\frontend\custody.html',
     'class="btn btn-primary" onclick="openModal(\'transferModal\')"',
     'class="btn btn-primary req-senior" onclick="openModal(\'transferModal\')"'),
     
    (r'c:\Users\kalpesh\Downloads\forensic\forensic_coc\frontend\forensic.html',
     'class="btn btn-primary" onclick="openModal(\'assignModal\')"',
     'class="btn btn-primary req-senior" onclick="openModal(\'assignModal\')"'),
     
    (r'c:\Users\kalpesh\Downloads\forensic\forensic_coc\frontend\storage.html',
     'class="btn btn-primary" onclick="openModal(\'assignModal\')"',
     'class="btn btn-primary req-senior" onclick="openModal(\'assignModal\')"'),
     
    (r'c:\Users\kalpesh\Downloads\forensic\forensic_coc\frontend\court.html',
     'class="btn btn-primary" onclick="openModal(\'submitModal\')"',
     'class="btn btn-primary req-senior" onclick="openModal(\'submitModal\')"'),
     
    (r'c:\Users\kalpesh\Downloads\forensic\forensic_coc\frontend\tamper.html',
     'class="btn btn-danger" onclick="openModal(\'reportModal\')"',
     'class="btn btn-danger req-senior" onclick="openModal(\'reportModal\')"'),
     
    (r'c:\Users\kalpesh\Downloads\forensic\forensic_coc\frontend\tamper.html',
     '<button class="btn btn-success btn-sm" onclick="resolveTamper(${ti.incident_id})">',
     '<button class="btn btn-success btn-sm req-senior" onclick="resolveTamper(${ti.incident_id})">')
]

for path, old, new in html_patches:
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    html = html.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

print("RBAC Patches Applied Successfully.")
