"""
Esan ERP API – FastAPI Backend for Vercel
==========================================
Works both locally and on Vercel serverless.
Ensure the root requirements.txt contains: fastapi, uvicorn, sqlalchemy, psycopg2-binary
"""

import os
import sys
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Make sure the repo root is in sys.path so we can import models, etc.
# This is safe both locally and on Vercel.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine, Base   # root database.py (not api/database.py)
from models import Customer, Invoice, Payment, SalesOrder, Product

# ------------------------------------------------------------------
# App init
# ------------------------------------------------------------------
app = FastAPI(title="Esan ERP API", version="1.0")

# Allow requests from your Streamlit frontend (update in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Database setup (only create tables if they don't exist)
# ------------------------------------------------------------------
# We do NOT use Base.metadata.create_all here because it runs on every
# cold start. Instead, we create tables lazily or use a startup event.
# For Vercel, it's better to keep the database pre‑created.
# If you really need auto‑creation, uncomment the next two lines:
# @app.on_event("startup")
# def on_startup():
#     Base.metadata.create_all(bind=engine)

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
# Error handler helper
# ------------------------------------------------------------------
def handle_db_error(func):
    """Decorator to catch database errors and return a 500 response."""
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    return wrapper

# ------------------------------------------------------------------
# Customers
# ------------------------------------------------------------------
@app.get("/customers")
@handle_db_error
def list_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "customer_type": c.customer_type,
            "location": c.location,
            "country": c.country
        }
        for c in customers
    ]

# ------------------------------------------------------------------
# Invoices
# ------------------------------------------------------------------
@app.get("/invoices")
@handle_db_error
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).all()
    result = []
    for inv in invoices:
        payments = db.query(Payment).filter(Payment.invoice_id == inv.id).all()
        total_paid = sum(p.amount for p in payments)
        balance = inv.amount - total_paid
        result.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "customer_id": inv.customer_id,
            "amount": inv.amount,
            "paid": total_paid,
            "balance": balance,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None
        })
    return result

# ------------------------------------------------------------------
# Payments
# ------------------------------------------------------------------
@app.get("/payments")
@handle_db_error
def list_payments(db: Session = Depends(get_db)):
    payments = db.query(Payment).all()
    return [
        {
            "id": p.id,
            "invoice_id": p.invoice_id,
            "amount": p.amount,
            "payment_method": p.payment_method,
            "reference": p.reference,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in payments
    ]

# ------------------------------------------------------------------
# Sales Orders
# ------------------------------------------------------------------
@app.get("/orders")
@handle_db_error
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(SalesOrder).all()
    return [
        {
            "id": o.id,
            "order_number": o.order_number,
            "customer_id": o.customer_id,
            "status": o.status,
            "total_amount": o.total_amount,
            "created_at": o.created_at.isoformat() if o.created_at else None
        }
        for o in orders
    ]

# ------------------------------------------------------------------
# Products (Inventory)
# ------------------------------------------------------------------
@app.get("/products")
@handle_db_error
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "unit": p.unit,
            "quantity": p.quantity,
            "cost_price": p.cost_price,
            "selling_price": p.selling_price
        }
        for p in products
    ]

# ------------------------------------------------------------------
# Root (health check)
# ------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Esan ERP API is running", "version": "1.0"}