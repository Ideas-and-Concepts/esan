"""
Esan ERP API – FastAPI Backend for Vercel
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

# Import database and models (adjust import paths as needed)
from .database import SessionLocal, engine, Base
import sys
import os
# Add the parent directory to sys.path so we can import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Customer, Invoice, Payment, SalesOrder, Product

# Create tables (only needed if the database is fresh)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Esan ERP API", version="1.0")

# Allow requests from your Streamlit frontend (update the origin if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict to your Streamlit domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------
#  Customers
# -------------------------------
@app.get("/customers", response_model=List[dict])
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

# -------------------------------
#  Invoices
# -------------------------------
@app.get("/invoices", response_model=List[dict])
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).all()
    result = []
    for inv in invoices:
        # Calculate balance (sum of payments)
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

# -------------------------------
#  Payments
# -------------------------------
@app.get("/payments", response_model=List[dict])
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

# -------------------------------
#  Sales Orders
# -------------------------------
@app.get("/orders", response_model=List[dict])
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

# -------------------------------
#  Products (Inventory)
# -------------------------------
@app.get("/products", response_model=List[dict])
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

# -------------------------------
#  Root (health check)
# -------------------------------
@app.get("/")
def root():
    return {"message": "Esan ERP API is running", "version": "1.0"}