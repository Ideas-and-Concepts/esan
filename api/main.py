"""
Esan ERP API – FastAPI Backend for Vercel
==========================================
- Floating collapsible sidebar (open/close)
- All modules from streamlit_app.py
- Login with admin / admin123
- API endpoints under /api/
- Health check at /health
- Database auto‑creation (tables + admin)
- Graceful fallbacks for missing modules
"""

import os
import sys
import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from sqlalchemy import inspect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("esan_api")

# Make repository root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------- Database / models / auth ----------
try:
    from database import SessionLocal, engine, Base
    from models import (
        User, Customer, Invoice, Payment, SalesOrder, Product,
        Quotation, Supplier, Delivery, MillingBatch, PackagingBatch,
        FinanceTransaction
    )
    from auth import verify_password, hash_password
    DB_AVAILABLE = True
except Exception as e:
    logger.error(f"Database import failed: {e}")
    DB_AVAILABLE = False

# ---------- FastAPI app ----------
app = FastAPI(title="Esan ERP API", version="1.4.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    if not DB_AVAILABLE:
        return
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            admin = db.query(User).filter(User.username == "admin").first()
            if not admin:
                admin = User(
                    username="admin", password_hash=hash_password("admin123"),
                    role="Administrator", full_name="System Administrator",
                    email="admin@nileharvest.com"
                )
                db.add(admin)
                db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Startup error: {e}")

def get_db():
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database unavailable")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

security = HTTPBasic()

@app.post("/api/login")
def login(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"username": user.username, "full_name": user.full_name or user.username, "role": user.role}

# ---------- API data endpoints ----------
@app.get("/api/customers")
def list_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    return [{"id": c.id, "name": c.name, "email": c.email, "phone": c.phone,
             "customer_type": c.customer_type, "location": c.location, "country": c.country} for c in customers]

@app.get("/api/orders")
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(SalesOrder).all()
    return [{"id": o.id, "order_number": o.order_number, "customer_id": o.customer_id,
             "status": o.status, "total_amount": o.total_amount,
             "created_at": o.created_at.isoformat() if o.created_at else None} for o in orders]

@app.get("/api/invoices")
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).all()
    result = []
    for inv in invoices:
        payments = db.query(Payment).filter(Payment.invoice_id == inv.id).all()
        total_paid = sum(p.amount for p in payments)
        result.append({
            "id": inv.id, "invoice_number": inv.invoice_number,
            "customer_id": inv.customer_id, "amount": inv.amount,
            "paid": total_paid, "balance": inv.amount - total_paid,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None
        })
    return result

@app.get("/api/payments")
def list_payments(db: Session = Depends(get_db)):
    payments = db.query(Payment).all()
    return [{"id": p.id, "invoice_id": p.invoice_id, "amount": p.amount,
             "payment_method": p.payment_method, "reference": p.reference,
             "status": p.status} for p in payments]

@app.get("/api/products")
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [{"id": p.id, "name": p.name, "category": p.category, "unit": p.unit,
             "quantity": p.quantity, "cost_price": p.cost_price, "selling_price": p.selling_price} for p in products]

@app.get("/api/suppliers")
def list_suppliers(db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).all()
    return [{"id": s.id, "name": s.name, "email": s.email, "phone": s.phone} for s in suppliers]

@app.get("/api/quotations")
def list_quotations(db: Session = Depends(get_db)):
    quotations = db.query(Quotation).all()
    return [{"id": q.id, "quotation_number": q.quotation_number, "customer_id": q.customer_id,
             "status": q.status, "total_amount": q.total_amount} for q in quotations]

@app.get("/api/deliveries")
def list_deliveries(db: Session = Depends(get_db)):
    deliveries = db.query(Delivery).all()
    return [{"id": d.id, "delivery_number": d.delivery_number, "order_id": d.order_id,
             "destination": d.destination, "driver": d.driver, "status": d.status} for d in deliveries]

@app.get("/api/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    return {
        "customers": db.query(Customer).count(),
        "orders": db.query(SalesOrder).count(),
        "products": db.query(Product).count(),
        "invoices": db.query(Invoice).count(),
        "quotations": db.query(Quotation).count(),
        "suppliers": db.query(Supplier).count(),
        "milling_batches": db.query(MillingBatch).count(),
        "packaging_batches": db.query(PackagingBatch).count(),
    }

# ---------- Full ERP frontend with floating sidebar ----------
@app.get("/", response_class=HTMLResponse)
def erp_frontend():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Esan ERP – Nile Harvest Foods Ltd.</title>
        <style>
            * { margin:0; padding:0; box-sizing:border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; }
            #login-overlay { position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(255,255,255,0.98); display:flex; justify-content:center; align-items:center; z-index:999; flex-direction:column; }
            #login-overlay.hidden { display: none; }
            .login-card { background:white; padding:2rem; border-radius:10px; box-shadow:0 10px 25px rgba(0,0,0,0.1); width:320px; text-align:center; }
            .login-card h1 { font-size:2rem; margin-bottom:0.5rem; }
            .login-card input { width:100%; padding:10px; margin:8px 0; border:1px solid #ddd; border-radius:5px; }
            .login-card button { width:100%; padding:10px; background:#2e7d32; color:white; border:none; border-radius:5px; font-weight:600; cursor:pointer; }
            .login-card button:hover { background:#1b5e20; }
            .error { color:#d32f2f; font-size:0.9rem; margin-top:10px; }
            /* Layout */
            .app-container { display: flex; height: 100vh; }
            .sidebar { width: 280px; background: #f8f9fa; border-right: 1px solid #ddd;
                       position: fixed; top: 0; left: 0; height: 100vh; overflow-y: auto;
                       padding: 1rem; display: flex; flex-direction: column; z-index: 10;
                       transition: transform 0.3s ease; }
            .sidebar.collapsed { transform: translateX(-100%); }
            .main-content { margin-left: 280px; flex: 1; padding: 2rem; overflow-y: auto; transition: margin-left 0.3s ease; }
            .main-content.expanded { margin-left: 0; }
            /* Toggle button */
            .sidebar-toggle { position: fixed; top: 1rem; left: 1rem; z-index: 20; background: white; border: 1px solid #ddd; border-radius: 6px; padding: 8px 10px; cursor: pointer; display: none; }
            @media (max-width: 768px) {
                .sidebar { transform: translateX(-100%); }
                .sidebar.open { transform: translateX(0); }
                .main-content { margin-left: 0; }
                .sidebar-toggle { display: block; }
            }
            /* Sidebar elements */
            .sidebar-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
            .sidebar-header h2 { color:#2d3748; }
            .close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #888; }
            .nav-group { margin-bottom:1.5rem; }
            .nav-group-title { font-weight:600; color:#555; margin-bottom:0.3rem; text-transform:uppercase; font-size:0.8rem; }
            .nav-btn { display:block; width:100%; padding:10px 12px; margin-bottom:4px; text-align:left; background:white; border:1px solid #e0e0e0; border-radius:6px; cursor:pointer; color:#333; font-size:0.95rem; transition: background 0.2s; }
            .nav-btn:hover { background:#e2e8f0; }
            .nav-btn.active { background:#c6f6d5; border-color:#38a169; font-weight:600; }
            .user-panel { margin-top:auto; padding-top:1rem; border-top:1px solid #ddd; }
            .logout-btn { background:#e53e3e !important; color:white !important; margin-top:0.5rem; width:100%; border:none; padding:10px; border-radius:6px; cursor:pointer; }
            /* Main area */
            .main h1 { font-size:2rem; color:#2d3748; }
            .main .subtitle { color:#666; margin-bottom:2rem; }
            .kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px,1fr)); gap:1rem; margin-bottom:2rem; }
            .kpi { background:white; border-radius:10px; padding:1.2rem; box-shadow:0 2px 10px rgba(0,0,0,0.05); text-align:center; }
            .kpi .number { font-size:1.8rem; font-weight:600; color:#2e7d32; }
            .kpi .label { font-size:0.9rem; color:#888; }
            table { width:100%; border-collapse:collapse; margin-top:1rem; background:white; border-radius:8px; overflow:hidden; }
            th { background:#f5f5f5; padding:10px; text-align:left; border-bottom:2px solid #ddd; }
            td { padding:10px; border-bottom:1px solid #eee; }
            .footer { margin-top:2rem; color:#999; font-size:0.85rem; }
            #admin-menu { display: none; }
        </style>
    </head>
    <body>
        <!-- Login Screen -->
        <div id="login-overlay">
            <div class="login-card">
                <h1>🌾 Esan ERP</h1>
                <p style="margin-bottom:1rem; color:gray;">Nile Harvest Foods Ltd.</p>
                <input type="text" id="username" placeholder="Username" autocomplete="off">
                <input type="password" id="password" placeholder="Password">
                <button onclick="login()">Login</button>
                <div class="error" id="login-error"></div>
                <p style="font-size:0.8rem; margin-top:1rem; color:gray;">Default: admin / admin123</p>
            </div>
        </div>

        <!-- Main App -->
        <div id="app" style="display:none">
            <!-- Sidebar Toggle Button (mobile / collapsed) -->
            <button class="sidebar-toggle" onclick="toggleSidebar()">☰</button>

            <div class="sidebar" id="sidebar">
                <div class="sidebar-header">
                    <h2>🌾 Esan ERP</h2>
                    <button class="close-btn" onclick="toggleSidebar()">✕</button>
                </div>
                <div class="nav-group">
                    <div class="nav-group-title">MAIN</div>
                    <button class="nav-btn" data-module="overview">🏠 Overview</button>
                </div>
                <div class="nav-group">
                    <div class="nav-group-title">OPERATIONS</div>
                    <button class="nav-btn" data-module="procurement">🌾 Procurement</button>
                    <button class="nav-btn" data-module="warehouse">📦 Warehouse</button>
                    <button class="nav-btn" data-module="milling">🏭 Milling</button>
                    <button class="nav-btn" data-module="packaging">📦 Packaging</button>
                </div>
                <div class="nav-group">
                    <div class="nav-group-title">COMMERCIAL</div>
                    <button class="nav-btn" data-module="sales">🚚 Sales & Distribution</button>
                </div>
                <div class="nav-group">
                    <div class="nav-group-title">FINANCE</div>
                    <button class="nav-btn" data-module="finance">💰 Finance</button>
                </div>
                <div class="nav-group">
                    <div class="nav-group-title">LOGISTICS & HR</div>
                    <button class="nav-btn" data-module="logistics">🚚 Logistics</button>
                    <button class="nav-btn" data-module="hr">👥 HR & Employees</button>
                    <button class="nav-btn" data-module="maintenance">🔧 Maintenance</button>
                    <button class="nav-btn" data-module="ai">🤖 AI Assistant</button>
                </div>
                <div class="nav-group">
                    <div class="nav-group-title">REPORTING</div>
                    <button class="nav-btn" data-module="reports">📊 Reports</button>
                </div>
                <div class="nav-group" id="admin-menu">
                    <div class="nav-group-title">ADMINISTRATION</div>
                    <button class="nav-btn" data-module="user_management">🔐 User Management</button>
                    <button class="nav-btn" data-module="change_password">🔑 Change Password</button>
                </div>
                <div class="user-panel" id="sidebar-user">
                    <strong id="sidebar-username"></strong>
                    <div id="sidebar-role"></div>
                    <button class="logout-btn" onclick="logout()">🚪 Logout</button>
                </div>
            </div>

            <div class="main-content" id="main-content">
                <h1>🌾 Esan ERP</h1>
                <p class="subtitle">Nile Harvest Foods Ltd. | Version 1.4.0 Alpha</p>
                <div id="module-content"></div>
                <div class="footer">© Nile Harvest Foods Ltd. | Esan ERP Enterprise Platform</div>
            </div>
        </div>

        <script>
            const API_BASE = window.location.origin;
            let currentModule = 'overview';
            let userRole = '';

            // ---------- Authentication ----------
            async function login() {
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const errorDiv = document.getElementById('login-error');
                try {
                    const response = await fetch(API_BASE + '/api/login', {
                        method: 'POST',
                        headers: { 'Authorization': 'Basic ' + btoa(username + ':' + password) }
                    });
                    if (response.ok) {
                        const user = await response.json();
                        sessionStorage.setItem('user', JSON.stringify(user));
                        userRole = user.role;
                        document.getElementById('login-overlay').classList.add('hidden');
                        document.getElementById('app').style.display = 'flex';
                        document.getElementById('sidebar-username').innerText = user.full_name || user.username;
                        document.getElementById('sidebar-role').innerText = user.role;
                        if (user.role === 'Administrator') {
                            document.getElementById('admin-menu').style.display = 'block';
                        }
                        navigate('overview');
                    } else {
                        errorDiv.innerText = 'Invalid username or password';
                    }
                } catch (e) {
                    errorDiv.innerText = 'Connection error.';
                }
            }

            function logout() {
                sessionStorage.removeItem('user');
                document.getElementById('login-overlay').classList.remove('hidden');
                document.getElementById('app').style.display = 'none';
                document.getElementById('username').value = '';
                document.getElementById('password').value = '';
                document.getElementById('admin-menu').style.display = 'none';
                // Close sidebar on mobile
                document.getElementById('sidebar').classList.remove('open');
            }

            // ---------- Sidebar toggle ----------
            function toggleSidebar() {
                const sidebar = document.getElementById('sidebar');
                const mainContent = document.getElementById('main-content');
                if (window.innerWidth <= 768) {
                    sidebar.classList.toggle('open');
                } else {
                    sidebar.classList.toggle('collapsed');
                    mainContent.classList.toggle('expanded');
                }
            }

            // ---------- Navigation (mirrors streamlit_app.py) ----------
            async function navigate(module) {
                currentModule = module;
                const content = document.getElementById('module-content');
                switch(module) {
                    case 'overview': content.innerHTML = await loadOverview(); break;
                    case 'procurement': content.innerHTML = '<h3>🌾 Procurement</h3><div id="procurement-content">Loading...</div>'; loadSuppliers(); break;
                    case 'warehouse': content.innerHTML = '<h3>📦 Warehouse</h3><div id="warehouse-content">Loading...</div>'; loadProducts(); break;
                    case 'milling': content.innerHTML = '<h3>🏭 Milling</h3><p>Coming soon.</p>'; break;
                    case 'packaging': content.innerHTML = '<h3>📦 Packaging</h3><p>Coming soon.</p>'; break;
                    case 'sales':
                        content.innerHTML = `
                            <h3>🚚 Sales & Distribution</h3>
                            <div>
                                <button onclick="loadCustomers()">👥 Customers</button>
                                <button onclick="loadQuotations()">📄 Quotations</button>
                                <button onclick="loadOrders()">📋 Sales Orders</button>
                                <button onclick="loadDeliveries()">🚛 Deliveries</button>
                                <button onclick="loadInvoices()">🧾 Invoices</button>
                                <button onclick="loadPayments()">💰 Payments</button>
                            </div>
                            <div id="sales-sub-content"></div>
                        `;
                        break;
                    case 'finance': content.innerHTML = '<h3>💰 Finance</h3><p>Coming soon.</p>'; break;
                    case 'logistics': content.innerHTML = '<h3>🚚 Logistics</h3><p>Coming soon.</p>'; break;
                    case 'hr': content.innerHTML = '<h3>👥 HR & Employees</h3><p>Coming soon.</p>'; break;
                    case 'maintenance': content.innerHTML = '<h3>🔧 Maintenance</h3><p>Coming soon.</p>'; break;
                    case 'ai': content.innerHTML = '<h3>🤖 AI Assistant</h3><p>Coming soon.</p>'; break;
                    case 'reports': content.innerHTML = '<h3>📊 Reports</h3><p>Coming soon.</p>'; break;
                    case 'user_management': content.innerHTML = '<h3>🔐 User Management</h3><p>Admin only.</p>'; break;
                    case 'change_password': content.innerHTML = '<h3>🔑 Change Password</h3><p>Coming soon.</p>'; break;
                    default: content.innerHTML = '<p>Module not found.</p>';
                }
                updateActiveButton(module);
                // On mobile, close sidebar after navigation
                if (window.innerWidth <= 768) {
                    document.getElementById('sidebar').classList.remove('open');
                }
            }

            function updateActiveButton(module) {
                document.querySelectorAll('.sidebar .nav-btn').forEach(btn => btn.classList.remove('active'));
                const activeBtn = document.querySelector(`.sidebar .nav-btn[data-module="${module}"]`);
                if (activeBtn) activeBtn.classList.add('active');
            }

            // Attach click handlers to all sidebar buttons
            document.addEventListener('DOMContentLoaded', function() {
                document.querySelectorAll('.sidebar .nav-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const module = this.getAttribute('data-module');
                        if (module) navigate(module);
                    });
                });
            });

            // ---------- Data loaders ----------
            async function loadOverview() {
                try {
                    const resp = await fetch(API_BASE + '/api/dashboard/summary');
                    const data = await resp.json();
                    return `
                        <div class="kpi-grid">
                            <div class="kpi"><div class="number">${data.customers}</div><div class="label">Customers</div></div>
                            <div class="kpi"><div class="number">${data.orders}</div><div class="label">Orders</div></div>
                            <div class="kpi"><div class="number">${data.products}</div><div class="label">Products</div></div>
                            <div class="kpi"><div class="number">${data.invoices}</div><div class="label">Invoices</div></div>
                        </div>`;
                } catch (e) { return '<p>Could not load dashboard.</p>'; }
            }

            async function loadCustomers() {
                const resp = await fetch(API_BASE + '/api/customers');
                const data = await resp.json();
                let html = '<table><tr><th>Name</th><th>Type</th><th>Phone</th></tr>';
                data.forEach(c => { html += `<tr><td>${c.name}</td><td>${c.customer_type || ''}</td><td>${c.phone || ''}</td></tr>`; });
                html += '</table>';
                document.getElementById('module-content').innerHTML = '<h3>👥 Customers</h3>' + html;
            }

            async function loadOrders() {
                const resp = await fetch(API_BASE + '/api/orders');
                const data = await resp.json();
                let html = '<table><tr><th>Order #</th><th>Status</th><th>Total</th></tr>';
                data.forEach(o => { html += `<tr><td>${o.order_number}</td><td>${o.status}</td><td>${o.total_amount}</td></tr>`; });
                html += '</table>';
                document.getElementById('module-content').innerHTML = '<h3>📋 Sales Orders</h3>' + html;
            }

            async function loadQuotations() {
                const resp = await fetch(API_BASE + '/api/quotations');
                const data = await resp.json();
                let html = '<table><tr><th>Quotation #</th><th>Status</th><th>Total</th></tr>';
                data.forEach(q => { html += `<tr><td>${q.quotation_number}</td><td>${q.status}</td><td>${q.total_amount}</td></tr>`; });
                html += '</table>';
                document.getElementById('module-content').innerHTML = '<h3>📄 Quotations</h3>' + html;
            }

            async function loadInvoices() {
                const resp = await fetch(API_BASE + '/api/invoices');
                const data = await resp.json();
                let html = '<table><tr><th>Invoice #</th><th>Amount</th><th>Status</th></tr>';
                data.forEach(inv => { html += `<tr><td>${inv.invoice_number}</td><td>${inv.amount}</td><td>${inv.status}</td></tr>`; });
                html += '</table>';
                document.getElementById('module-content').innerHTML = '<h3>🧾 Invoices</h3>' + html;
            }

            async function loadPayments() {
                const resp = await fetch(API_BASE + '/api/payments');
                const data = await resp.json();
                let html = '<table><tr><th>Invoice ID</th><th>Amount</th><th>Method</th></tr>';
                data.forEach(p => { html += `<tr><td>${p.invoice_id}</td><td>${p.amount}</td><td>${p.payment_method}</td></tr>`; });
                html += '</table>';
                document.getElementById('module-content').innerHTML = '<h3>💰 Payments</h3>' + html;
            }

            async function loadDeliveries() {
                const resp = await fetch(API_BASE + '/api/deliveries');
                const data = await resp.json();
                let html = '<table><tr><th>Delivery #</th><th>Order ID</th><th>Status</th></tr>';
                data.forEach(d => { html += `<tr><td>${d.delivery_number}</td><td>${d.order_id}</td><td>${d.status}</td></tr>`; });
                html += '</table>';
                document.getElementById('module-content').innerHTML = '<h3>🚛 Deliveries</h3>' + html;
            }

            async function loadProducts() {
                const resp = await fetch(API_BASE + '/api/products');
                const data = await resp.json();
                let html = '<table><tr><th>Product</th><th>Quantity</th><th>Unit</th></tr>';
                data.forEach(p => { html += `<tr><td>${p.name}</td><td>${p.quantity}</td><td>${p.unit || ''}</td></tr>`; });
                html += '</table>';
                document.getElementById('warehouse-content').innerHTML = html;
            }

            async function loadSuppliers() {
                const resp = await fetch(API_BASE + '/api/suppliers');
                const data = await resp.json();
                let html = '<table><tr><th>Name</th><th>Email</th><th>Phone</th></tr>';
                data.forEach(s => { html += `<tr><td>${s.name}</td><td>${s.email || ''}</td><td>${s.phone || ''}</td></tr>`; });
                html += '</table>';
                document.getElementById('procurement-content').innerHTML = html;
            }

            // Restore session on page load
            window.onload = () => {
                const user = sessionStorage.getItem('user');
                if (user) {
                    const parsed = JSON.parse(user);
                    userRole = parsed.role;
                    document.getElementById('login-overlay').classList.add('hidden');
                    document.getElementById('app').style.display = 'flex';
                    document.getElementById('sidebar-username').innerText = parsed.full_name || parsed.username;
                    document.getElementById('sidebar-role').innerText = parsed.role;
                    if (parsed.role === 'Administrator') {
                        document.getElementById('admin-menu').style.display = 'block';
                    }
                    navigate('overview');
                }
            };
        </script>
    </body>
    </html>
    """

@app.get("/health")
def health():
    return {"message": "Esan ERP API is running"}