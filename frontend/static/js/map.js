let map;
let markers = [];
let trailLayer = null;
let currentTrailMarkers = [];

async function initMap() {
    // Initialize map centered between Pune and Mumbai
    map = L.map('map').setView([18.8, 73.3], 9);

    // Add Dark Mode Tiles (Stadia Maps Alidade Smooth Dark — free, no API key required)
    L.tileLayer('https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
        maxZoom: 20
    }).addTo(map);

    await loadInitialData();
}

async function loadInitialData() {
    // Load map marker locations (independent — failure won't block dropdown)
    try {
        const locations = await get('/map/locations');
        renderMarkers(locations);
    } catch (e) {
        console.error("Failed to load map locations:", e);
        toast("Could not load map markers", "warning");
    }

    // Load evidence list for the trail dropdown (independent)
    try {
        const evList = await get('/evidence');
        populateSelect('evidenceSelect', evList, 'evidence_id', 'description', 'Select Evidence to Track...');
    } catch (e) {
        console.error("Failed to load evidence list:", e);
        toast("Could not load evidence list", "warning");
    }
}

function renderMarkers(data) {
    // Clear existing fixed markers if any
    // stations, labs, courts, storage, scenes
    
    const iconColors = {
        'PoliceStation': '#2E5FA3', // Blue
        'ForensicLab': '#5B2C8D',   // Purple
        'Court': '#e67e22',         // Orange
        'StorageFacility': '#27ae60', // Green
        'CrimeScene': '#C0392B'      // Red
    };

    const categories = ['stations', 'labs', 'courts', 'storage', 'scenes'];
    
    categories.forEach(cat => {
        if (!data[cat]) return;
        data[cat].forEach(loc => {
            const marker = L.circleMarker([loc.latitude, loc.longitude], {
                radius: 8,
                fillColor: iconColors[loc.type] || '#7eb8f7',
                color: "#fff",
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }).addTo(map);

            marker.bindPopup(`
                <div style="font-family: Inter, sans-serif;">
                    <b style="color: var(--accent);">${loc.type.replace(/([A-Z])/g, ' $1').trim()}</b><br>
                    <span style="font-size: 14px; font-weight: 600;">${loc.name}</span><br>
                    <span style="font-size: 12px; color: #aaa;">${loc.address}</span>
                </div>
            `);
        });
    });
}

async function loadEvidenceTrail(eid) {
    if (!eid) {
        clearTrail();
        return;
    }

    try {
        const trail = await get(`/map/evidence-trail/${eid}`);
        renderTrail(trail);
    } catch (e) {
        toast("Failed to load evidence trail", "danger");
    }
}

function renderTrail(trail) {
    clearTrail();
    if (!trail || trail.length === 0) {
        document.getElementById('trailList').innerHTML = '<div class="empty">No trail data found for this evidence.</div>';
        return;
    }

    const trailList = document.getElementById('trailList');
    trailList.innerHTML = '';

    const pathCoords = [];

    trail.forEach((step, index) => {
        pathCoords.push([step.latitude, step.longitude]);

        // Add to Sidebar
        const div = document.createElement('div');
        div.className = 'trail-step';
        div.innerHTML = `
            <div class="step-title">${step.location_type}: ${step.address}</div>
            <div class="step-meta">${fmtDT(step.timestamp)}</div>
        `;
        div.onclick = () => map.flyTo([step.latitude, step.longitude], 13);
        trailList.appendChild(div);

        // Add specialized marker for trail
        const marker = L.marker([step.latitude, step.longitude], {
            icon: L.divIcon({
                className: 'custom-div-icon',
                html: `<div style="background-color: var(--accent); width: 12px; height: 12px; border: 2px solid white; border-radius: 50%;"></div>`,
                iconSize: [12, 12],
                iconAnchor: [6, 6]
            })
        }).addTo(map);
        
        marker.bindPopup(`<b>Step ${index + 1}: ${step.location_type}</b><br>${step.address}`);
        currentTrailMarkers.push(marker);
    });

    // Draw Polyline
    trailLayer = L.polyline(pathCoords, {
        color: 'var(--accent)',
        weight: 3,
        opacity: 0.8,
        dashArray: '10, 10',
        lineJoin: 'round'
    }).addTo(map);

    // Zoom to fit trail
    if (pathCoords.length > 0) {
        map.fitBounds(trailLayer.getBounds(), { padding: [50, 50] });
    }
}

function clearTrail() {
    if (trailLayer) map.removeLayer(trailLayer);
    currentTrailMarkers.forEach(m => map.removeLayer(m));
    currentTrailMarkers = [];
    document.getElementById('trailList').innerHTML = '';
}

document.addEventListener('DOMContentLoaded', initMap);
