const API = '';  // same origin — Flask serves frontend too

function getAuthHeaders(headers = {}) {
    const t = localStorage.getItem('auth_token');
    if (t) headers['Authorization'] = `Bearer ${t}`;
    return headers;
}
async function handleResponse(r) {
    if (r.status === 401) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('officer');
        if (!window.location.pathname.endsWith('login.html')) window.location.href = 'login.html';
        throw new Error("Unauthorized");
    }
    if (r.status === 403) {
        toast("Permission Denied: Senior officer rank required for this action.", "danger");
        throw new Error("Forbidden");
    }
    return r.json();
}

async function get(ep)         { const r=await fetch(API+'/api'+ep, {headers: getAuthHeaders()}); return handleResponse(r); }
async function post(ep,data)   { const r=await fetch(API+'/api'+ep,{method:'POST',headers:getAuthHeaders({'Content-Type':'application/json'}),body:JSON.stringify(data)}); return handleResponse(r); }
async function postForm(ep,fd) { const r=await fetch(API+'/api'+ep,{method:'POST',headers:getAuthHeaders(),body:fd}); return handleResponse(r); }
function statusBadge(s){
    const m={
        'Investigation':'badge-orange','Trial':'badge-blue','Closed':'badge-green','Acquitted':'badge-gray',
        'Collected':'badge-blue','In Storage':'badge-gray','In Lab':'badge-purple',
        'In Court':'badge-orange','Returned':'badge-green','Archived':'badge-gray',
        'Compromised':'badge-red','Expired':'badge-red',
        'Completed':'badge-green','In Progress':'badge-blue','Pending':'badge-orange','Overdue':'badge-red',
        'Critical':'badge-red','High':'badge-orange','Medium':'badge-blue','Low':'badge-gray',
        'Open':'badge-red','Resolved':'badge-green','Under Investigation':'badge-orange'
    };
    return `<span class="badge ${m[s]||'badge-gray'}">${s||'—'}</span>`;
}

function fmtDate(d){
    if(!d) return '—';
    return new Date(d).toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'});
}
function fmtDT(d){
    if(!d) return '—';
    return new Date(d).toLocaleString('en-IN',{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'});
}

function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

function toast(msg,type='info'){
    const t=document.createElement('div');
    t.className=`alert-box ${type}`;
    t.style.cssText='position:fixed;bottom:24px;right:24px;z-index:9999;max-width:380px;box-shadow:0 4px 20px rgba(0,0,0,.5)';
    const icons={success:'✓',danger:'✕',warning:'⚠',info:'ℹ'};
    t.innerHTML=`<span style="font-size:16px">${icons[type]||'ℹ'}</span><div>${msg}</div>`;
    document.body.appendChild(t);
    setTimeout(()=>t.remove(),3500);
}

function populateSelect(id,items,vk,lk,ph='Select...'){
    const s=document.getElementById(id);
    if(!s) return;
    s.innerHTML=`<option value="">${ph}</option>`;
    if (Array.isArray(items)) {
        items.forEach(i=>{ const o=document.createElement('option'); o.value=i[vk]; o.textContent=i[lk]; s.appendChild(o); });
    }
}

function searchTable(inputId,tableId){
    const inp=document.getElementById(inputId);
    if(!inp) return;
    inp.addEventListener('input',()=>{
        const t=inp.value.toLowerCase();
        document.querySelectorAll(`#${tableId} tbody tr`).forEach(r=>{
            r.style.display=r.textContent.toLowerCase().includes(t)?'':'none';
        });
    });
}

function setActiveNav(){
    const page=window.location.pathname.split('/').pop()||'index.html';
    document.querySelectorAll('.nav-item').forEach(item=>{
        const href=item.getAttribute('href')||'';
        if(href===page||(page===''&&href==='index.html')) item.classList.add('active');
    });
}

async function loadAlertCount(){
    try{
        const a=await get('/alerts');
        const n=a.filter(x=>!x.is_acknowledged).length;
        const b=document.getElementById('alertBadge');
        if(b){ b.textContent=n; b.style.display=n>0?'inline':'none'; }
    }catch(e){}
}

// Lightbox for media
function openLightbox(url, isVideo, caption){
    let lb=document.getElementById('globalLightbox');
    if(!lb){
        lb=document.createElement('div');
        lb.id='globalLightbox';
        lb.className='lightbox';
        lb.innerHTML=`<button class="lightbox-close" onclick="closeLightbox()">×</button>
            <div id="lbMedia"></div>
            <div class="lightbox-caption" id="lbCaption"></div>`;
        lb.addEventListener('click', e=>{ if(e.target===lb) closeLightbox(); });
        document.body.appendChild(lb);
    }
    const media=document.getElementById('lbMedia');
    if(isVideo){
        media.innerHTML=`<video controls autoplay><source src="${url}"><p style="color:white">Video: ${url}</p></video>`;
    } else {
        media.innerHTML=`<img src="${url}" alt="${caption||''}" onerror="this.src='http://127.0.0.1:5000/uploads/placeholder.png'">`;
    }
    document.getElementById('lbCaption').textContent=caption||'';
    lb.classList.add('open');
}
function closeLightbox(){
    const lb=document.getElementById('globalLightbox');
    if(lb){ lb.classList.remove('open'); document.getElementById('lbMedia').innerHTML=''; }
}
document.addEventListener('keydown', e=>{ if(e.key==='Escape') closeLightbox(); });

// Sidebar HTML
const SIDEBAR_HTML=`
<div class="sidebar">
    <div class="sidebar-logo">
        <div class="logo-top">DBMS Project</div>
        <div class="logo-main">Forensic Evidence<br>Chain of Custody</div>
    </div>
    <nav class="sidebar-nav">
        <div class="nav-section">Main</div>
        <a class="nav-item" href="index.html"><span class="icon">⬛</span> Dashboard</a>
        <a class="nav-item" href="ai_assistant.html"><span class="icon">🤖</span> Forensic AI Assistant</a>
        <a class="nav-item" href="map.html"><span class="icon">🗺</span> Forensic Map</a>
        <div class="nav-section">Case Management</div>
        <a class="nav-item" href="cases.html"><span class="icon">📁</span> Cases</a>
        <a class="nav-item" href="evidence.html"><span class="icon">🔬</span> Evidence</a>
        <a class="nav-item" href="custody.html"><span class="icon">🔗</span> Custody Log</a>
        <div class="nav-section">Forensic</div>
        <a class="nav-item" href="forensic.html"><span class="icon">🧪</span> Forensic Lab</a>
        <a class="nav-item" href="storage.html"><span class="icon">🏛</span> Storage</a>
        <a class="nav-item" href="court.html"><span class="icon">⚖</span> Court</a>
        <div class="nav-section">Integrity</div>
        <a class="nav-item" href="tamper.html"><span class="icon">⚠</span> Tamper Incidents</a>
        <a class="nav-item" href="alerts.html"><span class="icon">🔔</span> Alerts <span class="nav-badge" id="alertBadge" style="display:none">0</span></a>
        <div class="nav-section">Admin</div>
        <a class="nav-item" href="officers.html"><span class="icon">👮</span> Officers</a>
        <a class="nav-item" href="#" onclick="logout()"><span class="icon">🚪</span> Logout</a>
    </nav>
</div>`;

function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('officer');
    window.location.href = 'login.html';
}

document.addEventListener('DOMContentLoaded',()=>{
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
    
    setActiveNav();
    loadAlertCount();
});
