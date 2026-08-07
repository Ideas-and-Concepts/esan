"""
Esan ERP API – FastAPI Backend for Vercel
With auto‑creation of tables and admin user.
"""

import os
import sys
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine, Base
from models import Customer, Invoice, Payment, SalesOrder, Product, User
from auth import verify_password, hash_password

app = FastAPI(title="Esan ERP API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Startup: create tables + admin
# ------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
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
# Keep all your existing endpoints exactly as they were
# (customers, invoices, payments, orders, products, dashboard/summary)
# ... (I'll assume they are already there – no changes needed)
# ------------------------------------------------------------------

# (Place your remaining routes here)

# ------------------------------------------------------------------
# Serve frontend at root (keep your existing HTML)
# ------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def root():
    # Your static HTML page – unchanged
    return """..."""  # (abbreviated – use your existing frontend)
