"""
Esan ERP Database Models

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import relationship

from database import Base


# ==================================================
# USER
# ==================================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    full_name = Column(
        String(200),
        nullable=True,
    )

    email = Column(
        String(200),
        nullable=True,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    role = Column(
        String(100),
        default="user",
        nullable=False,
    )

    active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# ==================================================
# CUSTOMER
# ==================================================

class Customer(Base):

    __tablename__ = "customers"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(200),
        nullable=False,
        index=True,
    )

    contact_person = Column(
        String(200),
        nullable=True,
    )

    phone = Column(
        String(100),
        nullable=True,
        index=True,
    )

    email = Column(
        String(200),
        nullable=True,
        index=True,
    )

    address = Column(
        String(500),
        nullable=True,
    )

    location = Column(
        String(200),
        nullable=True,
    )

    country = Column(
        String(100),
        nullable=True,
    )

    customer_type = Column(
        String(100),
        default="Retail",
        nullable=False,
    )

    active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # --------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------

    quotations = relationship(
        "Quotation",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    sales_orders = relationship(
        "SalesOrder",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    invoices = relationship(
        "Invoice",
        back_populates="customer",
        lazy="selectin",
    )


# ==================================================
# SUPPLIER
# ==================================================

class Supplier(Base):

    __tablename__ = "suppliers"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(200),
        nullable=False,
        index=True,
    )

    contact_person = Column(
        String(200),
        nullable=True,
    )

    phone = Column(
        String(100),
        nullable=True,
    )

    email = Column(
        String(200),
        nullable=True,
    )

    address = Column(
        String(500),
        nullable=True,
    )

    location = Column(
        String(200),
        nullable=True,
    )

    country = Column(
        String(100),
        nullable=True,
    )

    supplier_type = Column(
        String(100),
        default="Agricultural Supplier",
        nullable=False,
    )

    active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    purchase_orders = relationship(
        "PurchaseOrder",
        back_populates="supplier",
        lazy="selectin",
    )

    purchases = relationship(
        "Purchase",
        back_populates="supplier",
        lazy="selectin",
    )


# ==================================================
# PURCHASE ORDER
# ==================================================

class PurchaseOrder(Base):

    __tablename__ = "purchase_orders"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    po_number = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    supplier_id = Column(
        Integer,
        ForeignKey(
            "suppliers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    status = Column(
        String(100),
        default="Draft",
        nullable=False,
    )

    total_amount = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    supplier = relationship(
        "Supplier",
        back_populates="purchase_orders",
        lazy="joined",
    )

    items = relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# ==================================================
# PURCHASE ORDER ITEM
# ==================================================

class PurchaseOrderItem(Base):

    __tablename__ = "purchase_order_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    purchase_order_id = Column(
        Integer,
        ForeignKey(
            "purchase_orders.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    product_name = Column(
        String(200),
        nullable=False,
    )

    quantity = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    unit_price = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    total = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    purchase_order = relationship(
        "PurchaseOrder",
        back_populates="items",
    )


# ==================================================
# PURCHASE
# ==================================================

class Purchase(Base):

    __tablename__ = "purchases"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    purchase_number = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    supplier_id = Column(
        Integer,
        ForeignKey(
            "suppliers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    product_name = Column(
        String(200),
        nullable=False,
    )

    quantity = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    unit_price = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    total_amount = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    status = Column(
        String(100),
        default="Pending",
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    supplier = relationship(
        "Supplier",
        back_populates="purchases",
        lazy="joined",
    )


# ==================================================
# WAREHOUSE
# ==================================================

class Warehouse(Base):

    __tablename__ = "warehouses"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(200),
        nullable=False,
    )

    location = Column(
        String(200),
        nullable=True,
    )

    capacity = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# ==================================================
# PRODUCT
# ==================================================

class Product(Base):

    __tablename__ = "products"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(200),
        nullable=False,
        index=True,
    )

    sku = Column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
    )

    category = Column(
        String(100),
        nullable=True,
    )

    unit = Column(
        String(50),
        default="Kg",
        nullable=False,
    )

    quantity = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    cost_price = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    selling_price = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    stock_movements = relationship(
        "StockMovement",
        back_populates="product",
        lazy="selectin",
    )


# ==================================================
# STOCK MOVEMENT
# ==================================================

class StockMovement(Base):

    __tablename__ = "stock_movements"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    product_id = Column(
        Integer,
        ForeignKey(
            "products.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    movement_type = Column(
        String(100),
        nullable=False,
    )

    quantity = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    reference = Column(
        String(200),
        nullable=True,
    )

    notes = Column(
        String(500),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    product = relationship(
        "Product",
        back_populates="stock_movements",
        lazy="joined",
    )


# ==================================================
# MILLING BATCH
# ==================================================

class MillingBatch(Base):

    __tablename__ = "milling_batches"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    batch_number = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    product_name = Column(
        String(200),
        nullable=True,
    )

    input_quantity = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    output_quantity = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    status = Column(
        String(100),
        default="Planned",
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# ==================================================
# PACKAGING BATCH
# ==================================================

class PackagingBatch(Base):

    __tablename__ = "packaging_batches"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    batch_number = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    product_name = Column(
        String(200),
        nullable=True,
    )

    quantity = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    package_size = Column(
        String(100),
        nullable=True,
    )

    status = Column(
        String(100),
        default="Planned",
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# ==================================================
# QUOTATION
# ==================================================

class Quotation(Base):

    __tablename__ = "quotations"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    quotation_number = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    customer_id = Column(
        Integer,
        ForeignKey(
            "customers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    status = Column(
        String(100),
        default="Draft",
        nullable=False,
    )

    total_amount = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    valid_until = Column(
        DateTime,
        nullable=True,
    )

    notes = Column(
        String(1000),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    customer = relationship(
        "Customer",
        back_populates="quotations",
        lazy="joined",
    )

    items = relationship(
        "QuotationItem",
        back_populates="quotation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# ==================================================
# QUOTATION ITEM
# ==================================================

class QuotationItem(Base):

    __tablename__ = "quotation_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    quotation_id = Column(
        Integer,
        ForeignKey(
            "quotations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    product_name = Column(
        String(200),
        nullable=False,
    )

    quantity = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    unit_price = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    total = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    quotation = relationship(
        "Quotation",
        back_popates="items",
    )


# ==================================================
# SALES ORDER
# ==================================================

class SalesOrder(Base):

    __tablename__ = "sales_orders"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    order_number = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    customer_id = Column(
        Integer,
        ForeignKey(
            "customers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    quotation_id = Column(
        Integer,
        ForeignKey(
            "quotations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    status = Column(
        String(100),
        default="Pending",
        nullable=False,
    )

    total_amount = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    customer = relationship(
        "Customer",
        back_populates="sales_orders",
        lazy="joined",
    )

    quotation = relationship(
        "Quotation",
        lazy="joined",
    )

    items = relationship(
        "SalesOrderItem",
        back_populates="sales_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# ==================================================
# SALES ORDER ITEM
# ==================================================

class SalesOrderItem(Base):

    __tablename__ = "sales_order_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    order_id = Column(
        Integer,
        ForeignKey(
            "sales_orders.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    product_name = Column(
        String(200),
        nullable=False,
    )

    quantity = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    unit_price = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    total = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    sales_order = relationship(
        "SalesOrder",
        back_populates="items",
    )


# ==================================================
# DELIVERY
# ==================================================

class Delivery(Base):

    __tablename__ = "deliveries"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    delivery_number = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    order_id = Column(
        Integer,
        ForeignKey(
            "sales_orders.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    customer_id = Column(
        Integer,
        ForeignKey(
            "customers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    status = Column(
        String(100),
        default="Pending",
        nullable=False,
    )

    delivery_address = Column(
        String(500),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# ==================================================
# INVOICE
# ==================================================

class Invoice(Base):

    __tablename__ = "invoices"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    invoice_number = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    customer_id = Column(
        Integer,
        ForeignKey(
            "customers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    order_id = Column(
        Integer,
        ForeignKey(
            "sales_orders.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    amount = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    status = Column(
        String(100),
        default="Unpaid",
        nullable=False,
    )

    due_date = Column(
        DateTime,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    customer = relationship(
        "Customer",
        back_populates="invoices",
        lazy="joined",
    )


# ==================================================
# PAYMENT
# ==================================================

class Payment(Base):

    __tablename__ = "payments"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    payment_number = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    invoice_id = Column(
        Integer,
        ForeignKey(
            "invoices.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    amount = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    payment_method = Column(
        String(100),
        default="Cash",
        nullable=False,
    )

    reference = Column(
        String(200),
        nullable=True,
    )

    status = Column(
        String(100),
        default="Completed",
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# ==================================================
# END OF MODELS
# ==================================================