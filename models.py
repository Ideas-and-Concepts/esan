"""
Esan ERP Database Models
Nile Harvest Foods Ltd.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime
)

from database import Base



# ==========================
# USER MANAGEMENT
# ==========================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True
    )

    username = Column(
        String,
        unique=True,
        nullable=False
    )

    full_name = Column(
        String
    )

    password_hash = Column(
        String,
        nullable=False
    )

    role = Column(
        String,
        default="User"
    )

    active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )



# ==========================
# SUPPLIERS
# ==========================

class Supplier(Base):

    __tablename__ = "suppliers"

    id = Column(
        Integer,
        primary_key=True
    )

    supplier_code = Column(
        String,
        unique=True
    )

    name = Column(
        String,
        nullable=False
    )

    phone = Column(
        String
    )

    location = Column(
        String
    )

    product = Column(
        String
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )



# ==========================
# PURCHASE ORDERS
# ==========================

class PurchaseOrder(Base):

    __tablename__ = "purchase_orders"

    id = Column(
        Integer,
        primary_key=True
    )

    po_number = Column(
        String,
        unique=True
    )

    supplier = Column(
        String
    )

    product = Column(
        String
    )

    quantity = Column(
        Float
    )

    unit_price = Column(
        Float
    )

    status = Column(
        String,
        default="Pending"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )



# ==========================
# DELIVERIES
# ==========================

class Delivery(Base):

    __tablename__ = "deliveries"

    id = Column(
        Integer,
        primary_key=True
    )

    delivery_number = Column(
        String,
        unique=True
    )

    supplier = Column(
        String
    )

    product = Column(
        String
    )

    quantity = Column(
        Float
    )

    quality_status = Column(
        String,
        default="Pending"
    )

    received_date = Column(
        DateTime,
        default=datetime.utcnow
    )



# ==========================
# INVENTORY
# ==========================

class Inventory(Base):

    __tablename__ = "inventory"

    id = Column(
        Integer,
        primary_key=True
    )

    product = Column(
        String
    )

    category = Column(
        String
    )

    quantity = Column(
        Float,
        default=0
    )

    unit = Column(
        String,
        default="Tonnes"
    )

    location = Column(
        String
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow
    )
