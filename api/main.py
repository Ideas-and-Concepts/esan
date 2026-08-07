"""
Esan ERP API for Vercel
- Root health check
- Full ERP frontend at /app
- API endpoints under /api/
"""

import os
import sys
import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("esan_api")

# Make repo root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="Esan ERP API", version="1.4.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ------------------------------------------------------------------
# Try to import database and models – don't crash if unavailable
# ------------------------------------------------------------------
try:
    from database import SessionLocal, engine, Base
    from models import User, Customer, Invoice, Payment, SalesOrder, Product
    from auth import verify_password, hash_password
    DB_AVAILABLE = True
except Exception as e:
    logger.error(f"Database import failed: {e}")
    DB_AVAILABLE = False

# ------------------------------------------------------------------
# Startup: create tables and admin (only if DB available)
# ------------------------------------------------------------------
@app.on_event("startup")
def startup():
    if not DB_AVAILABLE:
        logger.warning("Database not available – skipping startup setup.")
        return
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            admin = db.query(User).filter(User.username == "admin").first()
            if not admin:
                admin = User(
                    username="admin",
                    password_hash=hash_password("admin123"),
                    role="Administrator",
                    full_name="System Administrator",
                    email="admin@nileharvest.com"
                )
                db.add(admin)
                db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Startup error: {e}")

# ------------------------------------------------------------------
# Dependency
# ------------------------------------------------------------------
def get_db():
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------------------------------------------
# Simple health check (root)
# ------------------------------------------------------------------
@app.get("/")
def health():
    return {"message": "Esan ERP API is running"}

# ------------------------------------------------------------------
# Authentication endpoint
# ------------------------------------------------------------------
security = HTTPBasic()

@app.post("/api/login")
def login(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"username": user.username, "full_name": user.full_name or user.username, "role": user.role}

# ------------------------------------------------------------------
# Example data endpoints (add more as needed)
# ------------------------------------------------------------------
@app.get("/api/customers")
def customers(db: Session = Depends(get_db)):
    return [{"id": c.id, "name": c.name, "email": c.email} for c in db.query(Customer).all()]

@app.get("/api/orders")
def orders(db: Session = Depends(get_db)):
    return [{"id": o.id, "order_number": o.order_number, "status": o.status} for o in db.query(SalesOrder).all()]

@app.get("/api/invoices")
def invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).all()
    result = []
    for inv in invoices:
        payments = db.query(Payment).filter(Payment.invoice_id == inv.id).all()
        paid = sum(p.amount for p in payments)
        result.append({
            "id": inv.id, "invoice_number": inv.invoice_number,
            "amount": inv.amount, "paid": paid, "balance": inv.amount - paid,
            "status": inv.status
        })
    return result

@app.get("/api/products")
def products(db: Session = Depends(get_db)):
    return [{"id": p.id, "name": p.name, "quantity": p.quantity} for p in db.query(Product).all()]

# ------------------------------------------------------------------
# Full ERP frontend (identical to your Streamlit UI)
# ------------------------------------------------------------------
@app.get("/app", response_class=HTMLResponse)
def erp_frontend():
    # This is the exact HTML you had – unchanged, but now behind /app
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
            #app { display: flex; height: 100vh; }
            .sidebar { width:280px; background:#f8f9fa; padding:1rem; display:flex; flex-direction:column; border-right:1px solid #ddd; }
            .sidebar h2 { text-align:center; color:#2d3748; margin-bottom:1rem; }
            .sidebar .nav-group { margin-bottom:1.5rem; }
            .sidebar .nav-group-title { font-weight:600; color:#555; margin-bottom:0.3rem; text-transform:uppercase; font-size:0.8rem; }
            .sidebar button { display:block; width:100%; padding:8px 12px; margin-bottom:4px; text-align:left; background:none; border:none; border-radius:6px; cursor:pointer; color:#333; font-size:0.95rem; }
            .sidebar button:hover { background:#e2e8f0; }
            .user-panel { margin-top:auto; padding-top:1rem; border-top:1px solid #ddd; }
            .logout-btn { background:#e53e3e !important; color:white !important; margin-top:0.5rem; }
            .main { flex:1; padding:2rem; overflow-y:auto; }
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
            @media (max-width:768px) { .sidebar { display:none; } }
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
            <div class="sidebar">
                <h2>🌾 Esan ERP</h2>
                <div class="nav-group">
                    <div class="nav-group-title">MAIN</div>
                    <button onclick="navigate('overview')">🏠 Overview</button>
                </div>
                <div class="nav-group">
                    <div class="nav-group-title">OPERATIONS</div>
                    <button onclick="navigate('procurement')">🌾 Procurement</button>
                    <button onclick="navigate('warehouse')">📦 Warehouse</button>
                    <button onclick="navigate('milling')">🏭 Milling</button>
                    <button onclick="navigate('packaging')">📦 Packaging</button>
                </div>
                <div class="nav-group">
                    <div class="nav-group-title">COMMERCIAL</div>
                    <button onclick="navigate('sales')">🚚 Sales & Distribution</button>
                </div>
                <div class="nav-group">
                    <div class="nav-group-title">FINANCE</div>
                    <button onclick="navigate('finance')">💰 Finance</button>
                </div>
                <div class="nav-group">
                    <div class="nav-group-title">REPORTING</div>
                    <button onclick="navigate('reports')">📊 Reports</button>
                </div>
                <div class="user-panel" id="sidebar-user">
                    <strong id="sidebar-username"></strong>
                    <div id="sidebar-role"></div>
                    <button class="logout-btn" onclick="logout()">🚪 Logout</button>
                </div>
            </div>
            <div class="main">
                <h1>🌾 Esan ERP</h1>
                <p class="subtitle">Nile Harvest Foods Ltd. | Version 1.4.0 Alpha</p>
                <div id="module-content"></div>
                <div class="footer">© Nile Harvest Foods Ltd. | Esan ERP Enterprise Platform</div>
            </div>
        </div>

        <script>
            const API_BASE = window.location.origin;

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
                        document.getElementById('login-overlay').classList.add('hidden');
                        document.getElementById('app').style.display = 'flex';
                        document.getElementById('sidebar-username').innerText = user.full_name || user.username;
                        document.getElementById('sidebar-role').innerText = user.role;
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
            }

            async function navigate(module) {
                const content = document.getElementById('module-content');
                switch(module) {
                    case 'overview': content.innerHTML = await loadOverview(); break;
                    case 'procurement': content.innerHTML = '<h3>Procurement</h3><div id="procurement-content">Loading...</div>'; loadSuppliers(); break;
                    case 'warehouse': content.innerHTML = '<h3>Warehouse</h3><div id="warehouse-content">Loading...</div>'; loadProducts(); break;
                    case 'milling': content.innerHTML = '<h3>Milling</h3><p>Coming soon.</p>'; break;
                    case 'packaging': content.innerHTML = '<h3>Packaging</h3><p>Coming soon.</p>'; break;
                    case 'sales': content.innerHTML = '<h3>Sales & Distribution</h3><div id="sales-content">Choose a sub-module: <button onclick="loadCustomers()">Customers</button> <button onclick="loadOrders()">Orders</button> <button onclick="loadInvoices()">Invoices</button></div>'; break;
                    case 'finance': content.innerHTML = '<h3>Finance</h3><p>Coming soon.</p>'; break;
                    case 'reports': content.innerHTML = '<h3>Reports</h3><p>Coming soon.</p>'; break;
                    default: content.innerHTML = '<p>Module not found.</p>';
                }
            }

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
                document.getElementById('module-content').innerHTML = '<h3>Customers</h3>' + html;
            }

            async function loadOrders() {
                const resp = await fetch(API_BASE + '/api/orders');
                const data = await resp.json();
                let html = '<table><tr><th>Order #</th><th>Status</th><th>Total</th></tr>';
                data.forEach(o => { html += `<tr><td>${o.order_number}</td><td>${o.status}</td><td>${o.total_amount}</td></tr>`; });
                html += '</table>';
                document.getElementById('module-content').innerHTML = '<h3>Sales Orders</h3>' + html;
            }

            async function loadInvoices() {
                const resp = await fetch(API_BASE + '/api/invoices');
                const data = await resp.json();
                let html = '<table><tr><th>Invoice #</th><th>Amount</th><th>Status</th></tr>';
                data.forEach(inv => { html += `<tr><td>${inv.invoice_number}</td><td>${inv.amount}</td><td>${inv.status}</td></tr>`; });
                html += '</table>';
                document.getElementById('module-content').innerHTML = '<h3>Invoices</h3>' + html;
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

            window.onload = () => {
                const user = sessionStorage.getItem('user');
                if (user) {
                    const parsed = JSON.parse(user);
                    document.getElementById('login-overlay').classList.add('hidden');
                    document.getElementById('app').style.display = 'flex';
                    document.getElementById('sidebar-username').innerText = parsed.full_name || parsed.username;
                    document.getElementById('sidebar-role').innerText = parsed.role;
                    navigate('overview');
                }
            };
        </script>
    </body>
    </html>
    """