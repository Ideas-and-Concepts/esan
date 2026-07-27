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
    DateTime,
    Boolean
)

from database import Base



# =====================================
# USER MODEL
# =====================================

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


    password_hash = Column(
        String,
        nullable=False
    )


    role = Column(
        String,
        default="user"
    )



# =====================================
# SUPPLIERS
# =====================================

class Supplier(Base):

    __tablename__ = "suppliers"


    id = Column(
        Integer,
        primary_key=True
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


    country = Column(
        String
    )


    active = Column(
        Boolean,
        default=True
    )



# =====================================
# PROCUREMENT
# =====================================

class PurchaseOrder(Base):

    __tablename__ = "purchase_orders"


    id = Column(
        Integer,
        primary_key=True
    )


    supplier = Column(
        String
    )


    material = Column(
        String
    )


    quantity = Column(
        Float
    )


    unit_cost = Column(
        Float
    )


    total_cost = Column(
        Float
    )


    status = Column(
        String,
        default="Pending"
    )


    created_at = Column(
        DateTime,
        default=datetime.now
    )



# =====================================
# INVENTORY
# =====================================

class Inventory(Base):

    __tablename__ = "inventory"


    id = Column(
        Integer,
        primary_key=True
    )


    item_name = Column(
        String
    )


    category = Column(
        String
    )


    quantity = Column(
        Float
    )


    unit = Column(
        String
    )


    location = Column(
        String
    )


    updated_at = Column(
        DateTime,
        default=datetime.now
    )



# =====================================
# MILLING PRODUCTION
# =====================================

class ProductionBatch(Base):

    __tablename__ = "production_batches"


    id = Column(
        Integer,
        primary_key=True
    )


    product = Column(
        String
    )


    raw_material = Column(
        String
    )


    input_quantity = Column(
        Float
    )


    output_quantity = Column(
        Float
    )


    waste_quantity = Column(
        Float
    )


    production_date = Column(
        DateTime,
        default=datetime.now
    )



# =====================================
# PACKAGING
# =====================================

class PackagingRecord(Base):

    __tablename__ = "packaging_records"


    id = Column(
        Integer,
        primary_key=True
    )


    product = Column(
        String
    )


    quantity = Column(
        Float
    )


    packaging_size = Column(
        String
    )


    batch_number = Column(
        String
    )


    date = Column(
        DateTime,
        default=datetime.now
    )



# =====================================
# CUSTOMERS
# =====================================

class Customer(Base):

    __tablename__ = "customers"


    id = Column(
        Integer,
        primary_key=True
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


    country = Column(
        String
    )


    customer_type = Column(
        String
    )



# =====================================
# SALES ORDERS
# =====================================

class SalesOrder(Base):

    __tablename__ = "sales_orders"


    id = Column(
        Integer,
        primary_key=True
    )


    customer = Column(
        String
    )


    product = Column(
        String
    )


    quantity = Column(
        Float
    )


    amount = Column(
        Float
    )


    status = Column(
        String,
        default="Pending"
    )


    order_date = Column(
        DateTime,
        default=datetime.now
    )



# =====================================
# PAYMENTS
# =====================================

class Payment(Base):

    __tablename__ = "payments"


    id = Column(
        Integer,
        primary_key=True
    )


    customer = Column(
        String
    )


    invoice_number = Column(
        String
    )


    amount = Column(
        Float
    )


    status = Column(
        String
    )


    payment_date = Column(
        DateTime,
        default=datetime.now
    )


# =====================================
# CUSTOMERS
# =====================================

class Customer(Base):

    __tablename__ = "customers"


    id = Column(
        Integer,
        primary_key=True
    )


    name = Column(
        String
    )


    phone = Column(
        String
    )


    location = Column(
        String
    )


    country = Column(
        String
    )


    customer_type = Column(
        String
    )