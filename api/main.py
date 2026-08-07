"""
Esan ERP API – FastAPI Backend for Vercel
Serves API endpoints and a static frontend that mimics the Streamlit UI.
"""

import os
import sys
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from typing import List
import json

# Ensure the repo root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine, Base
from models import Customer, Invoice, Payment, SalesOrder, Product, User
from auth import verify_password, hash_password      # <-- Added hash_password

# ------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------
app = FastAPI(title="Esan ERP API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Startup: auto‑create tables and default admin
# ------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    # Create tables if they don't exist (safe to run multiple times)
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

# ------------------------------------------------------------------
# Dependency
# ------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------------------------------------------
# Error handler
# ------------------------------------------------------------------
def handle_db_error(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return wrapper

# ------------------------------------------------------------------
# Authentication endpoint
# ------------------------------------------------------------------
security = HTTPBasic()

@app.post("/api/login")
def login(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "username": user.username,
        "full_name": user.full_name or user.username,
        "role": user.role
    }

# ------------------------------------------------------------------
# Existing API endpoints (keep all your current routes)
# ------------------------------------------------------------------
@app.get("/api/customers")
@handle_db_error
def list_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    return [{"id": c.id, "name": c.name, "email": c.email, "phone": c.phone, "customer_type": c.customer_type, "location": c.location, "country": c.country} for c in customers]

@app.get("/api/invoices")
@handle_db_error
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).all()
    result = []
    for inv in invoices:
        payments = db.query(Payment).filter(Payment.invoice_id == inv.id).all()
        total_paid = sum(p.amount for p in payments)
        balance = inv.amount - total_paid
        result.append({
            "id": inv.id, "invoice_number": inv.invoice_number,
            "customer_id": inv.customer_id, "amount": inv.amount,
            "paid": total_paid, "balance": balance, "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None
        })
    return result

@app.get("/api/payments")
@handle_db_error
def list_payments(db: Session = Depends(get_db)):
    payments = db.query(Payment).all()
    return [{"id": p.id, "invoice_id": p.invoice_id, "amount": p.amount, "payment_method": p.payment_method, "reference": p.reference, "status": p.status, "created_at": p.created_at.isoformat() if p.created_at else None} for p in payments]

@app.get("/api/orders")
@handle_db_error
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(SalesOrder).all()
    return [{"id": o.id, "order_number": o.order_number, "customer_id": o.customer_id, "status": o.status, "total_amount": o.total_amount, "created_at": o.created_at.isoformat() if o.created_at else None} for o in orders]

@app.get("/api/products")
@handle_db_error
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [{"id": p.id, "name": p.name, "category": p.category, "unit": p.unit, "quantity": p.quantity, "cost_price": p.cost_price, "selling_price": p.selling_price} for p in products]

@app.get("/api/dashboard/summary")
@handle_db_error
def dashboard_summary(db: Session = Depends(get_db)):
    total_customers = db.query(Customer).count()
    total_orders = db.query(SalesOrder).count()
    total_products = db.query(Product).count()
    total_invoiced = db.query(Invoice).count()
    return {
        "customers": total_customers,
        "orders": total_orders,
        "products": total_products,
        "invoices": total_invoiced
    }

# ------------------------------------------------------------------
# Serve the static frontend (index.html) at root
# ------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Esan ERP – Nile Harvest Foods Ltd.</title>
        <style>
            /* ===== FULL STREAMLIT-LIKE CSS ===== */
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f5f5f5; }
            #login-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.98); display: flex; justify-content: center; align-items: center; z-index: 999; flex-direction: column; }
            #login-overlay.hidden { display: none; }
            .login-card { background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); width: 320px; text-align: center; }
            .login-card h1 { font-size: 2rem; margin-bottom: 0.5rem; }
            .login-card input { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 5px; }
            .login-card button { width: 100%; padding: 10px; background: #2e7d32; color: white; border: none; border-radius: 5px; font-weight: 600; cursor: pointer; }
            .login-card button:hover { background: #1b5e20; }
            .error { color: #d32f2f; font-size: 0.9rem; margin-top: 10px; }
            #app { display: flex; height: 100vh; }
            .sidebar { width: 280px; background: #f8f9fa; padding: 1.5rem; border-right: 1px solid #e0e0e0; display: flex; flex-direction: column; overflow-y: auto; }
            .sidebar h2 { font-size: 1.5rem; color: #2e7d32; margin-bottom: 1rem; }
            .user-panel { margin-bottom: 1.5rem; padding: 12px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
            .user-panel .success { color: #2e7d32; font-weight: 500; }
            .user-panel .info { color: #1565c0; font-size: 0.9rem; }
            .logout-btn { padding: 10px; background: #d32f2f; color: white; border: none; border-radius: 6px; cursor: pointer; margin-bottom: 1.5rem; font-weight: 500; }
            .nav-label { font-size: 0.8rem; text-transform: uppercase; color: #888; margin-bottom: 0.5rem; }
            #nav-select { width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #ccc; font-size: 0.95rem; background: white; }
            .main { flex: 1; padding: 2rem; overflow-y: auto; }
            .main h1 { font-size: 2rem; color: #2e7d32; margin-bottom: 0.3rem; }
            .main .subtitle { color: #666; margin-bottom: 2rem; }
            .footer { margin-top: 2rem; color: #999; font-size: 0.85rem; }
            .card { background: white; border-radius: 10px; padding: 1.5rem; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 1rem; }
            table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
            th { background: #f5f5f5; padding: 10px; text-align: left; border-bottom: 2px solid #ddd; }
            td { padding: 10px; border-bottom: 1px solid #eee; }
            .kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px,1fr)); gap: 1rem; margin-bottom: 2rem; }
            .kpi { background: white; border-radius: 10px; padding: 1.2rem; box-shadow: 0 2px 10px rgba(0,0,0,0.05); text-align: center; }
            .kpi .number { font-size: 1.8rem; font-weight: 600; color: #2e7d32; }
            .kpi .label { font-size: 0.9rem; color: #888; }
            @media (max-width: 768px) { .sidebar { display: none; } }
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

        <!-- Main App (hidden until login) -->
        <div id="app" style="display:none">
            <div class="sidebar">
                <h2>🌾 Esan ERP</h2>
                <div class="user-panel">
                    <div class="success" id="sidebar-username"></div>
                    <div class="info" id="sidebar-role"></div>
                </div>
                <button class="logout-btn" onclick="logout()">🚪 Logout</button>
                <div class="nav-label">📋 Navigation</div>
                <select id="nav-select" onchange="loadModule(this.value)">
                    <option value="overview">Overview</option>
                    <option value="procurement">🌾 Procurement</option>
                    <option value="warehouse">📦 Warehouse</option>
                    <option value="milling">🏭 Milling</option>
                    <option value="packaging">📦 Packaging</option>
                    <option value="sales">🚚 Sales & Distribution</option>
                    <option value="finance">💰 Finance</option>
                    <option value="reports">📊 Reports</option>
                </select>
            </div>
            <div class="main">
                <h1>🌾 Esan ERP</h1>
                <p class="subtitle">Nile Harvest Foods Ltd. | Version 1.3.0 Alpha</p>
                <div id="module-content">
                    <!-- Dynamic content inserted here -->
                </div>
                <div class="footer">© Nile Harvest Foods Ltd. | Esan ERP Enterprise Platform</div>
            </div>
        </div>

        <script>
            // ---------- Configuration ----------
            const API_BASE = window.location.origin;   // automatically uses the current Vercel URL

            // ---------- Authentication ----------
            async function login() {
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const errorDiv = document.getElementById('login-error');

                try {
                    const response = await fetch(API_BASE + '/api/login', {
                        method: 'POST',
                        headers: {
                            'Authorization': 'Basic ' + btoa(username + ':' + password)
                        }
                    });

                    if (response.ok) {
                        const user = await response.json();
                        sessionStorage.setItem('user', JSON.stringify(user));
                        document.getElementById('login-overlay').classList.add('hidden');
                        document.getElementById('app').style.display = 'flex';
                        document.getElementById('sidebar-username').innerText = '✅ User: ' + user.username;
                        document.getElementById('sidebar-role').innerText = 'ℹ️ Role: ' + user.role;
                        loadModule('overview');
                    } else {
                        errorDiv.innerText = 'Invalid username or password';
                    }
                } catch (e) {
                    errorDiv.innerText = 'Connection error. Check your network.';
                }
            }

            function logout() {
                sessionStorage.removeItem('user');
                document.getElementById('login-overlay').classList.remove('hidden');
                document.getElementById('app').style.display = 'none';
                document.getElementById('username').value = '';
                document.getElementById('password').value = '';
            }

            // ---------- Module Loader ----------
            async function loadModule(module) {
                const content = document.getElementById('module-content');
                switch(module) {
                    case 'overview': content.innerHTML = await loadOverview(); break;
                    case 'procurement': content.innerHTML = '<h3>Procurement</h3><p>Coming soon.</p>'; break;
                    case 'warehouse': content.innerHTML = '<h3>Warehouse</h3><div id="products-table"></div>'; loadProducts(); break;
                    case 'sales': content.innerHTML = '<h3>Sales & Distribution</h3><p>Choose a sub-module:</p><button onclick="loadCustomers()">Customers</button> <button onclick="loadOrders()">Orders</button> <button onclick="loadInvoices()">Invoices</button>'; break;
                    case 'finance': content.innerHTML = '<h3>Finance</h3><p>Coming soon.</p>'; break;
                    case 'reports': content.innerHTML = '<h3>Reports</h3><p>Coming soon.</p>'; break;
                    default: content.innerHTML = '<p>Select a module.</p>';
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
                        </div>
                    `;
                } catch (e) {
                    return '<p>Failed to load dashboard.</p>';
                }
            }

            async function loadCustomers() {
                const resp = await fetch(API_BASE + '/api/customers');
                const customers = await resp.json();
                let html = '<h3>Customers</h3><table><tr><th>Name</th><th>Type</th><th>Phone</th></tr>';
                customers.forEach(c => {
                    html += `<tr><td>${c.name}</td><td>${c.customer_type}</td><td>${c.phone || ''}</td></tr>`;
                });
                html += '</table>';
                document.getElementById('module-content').innerHTML = html;
            }

            async function loadOrders() {
                const resp = await fetch(API_BASE + '/api/orders');
                const orders = await resp.json();
                let html = '<h3>Sales Orders</h3><table><tr><th>Order #</th><th>Status</th><th>Total</th></tr>';
                orders.forEach(o => {
                    html += `<tr><td>${o.order_number}</td><td>${o.status}</td><td>${o.total_amount}</td></tr>`;
                });
                html += '</table>';
                document.getElementById('module-content').innerHTML = html;
            }

            async function loadInvoices() {
                const resp = await fetch(API_BASE + '/api/invoices');
                const invoices = await resp.json();
                let html = '<h3>Invoices</h3><table><tr><th>Invoice #</th><th>Amount</th><th>Status</th></tr>';
                invoices.forEach(inv => {
                    html += `<tr><td>${inv.invoice_number}</td><td>${inv.amount}</td><td>${inv.status}</td></tr>`;
                });
                html += '</table>';
                document.getElementById('module-content').innerHTML = html;
            }

            async function loadProducts() {
                const resp = await fetch(API_BASE + '/api/products');
                const products = await resp.json();
                let html = '<h3>Products</h3><table><tr><th>Name</th><th>Quantity</th><th>Unit</th></tr>';
                products.forEach(p => {
                    html += `<tr><td>${p.name}</td><td>${p.quantity}</td><td>${p.unit}</td></tr>`;
                });
                html += '</table>';
                document.getElementById('products-table').innerHTML = html;
            }

            // Check if user already logged in (session)
            window.onload = () => {
                const user = sessionStorage.getItem('user');
                if (user) {
                    const parsed = JSON.parse(user);
                    document.getElementById('login-overlay').classList.add('hidden');
                    document.getElementById('app').style.display = 'flex';
                    document.getElementById('sidebar-username').innerText = '✅ User: ' + parsed.username;
                    document.getElementById('sidebar-role').innerText = 'ℹ️ Role: ' + parsed.role;
                    loadModule('overview');
                }
            };
        </script>
    </body>
    </html>
    """