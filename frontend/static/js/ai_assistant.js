// frontend/static/js/ai_assistant.js
// Frontend logic for Forensic AI Assistant interface.
// Handles RAG query dispatch, method selection, answer rendering,
// source chips, conflict warnings, and tiered Why? modal view.

let currentQueryId = null;

document.addEventListener('DOMContentLoaded', () => {
    loadSuggestedQueries();

    const input = document.getElementById('aiQueryInput');
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendQuery();
        });
    }
});

async function loadSuggestedQueries() {
    try {
        const queries = await get('/ai/suggested-queries');
        const container = document.getElementById('suggestedPills');
        if (!container || !Array.isArray(queries)) return;

        container.innerHTML = queries.map(q => `
            <div class="suggested-pill" onclick="askSuggested('${q.replace(/'/g, "\\'")}')">
                🔍 "${q}"
            </div>
        `).join('');
    } catch (e) {
        console.error("Failed to load suggested queries:", e);
    }
}

function askSuggested(text) {
    const input = document.getElementById('aiQueryInput');
    if (input) {
        input.value = text;
        sendQuery();
    }
}

async function sendQuery() {
    const input = document.getElementById('aiQueryInput');
    const question = input.value.trim();
    if (!question) return;

    const method = document.getElementById('retrievalMethodSelect').value || 'HYBRID';

    // Append user message bubble
    appendMessage('user', question);
    input.value = '';

    // Show loading state
    const loadingId = appendLoadingBubble();

    try {
        const token = localStorage.getItem('auth_token');
        if (!token) {
            removeBubble(loadingId);
            appendMessage('ai', `<div class="alert-box danger">❌ Not authenticated. Please <a href="login.html">log in</a> first.</div>`);
            return;
        }

        const response = await fetch(`/api/ai/query?method=${method}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ question: question })
        });

        removeBubble(loadingId);

        if (!response.ok) {
            let errMsg = `HTTP ${response.status}`;
            try {
                const errData = await response.json();
                errMsg = errData.error || errMsg;
            } catch (_) {}
            if (response.status === 401) {
                appendMessage('ai', `<div class="alert-box danger">❌ Unauthorized (401): Session expired. Please <a href="login.html">log in again</a>.</div>`);
            } else if (response.status === 403) {
                appendMessage('ai', `<div class="alert-box danger">❌ Forbidden (403): ${errMsg}</div>`);
            } else if (response.status === 404) {
                appendMessage('ai', `<div class="alert-box danger">❌ Not Found (404): ${errMsg}</div>`);
            } else {
                appendMessage('ai', `<div class="alert-box danger">❌ Error ${response.status}: ${errMsg}</div>`);
            }
            return;
        }

        const res = await response.json();
        currentQueryId = res.query_id;
        appendAIMessage(res);
    } catch (err) {
        removeBubble(loadingId);
        appendMessage('ai', `<div class="alert-box danger">❌ Query failed: ${err.message || 'Network error'}</div>`);
    }
}

function appendMessage(role, content) {
    const messages = document.getElementById('chatMessages');
    if (!messages) return;

    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role}`;
    bubble.innerHTML = content;
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
}

function appendLoadingBubble() {
    const id = 'loading_' + Date.now();
    const messages = document.getElementById('chatMessages');
    if (!messages) return id;

    const bubble = document.createElement('div');
    bubble.id = id;
    bubble.className = 'chat-bubble ai';
    bubble.innerHTML = `<div class="loading">🔍 Retrieving verified records & analyzing context...</div>`;
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
    return id;
}

function removeBubble(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function appendAIMessage(data) {
    const messages = document.getElementById('chatMessages');
    if (!messages) return;

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble ai';

    let html = '';

    // Conflict Warning Banner
    if (data.conflict_warning) {
        html += `
            <div class="conflict-banner">
                <span>⚠</span>
                <div><strong>Source Conflict Flagged</strong><br>${data.conflict_warning}</div>
            </div>
        `;
    }

    // Answer Content
    html += `<div class="ai-answer-content">${formatAnswerText(data.answer)}</div>`;

    // Metadata Bar (Latency + Method)
    html += `
        <div style="font-family:var(--mono);font-size:10px;color:var(--text3);margin-bottom:8px">
            Method: <span style="color:var(--accent)">${data.retrieval_method || 'HYBRID'}</span> | 
            Total Latency: ${data.response_latency_ms || 0}ms (Retrieval: ${data.retrieval_latency_ms || 0}ms)
        </div>
    `;

    // Sources and Why Button
    const sources = data.sources || [];
    html += `<div class="sources-container">`;
    html += `<span class="source-label">Sources:</span>`;

    if (sources.length === 0) {
        html += `<span style="font-size:11px;color:var(--text3)">None cited</span>`;
    } else {
        sources.forEach(s => {
            html += `<span class="source-chip" onclick="navigateToSource('${s.type}', '${s.id}')">📎 ${s.type} ${s.id}</span>`;
        });
    }

    if (data.query_id) {
        html += `<button class="btn-why" onclick="openWhyModal('${data.query_id}')">❓ Why?</button>`;
    }

    html += `</div>`;

    bubble.innerHTML = html;
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
}

function formatAnswerText(text) {
    if (!text) return '';
    // Format citations and bullet points cleanly
    let formatted = text.replace(/•/g, '<br>• ');
    return formatted;
}

function navigateToSource(type, id) {
    if (type === 'Evidence') {
        const num = id.replace('E', '');
        window.location.href = `evidence.html?id=${parseInt(num)}`;
    } else if (type === 'Case') {
        window.location.href = `cases.html?fir=${encodeURIComponent(id)}`;
    } else {
        toast(`Source record: ${type} ${id}`, 'info');
    }
}

/**
 * Safely converts provenance_sources to an array.
 * Handles: already an array, a JSON-encoded string, null/undefined.
 */
function toArray(val) {
    if (Array.isArray(val)) return val;
    if (typeof val === 'string' && val.trim().startsWith('[')) {
        try { return JSON.parse(val); } catch (_) {}
    }
    return [];
}

async function openWhyModal(queryId) {
    try {
        const data = await get(`/ai/query/${queryId}/why`);
        const modal = document.getElementById('whyModal');
        const body = document.getElementById('whyModalBody');

        if (!modal || !body) return;

        let html = '';

        if (data.mode === 'admin') {
            const exp = data.explanation || {};
            html += `
                <div class="alert-box info mb-16">
                    <div><strong>Developer / Admin Explanation Mode</strong><br>Exposing technical SQL records, vector scores, and latency metrics.</div>
                </div>
                <div style="font-family:var(--mono);font-size:12px;margin-bottom:12px">
                    <strong>Query ID:</strong> ${queryId}<br>
                    <strong>Retrieval Method:</strong> ${exp.retrieval_method || 'HYBRID'}<br>
                    <strong>Model Used:</strong> ${exp.model_used || 'unknown'}<br>
                    <strong>Latency:</strong> ${exp.response_latency_ms || 0}ms
                </div>
                <div style="font-weight:600;margin:12px 0 6px;color:var(--accent)">Verified Facts Cited:</div>
                <pre style="background:var(--bg3);padding:10px;border-radius:4px;font-family:var(--mono);font-size:11px;overflow-x:auto">${JSON.stringify(exp.verified_facts || [], null, 2)}</pre>
                <div style="font-weight:600;margin:12px 0 6px;color:var(--accent)">Raw Structured SQL Data:</div>
                <pre style="background:var(--bg3);padding:10px;border-radius:4px;font-family:var(--mono);font-size:11px;overflow-x:auto">${JSON.stringify(exp.raw_sql_data || {}, null, 2)}</pre>
                <div style="font-weight:600;margin:12px 0 6px;color:var(--accent)">Raw Vector Chunks:</div>
                <pre style="background:var(--bg3);padding:10px;border-radius:4px;font-family:var(--mono);font-size:11px;overflow-x:auto">${JSON.stringify(exp.raw_vector_chunks || [], null, 2)}</pre>
            `;
        } else {
            const exp = data.explanation || {};
            const provSources = toArray(exp.provenance_sources);
            html += `
                <div style="margin-bottom:16px">${exp.summary || 'Answer derived from verified database records.'}</div>
                <div style="font-weight:600;margin-bottom:8px;color:var(--accent)">Verified Sources Cited:</div>
                <ul>
                    ${provSources.length > 0
                        ? provSources.map(s => `<li>${s.type} record ID: <strong>${s.id}</strong></li>`).join('')
                        : '<li>None</li>'}
                </ul>
                <div style="font-weight:600;margin:16px 0 8px;color:var(--accent)">Conflict Status:</div>
                <div>${exp.conflict_details || 'No source conflicts.'}</div>
            `;
        }

        body.innerHTML = html;
        openModal('whyModal');
    } catch (err) {
        toast('Failed to load explanation: ' + err.message, 'danger');
    }
}
