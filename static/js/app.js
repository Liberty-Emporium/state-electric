// State Electric & Lighting - Frontend App
const API = '/api';
let token = localStorage.getItem('token') || null;
let currentUser = null;

const NAV = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊', perm: 'all' },
    { id: 'customers', label: 'Customers', icon: '👥', perm: 'all' },
    { id: 'vendors', label: 'Vendors', icon: '🏢', perm: 'office' },
    { id: 'invoices', label: 'Invoices', icon: '📄', perm: 'office' },
    { id: 'work-orders', label: 'Work Orders', icon: '🔧', perm: 'all' },
    { id: 'documents', label: 'Documents', icon: '📁', perm: 'all' },
    { id: 'upload', label: 'Upload', icon: '⬆️', perm: 'office' },
    { id: 'timeclock', label: 'Time Clock', icon: '⏰', perm: 'employee' },
    { id: 'payroll', label: 'Payroll', icon: '💰', perm: 'office' },
    { id: 'reports', label: 'Reports', icon: '📈', perm: 'office' },
];

async function api(path, opts = {}) {
    const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    if (token) headers['Authorization'] = 'Bearer ' + token;
    const res = await fetch(API + path, { ...opts, headers });
    if (res.status === 401) { doLogout(); return null; }
    if (!res.ok) {
        const text = await res.text();
        console.error(`API Error ${res.status}: ${path}`, text);
        return null;
    }
    return res.json();
}

async function doLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const res = await fetch(API + '/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (res.ok && data.access) {
        token = data.access;
        localStorage.setItem('token', token);
        currentUser = data.user;
        showApp();
    } else {
        document.getElementById('login-error').textContent = data?.detail || 'Invalid credentials';
    }
}

function doLogout() {
    token = null;
    currentUser = null;
    localStorage.removeItem('token');
    document.getElementById('login-screen').classList.add('active');
    document.getElementById('app-screen').classList.remove('active');
}

function showApp() {
    document.getElementById('login-screen').classList.remove('active');
    document.getElementById('app-screen').classList.add('active');
    renderNav();
    if (currentUser) {
        document.getElementById('nav-user').innerHTML =
            `<strong>${currentUser.first_name || currentUser.username}</strong><br>${currentUser.role || ''}`;
    }
    navigate('dashboard');
}

function renderNav() {
    const navItems = document.getElementById('nav-items');
    const bottomNav = document.getElementById('bottom-nav') || createBottomNav();
    navItems.innerHTML = '';
    bottomNav.innerHTML = '';
    const role = currentUser?.role || 'employee';
    NAV.forEach(item => {
        if (item.perm !== 'all' && (item.perm === 'office' && role === 'employee')) return;
        const btn = document.createElement('button');
        btn.className = 'nav-item' + (item.id === 'dashboard' ? ' active' : '');
        btn.innerHTML = `<span class="icon">${item.icon}</span> ${item.label}`;
        btn.onclick = () => navigate(item.id);
        btn.dataset.id = item.id;
        navItems.appendChild(btn);
        const bbtn = document.createElement('button');
        bbtn.className = 'nav-item' + (item.id === 'dashboard' ? ' active' : '');
        bbtn.innerHTML = `<span class="icon">${item.icon}</span> ${item.label.split(' ')[0]}`;
        bbtn.onclick = () => navigate(item.id);
        bbtn.dataset.id = item.id;
        bottomNav.appendChild(bbtn);
    });
}

function createBottomNav() {
    const nav = document.createElement('nav');
    nav.id = 'bottom-nav';
    nav.className = 'bottom-nav';
    document.getElementById('app-screen').appendChild(nav);
    return nav;
}

function navigate(page) {
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.toggle('active', el.dataset.id === page);
    });
    const content = document.getElementById('main-content');
    switch(page) {
        case 'dashboard': renderDashboard(content); break;
        case 'customers': renderCustomers(content); break;
        case 'vendors': renderVendors(content); break;
        case 'invoices': renderInvoices(content); break;
        case 'work-orders': renderWorkOrders(content); break;
        case 'documents': renderDocuments(content); break;
        case 'upload': renderUpload(content); break;
        case 'timeclock': renderTimeclock(content); break;
        case 'payroll': renderPayroll(content); break;
        case 'reports': renderReports(content); break;
        default: content.innerHTML = '<div class="page-header"><h2>Page not found</h2></div>';
    }
}

async function renderDashboard(content) {
    content.innerHTML = `<div class="page-header"><h2>📊 Dashboard</h2><p>Welcome back, ${currentUser?.first_name || 'User'}</p></div><div class="loading">Loading dashboard...</div>`;

    const [summary, financials, topCust, activity] = await Promise.all([
        api('/reports/dashboard/'),
        api('/reports/dashboard/financials/'),
        api('/reports/dashboard/top-customers/'),
        api('/reports/dashboard/recent-activity/'),
    ]);

    if (!summary) { content.innerHTML = '<div class="page-header"><h2>📊 Dashboard</h2><p style="color:var(--danger)">Failed to load</p></div>'; return; }

    const kpiCustomers = summary?.active_customers || 0;
    const kpiVendors = summary?.total_vendors || 0;
    const kpiEmployees = summary?.total_employees || 0;
    const kpiOutstanding = parseFloat(summary?.outstanding_balance || 0);

    content.innerHTML = `
        <div class="page-header"><h2>📊 Dashboard</h2><p>Welcome back, ${currentUser?.first_name || 'User'}</p></div>
        <div class="grid">
            <div class="card"><div class="card-title">Active Customers</div><div class="card-value">${kpiCustomers}</div><div class="card-sub">Total in QB: ${summary?.total_customers_qb || 0}</div></div>
            <div class="card"><div class="card-title">Total Vendors</div><div class="card-value">${kpiVendors}</div><div class="card-sub">Suppliers & Contractors</div></div>
            <div class="card"><div class="card-title">Employees</div><div class="card-value">${kpiEmployees}</div><div class="card-sub">W-2 Staff</div></div>
            <div class="card"><div class="card-title">Outstanding</div><div class="card-value" style="color:var(--danger)">$${kpiOutstanding.toLocaleString()}</div><div class="card-sub">Unpaid Invoices</div></div>
        </div>
        <div class="ai-chat">
            <h3>🤖 Ask About Your Business</h3>
            <div class="ai-input">
                <input type="text" id="ai-q" placeholder="e.g., How many customers do I have?" onkeypress="if(event.key==='Enter')askAI()">
                <button class="btn btn-primary" onclick="askAI()">Ask</button>
            </div>
            <div class="ai-response" id="ai-res">Ask a question about your business data...</div>
            <div class="ai-suggestions">
                <button onclick="quickAsk('How many customers?')">Customers</button>
                <button onclick="quickAsk('Total income?')">Income</button>
                <button onclick="quickAsk('Top customers?')">Top Customers</button>
                <button onclick="quickAsk('Total expenses?')">Expenses</button>
                <button onclick="quickAsk('How many employees?')">Employees</button>
            </div>
        </div>
        <div class="grid">
            <div class="card"><div class="card-title">💰 Income vs Expenses</div>
                <div class="bar-chart">${renderBars(financials?.profit_loss?.income?.items || [], 'income') || '<p style="color:var(--text-muted)">No data yet</p>'}</div>
            </div>
            <div class="card"><div class="card-title">🏦 Balance Sheet</div>
                <div class="bar-chart">${renderBars(financials?.balance_sheet?.assets?.items || [], 'asset') || '<p style="color:var(--text-muted)">No data yet</p>'}</div>
            </div>
        </div>
        <div class="card"><div class="card-title">🏆 Top Customers</div>
            <div class="table-wrap"><table><thead><tr><th>Customer</th><th>Revenue</th></tr></thead>
            <tbody>${(topCust || []).map(c => `<tr><td>${c.customer}</td><td style="color:var(--success)">$${(c.total_revenue||0).toLocaleString()}</td></tr>`).join('') || '<tr><td colspan="2" style="color:var(--text-muted)">No data</td></tr>'}</tbody></table></div>
        </div>
        <div class="card"><div class="card-title">📋 Recent Activity</div>
            <div class="table-wrap"><table><thead><tr><th>Date</th><th>Type</th><th>Name</th><th>Amount</th></tr></thead>
            <tbody>${(activity || []).slice(0,15).map(r => `<tr><td>${r.date}</td><td>${r.type}</td><td>${r.name||r.account||''}</td><td>${r.debit>0?'<span style="color:var(--danger)">-$'+r.debit.toLocaleString()+'</span>':'<span style="color:var(--success)">+$'+r.credit.toLocaleString()+'</span>'}</td></tr>`).join('') || '<tr><td colspan="4" style="color:var(--text-muted)">No data</td></tr>'}</tbody></table></div>
        </div>
    `;
}

function renderBars(items, type) {
    if (!items || items.length === 0) return '';
    const max = Math.max(...items.map(i => Math.abs(i.amount)));
    return items.map(item => {
        const pct = max > 0 ? (Math.abs(item.amount) / max * 100) : 0;
        return `<div class="bar-row"><div class="bar-label">${item.label}</div><div class="bar-track"><div class="bar-fill ${type}" style="width:${pct}%"></div></div><div class="bar-value">$${(item.amount||0).toLocaleString()}</div></div>`;
    }).join('');
}

async function askAI() {
    const q = document.getElementById('ai-q').value;
    if (!q) return;
    document.getElementById('ai-res').textContent = 'Thinking...';
    const res = await api('/reports/dashboard/ask/?q=' + encodeURIComponent(q));
    if (res) {
        document.getElementById('ai-res').innerHTML = '<strong>Answer:</strong> ' + (res.answer || 'No response');
        if (res.data && Array.isArray(res.data) && res.data.length > 0) {
            document.getElementById('ai-res').innerHTML += '<br><br>' +
                res.data.map(d => `• ${d.customer}: <span style="color:var(--success)">$${(d.revenue||0).toLocaleString()}</span>`).join('<br>');
        }
    } else {
        document.getElementById('ai-res').textContent = 'Error getting response';
    }
}
function quickAsk(q) {
    document.getElementById('ai-q').value = q;
    askAI();
}

async function renderCustomers(content) {
    content.innerHTML = `<div class="page-header"><h2>👥 Customers</h2><p>Loading...</p></div>`;
    const customers = await api('/customers/');
    if (!customers) { content.innerHTML = '<div class="page-header"><h2>👥 Customers</h2><p style="color:var(--danger)">Failed to load</p></div>'; return; }
    content.innerHTML = `
        <div class="page-header"><h2>👥 Customers</h2><p>${customers.length} customers</p></div>
        <div class="search-bar"><input type="text" placeholder="Search customers..." oninput="filterTable(this,'.customer-row')"></div>
        <div class="table-wrap"><table>
            <thead><tr><th>Company</th><th>Contact</th><th>Phone</th><th>Email</th><th>Status</th></tr></thead>
            <tbody>${customers.map(c => `<tr class="customer-row"><td>${c.name||''}</td><td>${c.contact_name||''}</td><td>${c.phone||''}</td><td>${c.email||''}</td><td>${c.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-danger">Inactive</span>'}</td></tr>`).join('')}</tbody>
        </table></div>
    `;
}

async function renderVendors(content) {
    content.innerHTML = `<div class="page-header"><h2>🏢 Vendors</h2><p>Loading...</p></div>`;
    const vendors = await api('/vendors/');
    if (!vendors) { content.innerHTML = '<div class="page-header"><h2>🏢 Vendors</h2><p style="color:var(--danger)">Failed to load</p></div>'; return; }
    content.innerHTML = `
        <div class="page-header"><h2>🏢 Vendors</h2><p>${vendors.length} vendors</p></div>
        <div class="search-bar"><input type="text" placeholder="Search vendors..." oninput="filterTable(this,'.vendor-row')"></div>
        <div class="table-wrap"><table>
            <thead><tr><th>Company</th><th>Contact</th><th>Phone</th><th>Email</th></tr></thead>
            <tbody>${vendors.map(v => `<tr class="vendor-row"><td>${v.name||''}</td><td>${v.contact_name||''}</td><td>${v.phone||''}</td><td>${v.email||''}</td></tr>`).join('')}</tbody>
        </table></div>
    `;
}

async function renderInvoices(content) {
    content.innerHTML = `<div class="page-header"><h2>📄 Invoices</h2><p>Loading...</p></div>`;
    const resp = await api('/invoices/');
    if (!resp) { content.innerHTML = '<div class="page-header"><h2>📄 Invoices</h2><p style="color:var(--danger)">Failed to load</p></div>'; return; }
    const invoices = resp.results || resp;
    content.innerHTML = `
        <div class="page-header"><h2>📄 Invoices</h2><p>${invoices.length} invoices</p></div>
        <div class="table-wrap"><table><thead><tr><th>#</th><th>Customer</th><th>Total</th><th>Balance</th><th>Status</th><th>Date</th></tr></thead>
        <tbody>${invoices.slice(0,50).map(inv => `<tr><td>${inv.invoice_number||inv.id}</td><td>${inv.customer_name||inv.customer||''}</td><td>$${(inv.total||0).toLocaleString()}</td><td>$${(inv.balance_due||0).toLocaleString()}</td><td><span class="badge ${inv.status==='paid'?'badge-success':inv.status==='overdue'?'badge-danger':'badge-warning'}">${inv.status||'draft'}</span></td><td>${(inv.date_created||'').toString().slice(0,10)}</td></tr>`).join('') || '<tr><td colspan="6" style="color:var(--text-muted)">No invoices found</td></tr>'}</tbody></table></div>
    `;
}

async function renderWorkOrders(content) {
    content.innerHTML = `
        <div class="page-header"><h2>🔧 Work Orders</h2><p>View and manage work orders</p></div>
        <div class="card"><div class="card-title">QuickBooks Work Orders</div>
            <p style="color:var(--text-muted);margin-bottom:12px">Your OneDrive contains hundreds of scanned work orders and invoices.</p>
            <p style="color:var(--text-muted)">Total documents available: <strong style="color:var(--text)">9,125</strong> files including work order scans, invoices, permits, and bank deposit records.</p>
            <button class="btn btn-primary" onclick="navigate('documents')" style="margin-top:12px">View Documents</button>
        </div>`;
}

async function renderUpload(content) {
    content.innerHTML = `
        <div class="page-header"><h2>⬆️ Upload Documents</h2><p>Upload files to the document system</p></div>
        <div class="card">
            <h3 style="margin-bottom:16px">Upload Files</h3>
            <input type="file" id="fileInput" style="margin:12px 0">
            <div class="form-group"><label>Category</label>
                <select id="categoryInput">
                    <option value="invoice">Invoice</option>
                    <option value="work_order">Work Order</option>
                    <option value="estimate">Estimate</option>
                    <option value="scan">Scan</option>
                    <option value="permit">Permit</option>
                    <option value="insurance">Insurance</option>
                    <option value="receipt">Receipt</option>
                    <option value="other">Other</option>
                </select>
            </div>
            <div class="form-group"><label>Folder</label><input type="text" id="folderInput" placeholder="e.g. Invoices 2024"></div>
            <button class="btn btn-primary" onclick="uploadFile()">Upload</button>
            <div id="uploadResult" style="margin-top:12px"></div>
        </div>`;
}

async function uploadFile() {
    const file = document.getElementById('fileInput').files[0];
    if (!file) return alert('Select a file first');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', document.getElementById('categoryInput').value);
    formData.append('folder', document.getElementById('folderInput').value);
    
    const res = await fetch('/upload/api/upload/', {
        method: 'POST',
        body: formData,
        headers: { 'Authorization': 'Bearer ' + token }
    });
    const data = await res.json();
    
    const resultDiv = document.getElementById('uploadResult');
    if (data.success) {
        resultDiv.innerHTML = '<span style="color:var(--success)">✅ Uploaded: ' + data.title + '</span>';
        document.getElementById('fileInput').value = '';
    } else {
        resultDiv.innerHTML = '<span style="color:var(--danger)">❌ ' + (data.error || 'Upload failed') + '</span>';
    }
}

async function renderDocuments() {
    const content = document.getElementById('main-content') || document.getElementById('content');
    if (!content) return;
    content.innerHTML = `<div class="page-header"><h2>📁 Documents</h2><p>Loading...</p></div>`;
    try {
        const res = await api('/api/files/');
        const data = await res.json();
        const docs = data.results || [];
        const counts = {};
        docs.forEach(d => { counts[d.category] = (counts[d.category] || 0) + 1; });
        content.innerHTML = `
            <div class="page-header"><h2>📁 Documents</h2><p>${data.count} total files</p></div>
            <div class="grid">
                <div class="card"><div class="card-title">📄 Invoices</div><div class="card-value">${counts['invoice'] || 0}</div></div>
                <div class="card"><div class="card-title">🔧 Work Orders</div><div class="card-value">${counts['work_order'] || 0}</div></div>
                <div class="card"><div class="card-title">📝 Estimates</div><div class="card-value">${counts['estimate'] || 0}</div></div>
                <div class="card"><div class="card-title">🖼️ Scans</div><div class="card-value">${counts['scan'] || 0}</div></div>
                <div class="card"><div class="card-title">🛡️ Insurance</div><div class="card-value">${counts['insurance'] || 0}</div></div>
                <div class="card"><div class="card-title">📋 Permits</div><div class="card-value">${counts['permit'] || 0}</div></div>
            </div>
            <h3 style="margin:20px 0 12px">Recent Documents</h3>
            <div class="table-wrap"><table>
                <thead><tr><th>Title</th><th>Category</th><th>Folder</th><th></th></tr></thead>
                <tbody>${docs.slice(0, 50).map(d => `<tr><td>${d.title}</td><td>${d.category}</td><td>${d.folder || ''}</td><td><a href="${d.file}" target="_blank" class="btn btn-sm">📥</a></td></tr>`).join('')}</tbody>
            </table></div>
            ${data.count > 50 ? `<p style="text-align:center;color:var(--text-muted);margin-top:12px">Showing 50 of ${data.count} documents</p>` : ''}
        `;
    } catch (e) {
        content.innerHTML = `<div class="page-header"><h2>📁 Documents</h2><p style="color:var(--danger)">Failed to load</p></div>`;
    }
}

let clockInterval = null;

async function renderTimeclock(content) {
    // Clear any previous clock interval to prevent leaks
    if (clockInterval) { clearInterval(clockInterval); clockInterval = null; }

    content.innerHTML = `
        <div class="page-header"><h2>⏰ Time Clock</h2><p>${currentUser?.first_name || 'Employee'}</p></div>
        <div class="card" style="text-align:center;padding:40px">
            <div style="font-size:3rem;margin-bottom:16px" id="clock-display">--:--</div>
            <p style="color:var(--text-muted);margin-bottom:20px" id="clock-date">Loading...</p>
            <div style="display:flex;gap:12px;justify-content:center">
                <button class="btn btn-success" onclick="clockIn()">🟢 Clock In</button>
                <button class="btn btn-danger" onclick="clockOut()">🔴 Clock Out</button>
            </div>
        </div>
        <div class="card"><div class="card-title">Recent Time Entries</div>
            <div class="table-wrap"><table><thead><tr><th>Date</th><th>In</th><th>Out</th><th>Hours</th></tr></thead>
            <tbody id="time-entries"><tr><td colspan="4" style="color:var(--text-muted)">Loading...</td></tr></tbody></table></div>
        </div>`;

    function updateClock() {
        const display = document.getElementById('clock-display');
        const dateEl = document.getElementById('clock-date');
        if (!display || !dateEl) { clearInterval(clockInterval); clockInterval = null; return; }
        const now = new Date();
        display.textContent = now.toLocaleTimeString();
        dateEl.textContent = now.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    }
    updateClock();
    clockInterval = setInterval(updateClock, 1000);

    const entries = await api('/time/');
    if (entries && entries.length > 0) {
        document.getElementById('time-entries').innerHTML = entries.slice(0, 10).map(e =>
            `<tr><td>${e.date}</td><td>${(e.time_in||'').toString().slice(11,16)}</td><td>${e.time_out?(e.time_out).toString().slice(11,16):'<span style="color:var(--warning)">Still in</span>'}</td><td>${e.hours_worked||0}h</td></tr>`).join('');
    } else {
        document.getElementById('time-entries').innerHTML = '<tr><td colspan="4" style="color:var(--text-muted)">No entries yet</td></tr>';
    }
}

function clockIn() {
    fetch(API + '/time/clock-in/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
        body: JSON.stringify({ notes: '' })
    }).then(r => r.json()).then(d => {
        if (d.error) alert(d.error);
        else alert('Clocked in!');
        renderTimeclock(document.getElementById('main-content'));
    }).catch(e => alert('Error: ' + e.message));
}

function clockOut() {
    fetch(API + '/time/clock-out/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
        body: JSON.stringify({ notes: '' })
    }).then(r => r.json()).then(d => {
        if (d.error) alert(d.error);
        else alert('Clocked out!');
        renderTimeclock(document.getElementById('main-content'));
    }).catch(e => alert('Error: ' + e.message));
}

async function renderPayroll(content) {
    content.innerHTML = `<div class="page-header"><h2>💰 Payroll</h2><p>Loading...</p></div>`;
    const payroll = await api('/reports/payroll/');
    content.innerHTML = `
        <div class="page-header"><h2>💰 Payroll</h2><p>Employee payroll summary</p></div>
        <div class="table-wrap"><table><thead><tr><th>Employee</th><th>Total Hours</th><th>Total Earnings</th></tr></thead>
        <tbody>${(payroll || []).map(p => `<tr><td>${p.employee||p.username||''}</td><td>${(p.total_hours||0).toFixed(1)}h</td><td style="color:var(--success)">$${(p.total_earnings||0).toLocaleString()}</td></tr>`).join('') || '<tr><td colspan="3" style="color:var(--text-muted)">No payroll data yet</td></tr>'}</tbody></table></div>
    `;
}

async function renderReports(content) {
    content.innerHTML = `<div class="page-header"><h2>📈 Reports</h2><p>Loading...</p></div>`;
    const [summary, outstanding, revenue] = await Promise.all([
        api('/reports/summary/'),
        api('/reports/outstanding/'),
        api('/reports/revenue/'),
    ]);

    content.innerHTML = `
        <div class="page-header"><h2>📈 Reports</h2><p>Business intelligence & analytics</p></div>
        <div class="grid">
            <div class="card"><div class="card-title">Total Customers</div><div class="card-value">${summary?.total_customers||0}</div></div>
            <div class="card"><div class="card-title">Total Invoices</div><div class="card-value">${summary?.total_invoices||0}</div></div>
            <div class="card"><div class="card-title">Revenue All Time</div><div class="card-value" style="color:var(--success)">$${parseFloat(summary?.total_revenue_all_time||0).toLocaleString()}</div></div>
            <div class="card"><div class="card-title">This Month</div><div class="card-value" style="color:var(--success)">$${parseFloat(summary?.this_month_revenue||0).toLocaleString()}</div></div>
        </div>
        <div class="card"><div class="card-title">📊 Monthly Revenue Trend</div>
            <div class="bar-chart">${(revenue||[]).map(r => {
                const max = Math.max(...(revenue||[]).map(x=>x.total||0), 1);
                const pct = (r.total/max*100);
                return `<div class="bar-row"><div class="bar-label">${r.label||r.month||''}</div><div class="bar-track"><div class="bar-fill income" style="width:${pct}%"></div></div><div class="bar-value">$${(r.total||0).toLocaleString()}</div></div>`;
            }).join('') || '<p style="color:var(--text-muted)">No payment data yet</p>'}</div>
        </div>
        <div class="card"><div class="card-title">⚠️ Outstanding Invoices</div>
            <div class="table-wrap"><table><thead><tr><th>Invoice</th><th>Customer</th><th>Balance</th><th>Status</th></tr></thead>
            <tbody>${(outstanding||[]).slice(0,20).map(inv => `<tr><td>${inv.invoice_number||''}</td><td>${inv.customer||''}</td><td style="color:var(--danger)">$${parseFloat(inv.balance_due||0).toLocaleString()}</td><td><span class="badge ${inv.status==='overdue'?'badge-danger':'badge-warning'}">${inv.status||''}</span></td></tr>`).join('') || '<tr><td colspan="4" style="color:var(--text-muted)">No outstanding invoices</td></tr>'}</tbody></table></div>
        </div>
    `;
}

function filterTable(input, rowSelector) {
    const filter = input.value.toLowerCase();
    document.querySelectorAll(rowSelector).forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(filter) ? '' : 'none';
    });
}

if (token) {
    api('/auth/me/').then(me => {
        if (me && me.username) {
            currentUser = me;
            showApp();
        } else {
            doLogout();
        }
    }).catch(() => doLogout());
}
