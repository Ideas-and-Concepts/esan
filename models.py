"""
Esan ERP - Database Models

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha

Modules:
- Users & Authentication
- Customers
- Suppliers
- Products
- Procurement
- Warehouse
- Milling
- Packaging
- Quotations
- Sales Orders
- Deliveries
- Invoices
- Payments
- Finance / Accounting
"""

from datetime import datetime, date

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship

from database import Base


# ============================================================
# USERS
# ============================================================

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
        unique=True,
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
    )


# ============================================================
# CUSTOMER
# ============================================================

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
    )

    phone = Column(
        String(50),
        nullable=True,
    )

    email = Column(
        String(200),
        nullable=True,
    )

    address = Column(
        Text,
        nullable=True,
    )

    customer_type = Column(
        String(50),
        default="Retail",
    )

    active = Column(
        Boolean,
        default=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    quotations = relationship(
        "Quotation",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    sales_orders = relationship(
        "SalesOrder",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    invoices = relationship(
        "Invoice",
        back_populates="customer",
    )


# ============================================================
# SUPPLIER
# ============================================================

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
    )

    phone = Column(
        String(50),
        nullable=True,
    )

    email = Column(
        String(200),
        nullable=True,
    )

    address = Column(
        Text,
        nullable=True,
    )

    contact_person = Column(
        String(200),
        nullable=True,
    )

    supplier_type = Column(
        String(100),
        default="General",
    )

    active = Column(
        Boolean,
        default=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    purchase_orders = relationship(
        "PurchaseOrder",
        back_populates="supplier",
        cascade="all, delete-orphan",
    )

    purchases = relationship(
        "Purchase",
        back_populates="supplier",
    )


# ============================================================
# PRODUCT
# ============================================================

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

    product_type = Column(
        String(100),
        default="Finished Product",
    )

    unit = Column(
        String(50),
        default="Kg",
    )

    quantity = Column(
        Float,
        default=0.0,
    )

    cost_price = Column(
        Float,
        default=0.0,
    )

    selling_price = Column(
        Float,
        default=0.0,
    )

    minimum_stock = Column(
        Float,
        default=0.0,
    )

    active = Column(
        Boolean,
        default=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    stock_movements = relationship(
        "StockMovement",
        back_populates="product",
    )


# ============================================================
# PURCHASE ORDER
# ============================================================

class PurchaseOrder(Base):

    __tablename__ = "purchase_orders"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    po_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    supplier_id = Column(
        Integer,
        ForeignKey("suppliers.id"),
        nullable=False,
    )

    order_date = Column(
        Date,
        default=date.today,
    )

    status = Column(
        String(100),
        default="Draft",
    )

    total_amount = Column(
        Float,
        default=0.0,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    supplier = relationship(
        "Supplier",
        back_populates="purchase_orders",
    )

    items = relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )


# ============================================================
# PURCHASE ORDER ITEM
# ============================================================

class PurchaseOrderItem(Base):

    __tablename__ = "purchase_order_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    purchase_order_id = Column(
        Integer,
        ForeignKey("purchase_orders.id"),
        nullable=False,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=True,
    )

    product_name = Column(
        String(200),
        nullable=False,
    )

    quantity = Column(
        Float,
        default=0.0,
    )

    unit_price = Column(
        Float,
        default=0.0,
    )

    total = Column(
        Float,
        default=0.0,
    )

    received_quantity = Column(
        Float,
        default=0.0,
    )

    purchase_order = relationship(
        "PurchaseOrder",
        back_populates="items",
    )

    product = relationship(
        "Product",
    )


# ============================================================
# PURCHASE
# ============================================================

class Purchase(Base):

    __tablename__ = "purchases"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    purchase_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    supplier_id = Column(
        Integer,
        ForeignKey("suppliers.id"),
        nullable=False,
    )

    purchase_order_id = Column(
        Integer,
        ForeignKey("purchase_orders.id"),
        nullable=True,
    )

    purchase_date = Column(
        Date,
        default=date.today,
    )

    status = Column(
        String(100),
        default="Received",
    )

    total_amount = Column(
        Float,
        default=0.0,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    supplier = relationship(
        "Supplier",
        back_populates="purchases",
    )

    purchase_order = relationship(
        "PurchaseOrder",
    )

    items = relationship(
        "PurchaseItem",
        back_populates="purchase",
        cascade="all, delete-orphan",
    )


# ============================================================
# PURCHASE ITEM
# ============================================================

class PurchaseItem(Base):

    __tablename__ = "purchase_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    purchase_id = Column(
        Integer,
        ForeignKey("purchases.id"),
        nullable=False,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=True,
    )

    product_name = Column(
        String(200),
        nullable=False,
    )

    quantity = Column(
        Float,
        default=0.0,
    )

    unit_price = Column(
        Float,
        default=0.0,
    )

    total = Column(
        Float,
        default=0.0,
    )

    purchase = relationship(
        "Purchase",
        back_populates="items",
    )

    product = relationship(
        "Product",
    )


# ============================================================
# STOCK MOVEMENT
# ============================================================

class StockMovement(Base):

    __tablename__ = "stock_movements"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
    )

    movement_type = Column(
        String(100),
        nullable=False,
    )

    quantity = Column(
        Float,
        default=0.0,
    )

    reference_type = Column(
        String(100),
        nullable=True,
    )

    reference_id = Column(
        Integer,
        nullable=True,
    )

    unit_cost = Column(
        Float,
        default=0.0,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    product = relationship(
        "Product",
        back_populates="stock_movements",
    )


# ============================================================
# WAREHOUSE
# ============================================================

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
        String(300),
        nullable=True,
    )

    warehouse_type = Column(
        String(100),
        default="General",
    )

    active = Column(
        Boolean,
        default=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )


# ============================================================
# MILLING BATCH
# ============================================================

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

    raw_material = Column(
        String(200),
        nullable=False,
    )

    input_quantity = Column(
        Float,
        default=0.0,
    )

    output_quantity = Column(
        Float,
        default=0.0,
    )

    waste_quantity = Column(
        Float,
        default=0.0,
    )

    status = Column(
        String(100),
        default="Planned",
    )

    production_date = Column(
        Date,
        default=date.today,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )


# ============================================================
# PACKAGING BATCH
# ============================================================

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
        nullable=False,
    )

    input_quantity = Column(
        Float,
        default=0.0,
    )

    output_quantity = Column(
        Float,
        default=0.0,
    )

    package_size = Column(
        Float,
        default=0.0,
    )

    package_unit = Column(
        String(50),
        default="Kg",
    )

    number_of_packages = Column(
        Integer,
        default=0,
    )

    status = Column(
        String(100),
        default="Planned",
    )

    packaging_date = Column(
        Date,
        default=date.today,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )


# ============================================================
# QUOTATION
# ============================================================

class Quotation(Base):

    __tablename__ = "quotations"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    quotation_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
    )

    quotation_date = Column(
        Date,
        default=date.today,
    )

    valid_until = Column(
        Date,
        nullable=True,
    )

    status = Column(
        String(100),
        default="Draft",
    )

    total_amount = Column(
        Float,
        default=0.0,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    customer = relationship(
        "Customer",
        back_populates="quotations",
    )

    items = relationship(
        "QuotationItem",
        back_populates="quotation",
        cascade="all, delete-orphan",
    )

    sales_orders = relationship(
        "SalesOrder",
        back_populates="quotation",
    )


# ============================================================
# QUOTATION ITEM
# ============================================================

class QuotationItem(Base):

    __tablename__ = "quotation_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    quotation_id = Column(
        Integer,
        ForeignKey("quotations.id"),
        nullable=False,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=True,
    )

    product_name = Column(
        String(200),
        nullable=False,
    )

    quantity = Column(
        Float,
        default=0.0,
    )

    unit_price = Column(
        Float,
        default=0.0,
    )

    total = Column(
        Float,
        default=0.0,
    )

    quotation = relationship(
        "Quotation",
        back_populates="items",
    )

    product = relationship(
        "Product",
    )


# ============================================================
# SALES ORDER
# ============================================================

class SalesOrder(Base):

    __tablename__ = "sales_orders"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    order_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
    )

    quotation_id = Column(
        Integer,
        ForeignKey("quotations.id"),
        nullable=True,
    )

    order_date = Column(
        Date,
        default=date.today,
    )

    status = Column(
        String(100),
        default="Draft",
    )

    total_amount = Column(
        Float,
        default=0.0,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    customer = relationship(
        "Customer",
        back_populates="sales_orders",
    )

    quotation = relationship(
        "Quotation",
        back_populates="sales_orders",
    )

    items = relationship(
        "SalesOrderItem",
        back_populates="sales_order",
        cascade="all, delete-orphan",
    )

    deliveries = relationship(
        "Delivery",
        back_populates="sales_order",
        cascade="all, delete-orphan",
    )

    invoices = relationship(
        "Invoice",
        back_populates="sales_order",
    )


# ============================================================
# SALES ORDER ITEM
# ============================================================

class SalesOrderItem(Base):

    __tablename__ = "sales_order_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    sales_order_id = Column(
        Integer,
        ForeignKey("sales_orders.id"),
        nullable=False,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=True,
    )

    product_name = Column(
        String(200),
        nullable=False,
    )

    quantity = Column(
        Float,
        default=0.0,
    )

    unit_price = Column(
        Float,
        default=0.0,
    )

    total = Column(
        Float,
        default=0.0,
    )

    reserved_quantity = Column(
        Float,
        default=0.0,
    )

    delivered_quantity = Column(
        Float,
        default=0.0,
    )

    sales_order = relationship(
        "SalesOrder",
        back_populates="items",
    )

    product = relationship(
        "Product",
    )

    delivery_items = relationship(
        "DeliveryItem",
        back_populates="sales_order_item",
    )


# ============================================================
# DELIVERY
# ============================================================

class Delivery(Base):

    __tablename__ = "deliveries"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    delivery_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    sales_order_id = Column(
        Integer,
        ForeignKey("sales_orders.id"),
        nullable=False,
    )

    delivery_date = Column(
        Date,
        default=date.today,
    )

    status = Column(
        String(100),
        default="Draft",
    )

    vehicle_number = Column(
        String(100),
        nullable=True,
    )

    driver_name = Column(
        String(200),
        nullable=True,
    )

    delivery_address = Column(
        Text,
        nullable=True,
    )

    total_amount = Column(
        Float,
        default=0.0,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    sales_order = relationship(
        "SalesOrder",
        back_populates="deliveries",
    )

    items = relationship(
        "DeliveryItem",
        back_populates="delivery",
        cascade="all, delete-orphan",
    )


# ============================================================
# DELIVERY ITEM
# ============================================================

class DeliveryItem(Base):

    __tablename__ = "delivery_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    delivery_id = Column(
        Integer,
        ForeignKey("deliveries.id"),
        nullable=False,
    )

    sales_order_item_id = Column(
        Integer,
        ForeignKey("sales_order_items.id"),
        nullable=True,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=True,
    )

    product_name = Column(
        String(200),
        nullable=False,
    )

    quantity = Column(
        Float,
        default=0.0,
    )

    unit_price = Column(
        Float,
        default=0.0,
    )

    total = Column(
        Float,
        default=0.0,
    )

    delivery = relationship(
        "Delivery",
        back_populates="items",
    )

    sales_order_item = relationship(
        "SalesOrderItem",
        back_populates="delivery_items",
    )

    product = relationship(
        "Product",
    )


# ============================================================
# INVOICE
# ============================================================

class Invoice(Base):

    __tablename__ = "invoices"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    invoice_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
    )

    sales_order_id = Column(
        Integer,
        ForeignKey("sales_orders.id"),
        nullable=True,
    )

    invoice_date = Column(
        Date,
        default=date.today,
    )

    due_date = Column(
        Date,
        nullable=True,
    )

    status = Column(
        String(100),
        default="Draft",
    )

    subtotal = Column(
        Float,
        default=0.0,
    )

    tax_amount = Column(
        Float,
        default=0.0,
    )

    total_amount = Column(
        Float,
        default=0.0,
    )

    amount_paid = Column(
        Float,
        default=0.0,
    )

    balance_due = Column(
        Float,
        default=0.0,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    customer = relationship(
        "Customer",
        back_populates="invoices",
    )

    sales_order = relationship(
        "SalesOrder",
        back_populates="invoices",
    )

    items = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    payments = relationship(
        "Payment",
        back_populates="invoice",
    )


# ============================================================
# INVOICE ITEM
# ============================================================

class InvoiceItem(Base):

    __tablename__ = "invoice_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id"),
        nullable=False,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=True,
    )

    product_name = Column(
        String(200),
        nullable=False,
    )

    quantity = Column(
        Float,
        default=0.0,
    )

    unit_price = Column(
        Float,
        default=0.0,
    )

    total = Column(
        Float,
        default=0.0,
    )

    invoice = relationship(
        "Invoice",
        back_populates="items",
    )

    product = relationship(
        "Product",
    )


# ============================================================
# PAYMENT
# ============================================================

class Payment(Base):

    __tablename__ = "payments"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    payment_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id"),
        nullable=False,
    )

    payment_date = Column(
        Date,
        default=date.today,
    )

    amount = Column(
        Float,
        default=0.0,
    )

    payment_method = Column(
        String(100),
        default="Cash",
    )

    reference = Column(
        String(200),
        nullable=True,
    )

    status = Column(
        String(100),
        default="Completed",
    )

    notes = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    invoice = relationship(
        "Invoice",
        back_populates="payments",
    )


# ============================================================
# FINANCE / ACCOUNTING
# ============================================================


# ============================================================
# ACCOUNT
# ============================================================

class Account(Base):
    """
    Chart of Accounts.
    """

    __tablename__ = "accounts"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    name = Column(
        String(150),
        nullable=False,
    )

    account_type = Column(
        String(50),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )


# ============================================================
# JOURNAL ENTRY
# ============================================================

class JournalEntry(Base):
    """
    General Ledger journal header.
    """

    __tablename__ = "journal_entries"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    entry_number = Column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
    )

    entry_date = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

    reference_type = Column(
        String(50),
        nullable=True,
        index=True,
    )

    reference_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    status = Column(
        String(30),
        default="Draft",
        nullable=False,
        index=True,
    )

    posted_at = Column(
        DateTime,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    lines = relationship(
        "JournalEntryLine",
        back_populates="journal_entry",
        cascade="all, delete-orphan",
    )


# ============================================================
# JOURNAL ENTRY LINE
# ============================================================

class JournalEntryLine(Base):
    """
    Individual debit/credit line in a journal entry.
    """

    __tablename__ = "journal_entry_lines"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    journal_entry_id = Column(
        Integer,
        ForeignKey("journal_entries.id"),
        nullable=False,
        index=True,
    )

    account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )

    debit = Column(
        Numeric(18, 2),
        default=0,
        nullable=False,
    )

    credit = Column(
        Numeric(18, 2),
        default=0,
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    journal_entry = relationship(
        "JournalEntry",
        back_populates="lines",
    )

    account = relationship(
        "Account",
    )