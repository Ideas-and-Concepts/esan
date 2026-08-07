"""
Esan ERP API – FastAPI Backend for Vercel
Starts reliably, creates tables/admin, serves login + UI.
"""

import os
import sys
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

# Make the repo root importable (so we can import models, database, auth)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine, Base
from models import Customer, Invoice, Payment, SalesOrder, Product, User
from auth import verify_password, hash_password   # ensure auth.py has these

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
# Startup: create tables and default admin (runs once per cold start)
# ------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Insert admin if missing
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
# Error handler (prevents 500 from leaking traceback)
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
# Authentication
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
# API endpoints (simplified – you can add more)
# ------------------------------------------------------------------
@app.get("/api/customers")
@handle_db_error
def list_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    return [{"id": c.id, "name": c.name, "email": c.email} for c in customers]

@app.get("/api/invoices")
@handle_db_error
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).all()
    return [{"id": i.id, "invoice_number": i.invoice_number, "amount": i.amount} for i in invoices]

@app.get("/api/orders")
@handle_db_error
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(SalesOrder).all()
    return [{"id": o.id, "order_number": o.order_number, "status": o.status} for o in orders]

@app.get("/api/products")
@handle_db_error
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [{"id": p.id, "name": p.name, "quantity": p.quantity} for p in products]

# ------------------------------------------------------------------
# Frontend – full HTML with login and sidebar (Streamlit‑like UI)
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
            * { margin:0; padding:0; box-sizing:border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
            #login-overlay { position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(255,255,255,0.98); display:flex; justify-content:center; align-items:center; z-index:999; flex-direction:column; }
            #login-overlay.hidden { display: none; }
            .login-card { background:white; padding:2rem; border-radius:10px; box-shadow:0 10px 25px rgba(0,0,0,0.1); width:320px; text-align:center; }
            .login-card h1 { font-size:2rem; margin-bottom:0.5rem; }
            .login-card input { width:100%; padding:10px; margin:8px 0; border:1px solid #ddd; border-radius:5px; }
            .login-card button { width:100%; padding:10px; background:#2e7d32; color:white; border:none; border-radius:5px; font-weight:600; cursor:pointer; }
            .login-card button:hover { background:#1b5e20; }
            .error { color:#d32f2f; font-size:0.9rem; margin-top:10px; }
            #app { display: flex; height: 100vh; }
            .sidebar { width:280px; background:#f8f9fa; padding:1.5rem; display:flex; flex-direction:column; }
            .sidebar h2 { margin-bottom:1rem; color:#2d3748; }
            .user-panel { margin-bottom:2rem; }
            .user-panel .success { color:#2f855a; }
            .user-panel .info { color:#2b6cb0; }
            .logout-btn { padding:8px 16px; background:#e53e3e; color:white; border:none; border-radius:6px; cursor:pointer; margin-bottom:1.5rem; }
            .nav select { width:100%; padding:8px; border-radius:6px; border:1px solid #cbd5e0; }
            .main { flex:1; padding:2rem; }
            .main h1 { font-size:2rem; color:#2d3748; }
            .footer { margin-top:2rem; color:#a0aec0; font-size:0.9rem; }
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

        <!-- Main App (hidden until login) -->
        <div id="app" style="display:none">
            <div class="sidebar">
                <h2>🌾 Esan ERP</h2>
                <div class="user-panel">
                    <p class="success" id="sidebar-username">✅ User: admin</p>
                    <p class="info" id="sidebar-role">ℹ️ Role: Administrator</p>
                </div>
                <button class="logout-btn" onclick="logout()">🚪 Logout</button>
                <div class="nav">
                    <label>📋 Navigation</label>
                    <select onchange="if(this.value) alert('Module navigation coming soon.')">
                        <option>Overview</option>
                        <option>🌾 Procurement</option>
                        <option>📦 Warehouse</option>
                        <option>🏭 Milling</option>
                        <option>📦 Packaging</option>
                        <option>🚚 Sales & Distribution</option>
                        <option>💰 Finance</option>
                        <option>📊 Reports</option>
                    </select>
                </div>
            </div>
            <div class="main">
                <h1>🌾 Esan ERP</h1>
                <p>Nile Harvest Foods Ltd. | Version 1.3.0 Alpha</p>
                <p>Welcome to Esan ERP. Use the sidebar to explore modules.</p>
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

            // Auto-login if session exists
            window.onload = () => {
                const user = sessionStorage.getItem('user');
                if (user) {
                    const parsed = JSON.parse(user);
                    document.getElementById('login-overlay').classList.add('hidden');
                    document.getElementById('app').style.display = 'flex';
                    document.getElementById('sidebar-username').innerText = '✅ User: ' + parsed.username;
                    document.getElementById('sidebar-role').innerText = 'ℹ️ Role: ' + parsed.role;
                }
            };
        </script>
    </body>
    </html>
    """