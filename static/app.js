// ============================================================
// PaySense AI — Frontend Application
// ============================================================

// Chart.js dark theme defaults
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = '#1e1e2e';
Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";

// State
let charts = { trends: null, failure: null, revenue: null, risk: null };

// ============================================================
// Initialization
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    loadDashboardData();
    setupEventListeners();
    setInterval(loadDashboardData, 30000); // Auto-refresh every 30s
});

// ============================================================
// API Helper — calls real backend endpoints
// ============================================================
async function api(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (body) options.body = JSON.stringify(body);

    try {
        const res = await fetch(endpoint, options);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (error) {
        console.error(`API error [${endpoint}]:`, error);
        return null;
    }
}

// ============================================================
// Dashboard Data Loading
// ============================================================
async function loadDashboardData() {
    try {
        const [overview, trends, failures, revenue, risk, decisions] = await Promise.all([
            api('/api/dashboard/overview'),
            api('/api/dashboard/trends'),
            api('/api/dashboard/failures'),
            api('/api/dashboard/revenue'),
            api('/api/dashboard/risk'),
            api('/api/agent/decisions')
        ]);

        if (overview) updateMetricCards(overview);
        if (trends) renderTrendsChart(trends);
        if (failures) renderFailureChart(failures);
        if (revenue) renderRevenueChart(revenue);
        if (risk) renderRiskChart(risk);
        if (decisions) updateDecisionLog(decisions);
        updateAlerts(overview);
    } catch (error) {
        console.error("Dashboard load error:", error);
    }
}

// ============================================================
// Metric Cards
// ============================================================
function updateMetricCards(data) {
    const rev = data?.revenue || {};
    const fail = data?.failures || {};

    const collected = rev.collected_paise || 0;
    const lost = rev.lost_paise || 0;
    const total = fail.total || 0;
    const successRate = fail.success_rate || 0;
    const healthScore = Math.min(100, Math.max(0, Math.round(successRate * 0.7 + 30)));

    document.getElementById('metric-revenue').textContent = formatCurrency(collected);
    document.getElementById('metric-success').textContent = `${successRate.toFixed(1)}%`;
    document.getElementById('metric-lost').textContent = formatCurrency(lost);
    document.getElementById('metric-health').textContent = healthScore;

    const healthEl = document.getElementById('metric-health');
    if (healthScore > 85) healthEl.style.color = 'var(--success)';
    else if (healthScore > 60) healthEl.style.color = 'var(--warning)';
    else healthEl.style.color = 'var(--danger)';
}

// ============================================================
// Chart Renderers
// ============================================================
function initializeCharts() {
    charts.trends = new Chart(document.getElementById('trendsChart').getContext('2d'), {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: { responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false },
            scales: { y: { beginAtZero: true, grid: { color: '#1e1e2e' } }, x: { grid: { display: false } } } }
    });

    charts.failure = new Chart(document.getElementById('failureChart').getContext('2d'), {
        type: 'doughnut',
        data: { labels: [], datasets: [] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '65%', plugins: { legend: { position: 'right', labels: { padding: 12 } } } }
    });

    charts.revenue = new Chart(document.getElementById('revenueChart').getContext('2d'), {
        type: 'bar',
        data: { labels: [], datasets: [] },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, grid: { color: '#1e1e2e' } }, x: { grid: { display: false } } } }
    });

    charts.risk = new Chart(document.getElementById('riskChart').getContext('2d'), {
        type: 'doughnut',
        data: { labels: [], datasets: [] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '65%', plugins: { legend: { position: 'right', labels: { padding: 12 } } } }
    });
}

function renderTrendsChart(data) {
    const failData = data?.failures || [];
    const revData = data?.revenue || [];

    // Merge dates from both sources
    const dateMap = {};
    failData.forEach(d => { dateMap[d.date] = { ...(dateMap[d.date] || {}), paid: d.paid || 0, failed: d.failed || 0 }; });
    revData.forEach(d => { dateMap[d.date] = { ...(dateMap[d.date] || {}), collected: d.collected || 0 }; });

    const dates = Object.keys(dateMap).sort();
    const paidCounts = dates.map(d => dateMap[d].paid || 0);
    const failedCounts = dates.map(d => dateMap[d].failed || 0);

    charts.trends.data = {
        labels: dates.map(d => d.slice(5)), // MM-DD format
        datasets: [
            { label: 'Paid', data: paidCounts, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', tension: 0.4, fill: true, pointRadius: 2 },
            { label: 'Failed', data: failedCounts, borderColor: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', tension: 0.4, fill: true, pointRadius: 2 }
        ]
    };
    charts.trends.update();
}

function renderFailureChart(data) {
    const reasons = data?.by_reason || [];
    if (reasons.length === 0) return;

    const colors = ['#ef4444', '#f59e0b', '#3b82f6', '#8b5cf6', '#64748b', '#ec4899'];
    charts.failure.data = {
        labels: reasons.map(r => (r.reason || 'unknown').replace(/_/g, ' ')),
        datasets: [{ data: reasons.map(r => r.count), backgroundColor: colors.slice(0, reasons.length), borderWidth: 0 }]
    };
    charts.failure.update();
}

function renderRevenueChart(data) {
    const methods = data?.by_method || [];
    if (methods.length === 0) return;

    charts.revenue.data = {
        labels: methods.map(m => (m.method || 'unknown').toUpperCase()),
        datasets: [{ label: 'Revenue (₹)', data: methods.map(m => Math.round((m.revenue || 0) / 100)), backgroundColor: '#4f46e5', borderRadius: 6, maxBarThickness: 50 }]
    };
    charts.revenue.update();
}

function renderRiskChart(data) {
    const dist = data?.distribution || {};
    const labels = ['Low', 'Medium', 'High'];
    const values = [dist.low || 0, dist.medium || 0, dist.high || 0];

    if (values.every(v => v === 0)) return;

    charts.risk.data = {
        labels,
        datasets: [{ data: values, backgroundColor: ['#10b981', '#f59e0b', '#ef4444'], borderWidth: 0 }]
    };
    charts.risk.update();
}

// ============================================================
// Alerts & Decision Log
// ============================================================
function updateAlerts(overview) {
    const list = document.getElementById('alerts-list');
    list.innerHTML = '';

    const fail = overview?.failures || {};
    const rev = overview?.revenue || {};
    const alerts = [];

    if (fail.failure_rate > 20) alerts.push({ message: `🔴 Critical: Payment failure rate is ${fail.failure_rate.toFixed(1)}%`, severity: 'high' });
    else if (fail.failure_rate > 10) alerts.push({ message: `🟡 Warning: Failure rate elevated at ${fail.failure_rate.toFixed(1)}%`, severity: 'medium' });

    if (rev.lost_paise > 1000000) alerts.push({ message: `🔴 Revenue leak: ₹${(rev.lost_paise / 100).toLocaleString('en-IN')} lost to failures`, severity: 'high' });

    if (fail.total > 0 && fail.success_rate > 85) alerts.push({ message: `🟢 Payment health is good (${fail.success_rate.toFixed(1)}% success)`, severity: 'low' });

    if (alerts.length === 0) alerts.push({ message: '🟢 No data yet — click "Simulate Payments" to generate demo data', severity: 'low' });

    alerts.forEach(alert => {
        const el = document.createElement('div');
        el.className = `alert-item severity-${alert.severity}`;
        el.textContent = alert.message;
        list.appendChild(el);
    });
}

function updateDecisionLog(decisions) {
    const tbody = document.getElementById('decisions-body');
    tbody.innerHTML = '';

    if (!decisions || decisions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text-muted)">No agent decisions yet</td></tr>';
        return;
    }

    decisions.slice(0, 10).forEach(d => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${formatDate(d.created_at)}</td>
            <td>${d.action_taken || d.decision_type || '-'}</td>
            <td>${truncate(d.result || d.reasoning || '-', 40)}</td>
            <td><span class="status-badge">${d.decision_type || 'action'}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// ============================================================
// Chat Functionality
// ============================================================
function setupEventListeners() {
    document.getElementById('chat-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('chat-input');
        const msg = input.value.trim();
        if (!msg) return;
        input.value = '';
        await handleUserMessage(msg);
    });

    document.getElementById('simulate-btn').addEventListener('click', simulatePayments);
}

async function handleUserMessage(message) {
    addChatMessage('user', message);
    showTypingIndicator();

    try {
        const result = await api('/api/agent/chat', 'POST', { message });
        hideTypingIndicator();

        if (result) {
            addChatMessage('agent', formatAgentResponse(result.response), result.tools_used || []);
        } else {
            addChatMessage('agent', 'Sorry, I encountered an error. Please check that your GEMINI_API_KEY is set in the .env file.');
        }
        loadDashboardData(); // Refresh — agent may have taken actions
    } catch (error) {
        hideTypingIndicator();
        addChatMessage('agent', 'Connection error. Is the server running?');
    }
}

async function runHealthScan() {
    addChatMessage('user', '🔍 Run Health Scan');
    showTypingIndicator();

    try {
        const result = await api('/api/agent/scan', 'POST');
        hideTypingIndicator();
        if (result) {
            addChatMessage('agent', formatAgentResponse(result.response), result.tools_used || []);
        } else {
            addChatMessage('agent', 'Scan failed. Check your API key configuration.');
        }
        loadDashboardData();
    } catch (e) {
        hideTypingIndicator();
        addChatMessage('agent', 'Error running health scan.');
    }
}

function sendQuickMessage(msg) {
    handleUserMessage(msg);
}

function formatAgentResponse(text) {
    if (!text) return 'No response generated.';
    // Basic markdown-like formatting
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
}

function addChatMessage(role, content, toolsUsed = []) {
    const chat = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;

    let toolsHtml = '';
    if (toolsUsed && toolsUsed.length > 0) {
        toolsHtml = '<div class="tool-pills">' +
            toolsUsed.map(t => `<span class="tool-pill">🔧 ${t.replace(/_/g, ' ')}</span>`).join('') +
            '</div>';
    }

    msgDiv.innerHTML = `<div class="message-content">${content}</div>${toolsHtml}`;
    chat.appendChild(msgDiv);
    chat.scrollTop = chat.scrollHeight;
}

let typingIndicator = null;
function showTypingIndicator() {
    const chat = document.getElementById('chat-messages');
    typingIndicator = document.createElement('div');
    typingIndicator.className = 'message agent';
    typingIndicator.innerHTML = `
        <div class="message-content typing">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            <span style="margin-left:8px;color:var(--text-muted)">Analyzing payments...</span>
        </div>`;
    chat.appendChild(typingIndicator);
    chat.scrollTop = chat.scrollHeight;
}

function hideTypingIndicator() {
    if (typingIndicator && typingIndicator.parentNode) {
        typingIndicator.parentNode.removeChild(typingIndicator);
        typingIndicator = null;
    }
}

// ============================================================
// Simulate Payments
// ============================================================
async function simulatePayments() {
    const btn = document.getElementById('simulate-btn');
    btn.textContent = '⏳ Generating...';
    btn.disabled = true;

    try {
        const result = await api('/api/payments/simulate', 'POST', { count: 200 });
        if (result && result.status === 'success') {
            showToast(result.message || 'Generated 200 payments', 'success');
            await loadDashboardData();
        } else {
            showToast('Simulation failed: ' + (result?.message || 'Unknown error'), 'error');
        }
    } catch (error) {
        showToast('Simulation failed', 'error');
    } finally {
        btn.textContent = '⚡ Simulate Payments';
        btn.disabled = false;
    }
}

// ============================================================
// Utilities
// ============================================================
function formatCurrency(paise) {
    if (!paise) return '₹0';
    const rupees = paise / 100;
    if (rupees >= 10000000) return `₹${(rupees / 10000000).toFixed(1)}Cr`;
    if (rupees >= 100000) return `₹${(rupees / 100000).toFixed(1)}L`;
    if (rupees >= 1000) return `₹${(rupees / 1000).toFixed(1)}K`;
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(rupees);
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
        return date.toLocaleString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch { return dateStr; }
}

function truncate(str, len) {
    if (!str) return '-';
    return str.length > len ? str.slice(0, len) + '...' : str;
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️'
    };

    toast.innerHTML = `<span>${icons[type] || ''} ${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
        toast.style.transition = 'all 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
