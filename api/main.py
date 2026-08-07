"""
Esan ERP – Vercel Unified Endpoint
Serves a static HTML page that looks like the Streamlit UI,
with the API available under /api/
"""

import os
import sys
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List

# Ensure the repo root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine, Base
from models import Customer, Invoice, Payment, SalesOrder, Product

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
# API Endpoints (kept separate under /api/)
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
# Static HTML that mimics the Streamlit UI
# ------------------------------------------------------------------
STREAMLIT_APP_URL = "https://YOUR-STREAMLIT-APP.streamlit.app"  # <-- change this

@app.get("/", response_class=HTMLResponse)
def root():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Esan ERP</title>
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
            .app {{ display: flex; height: 100vh; }}
            .sidebar {{ width: 280px; background: #f8f9fa; padding: 1.5rem; display: flex; flex-direction: column; }}
            .sidebar h2 {{ margin-bottom: 1rem; color: #2d3748; }}
            .user-panel {{ margin-bottom: 2rem; }}
            .user-panel .success {{ color: #2f855a; }}
            .user-panel .info {{ color: #2b6cb0; }}
            .logout {{ margin: 1rem 0; }}
            .logout button {{ padding: 8px 16px; background: #e53e3e; color: white; border: none; border-radius: 6px; cursor: pointer; }}
            .nav {{ flex: 1; }}
            .nav select {{ width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e0; }}
            .main {{ flex: 1; padding: 2rem; }}
            .main h1 {{ font-size: 2rem; color: #2d3748; }}
            .footer {{ margin-top: 2rem; color: #a0aec0; font-size: 0.9rem; }}
            @media (max-width: 768px) {{ .sidebar {{ display: none; }} }}
        </style>
    </head>
    <body>
        <div class="app">
            <div class="sidebar">
                <h2>🌾 Esan ERP</h2>
                <div class="user-panel">
                    <p class="success">✅ User: admin</p>
                    <p class="info">ℹ️ Role: Administrator</p>
                </div>
                <div class="logout">
                    <button onclick="window.location.href='{STREAMLIT_APP_URL}'">🚀 Launch Full App</button>
                </div>
                <div class="nav">
                    <label>📋 Navigation</label>
                    <select onchange="if(this.value) alert('Open the full app at {STREAMLIT_APP_URL}')">
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
                <p>This is a static preview. <a href="{STREAMLIT_APP_URL}">Open the full interactive ERP →</a></p>
                <div class="footer">© Nile Harvest Foods Ltd. | Esan ERP Enterprise Platform</div>
            </div>
        </div>
    </body>
    </html>
    """