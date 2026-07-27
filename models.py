"""
Esan ERP Database Models
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging ERP
Version 1.2.0
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from database import Base

# ==================================================
# USERS & AUTHENTICATION
# ==================================================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="user")
    email = Column(String)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==================================================
# SALES & CRM
# ==================================================
class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)
    address = Column(String)
    customer_type = Column(String, default="Retail")
    # New fields for seed data compatibility
    location = Column(String)          # city/region
    country = Column(String)           # country name
    contact_person = Column(String)    # primary contact
    created_at = Column(DateTime, default=datetime.utcnow)

    quotations = relationship("Quotation", back_populates="customer")
    orders = relationship("SalesOrder", back_populates="customer")

# ... rest of models unchanged ...

# ==================================================
# PROCUREMENT
# ==================================================
class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)
    address = Column(String)
    supplier_type = Column(String, default="Agricultural Supplier")
    # Extra fields often present in seed data
    location = Column(String)
    country = Column(String)
    contact_person = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")

# ... all other models unchanged (Quotation, SalesOrder, etc.) ...