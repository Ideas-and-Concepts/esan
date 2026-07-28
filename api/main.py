"""
Esan ERP API
FastAPI Backend
"""

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Customer, Invoice, Payment

app = FastAPI(title="Esan ERP API", version="1.0")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Esan ERP API is running"}

@app.get("/customers")
def list_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    return [{"id": c.id, "name": c.name, "email": c.email} for c in customers]

@app.get("/invoices")
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).all()
    return [{"id": inv.id, "number": inv.invoice_number, "amount": inv.amount, "status": inv.status} for inv in invoices]

@app.get("/payments")
def list_payments(db: Session = Depends(get_db)):
    payments = db.query(Payment).all()
    return [{"id": p.id, "amount": p.amount, "method": p.payment_method} for p in payments]