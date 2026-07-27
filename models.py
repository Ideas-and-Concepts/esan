"""
Esan ERP Database Models
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging ERP
Version 1.2.0
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Text
)

from sqlalchemy.orm import relationship

from database import Base



# ==================================================
# USERS & AUTHENTICATION
# ==================================================

class User(Base):

    __tablename__ = "users"


    id = Column(
        Integer,
        primary_key=True,
        index=True
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


    full_name = Column(
        String
    )


    role = Column(
        String,
        default="user"
    )


    email = Column(
        String
    )


    active = Column(
        Boolean,
        default=True
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )




# ==================================================
# SALES & CRM
# ==================================================

class Customer(Base):

    __tablename__ = "customers"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    name = Column(
        String,
        nullable=False
    )


    phone = Column(
        String
    )


    email = Column(
        String
    )


    address = Column(
        String
    )


    customer_type = Column(
        String,
        default="Retail"
    )


    location = Column(
        String
    )


    country = Column(
        String
    )


    contact_person = Column(
        String
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    quotations = relationship(
        "Quotation",
        back_populates="customer"
    )


    orders = relationship(
        "SalesOrder",
        back_populates="customer"
    )




# ==================================================
# QUOTATIONS
# ==================================================

class Quotation(Base):

    __tablename__ = "quotations"


    id = Column(
        Integer,
        primary_key=True
    )


    quotation_number = Column(
        String,
        unique=True
    )


    customer_id = Column(
        Integer,
        ForeignKey(
            "customers.id"
        )
    )


    status = Column(
        String,
        default="Draft"
    )


    total_amount = Column(
        Float,
        default=0
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    customer = relationship(
        "Customer",
        back_populates="quotations"
    )


    items = relationship(
        "QuotationItem",
        back_populates="quotation"
    )




class QuotationItem(Base):

    __tablename__ = "quotation_items"


    id = Column(
        Integer,
        primary_key=True
    )


    quotation_id = Column(
        Integer,
        ForeignKey(
            "quotations.id"
        )
    )


    product_name = Column(
        String
    )


    quantity = Column(
        Float
    )


    unit_price = Column(
        Float
    )


    total = Column(
        Float
    )


    quotation = relationship(
        "Quotation",
        back_populates="items"
    )



# ==================================================
# SALES ORDERS
# ==================================================

class SalesOrder(Base):

    __tablename__ = "sales_orders"


    id = Column(
        Integer,
        primary_key=True
    )


    order_number = Column(
        String,
        unique=True
    )


    customer_id = Column(
        Integer,
        ForeignKey(
            "customers.id"
        )
    )


    status = Column(
        String,
        default="Pending"
    )


    total_amount = Column(
        Float,
        default=0
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    customer = relationship(
        "Customer",
        back_populates="orders"
    )


    items = relationship(
        "SalesOrderItem",
        back_populates="order"
    )



class SalesOrderItem(Base):

    __tablename__ = "sales_order_items"


    id = Column(
        Integer,
        primary_key=True
    )


    order_id = Column(
        Integer,
        ForeignKey(
            "sales_orders.id"
        )
    )


    product_name = Column(
        String
    )


    quantity = Column(
        Float
    )


    unit_price = Column(
        Float
    )


    total = Column(
        Float
    )


    order = relationship(
        "SalesOrder",
        back_populates="items"
    )

# ==================================================
# PROCUREMENT
# ==================================================

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


    email = Column(
        String
    )


    address = Column(
        String
    )


    supplier_type = Column(
        String,
        default="Agricultural Supplier"
    )


    location = Column(
        String
    )


    country = Column(
        String
    )


    contact_person = Column(
        String
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )



    purchase_orders = relationship(
        "PurchaseOrder",
        back_populates="supplier"
    )




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


    supplier_id = Column(
        Integer,
        ForeignKey(
            "suppliers.id"
        )
    )


    status = Column(
        String,
        default="Draft"
    )


    total_amount = Column(
        Float,
        default=0
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    supplier = relationship(
        "Supplier",
        back_populates="purchase_orders"
    )


    items = relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order"
    )




class PurchaseOrderItem(Base):

    __tablename__ = "purchase_order_items"


    id = Column(
        Integer,
        primary_key=True
    )


    purchase_order_id = Column(
        Integer,
        ForeignKey(
            "purchase_orders.id"
        )
    )


    product_name = Column(
        String
    )


    quantity = Column(
        Float
    )


    unit_price = Column(
        Float
    )


    total = Column(
        Float
    )


    purchase_order = relationship(
        "PurchaseOrder",
        back_populates="items"
    )




# ==================================================
# INVENTORY / WAREHOUSE
# ==================================================

class Warehouse(Base):

    __tablename__ = "warehouses"


    id = Column(
        Integer,
        primary_key=True
    )


    name = Column(
        String,
        nullable=False
    )


    location = Column(
        String
    )


    capacity = Column(
        Float
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )



class Product(Base):

    __tablename__ = "products"


    id = Column(
        Integer,
        primary_key=True
    )


    name = Column(
        String,
        nullable=False
    )


    category = Column(
        String
    )


    unit = Column(
        String,
        default="Kg"
    )


    quantity = Column(
        Float,
        default=0
    )


    cost_price = Column(
        Float,
        default=0
    )


    selling_price = Column(
        Float,
        default=0
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )




class StockMovement(Base):

    __tablename__ = "stock_movements"


    id = Column(
        Integer,
        primary_key=True
    )


    product_id = Column(
        Integer,
        ForeignKey(
            "products.id"
        )
    )


    movement_type = Column(
        String
    )


    quantity = Column(
        Float
    )


    reference = Column(
        String
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )



# ==================================================
# PRODUCTION: MILLING
# ==================================================

class MillingBatch(Base):

    __tablename__ = "milling_batches"


    id = Column(
        Integer,
        primary_key=True
    )


    batch_number = Column(
        String,
        unique=True
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


    wastage = Column(
        Float
    )


    status = Column(
        String,
        default="Processing"
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ==================================================
# PRODUCTION: PACKAGING
# ==================================================

class PackagingBatch(Base):

    __tablename__ = "packaging_batches"


    id = Column(
        Integer,
        primary_key=True
    )


    batch_number = Column(
        String,
        unique=True
    )


    product_name = Column(
        String
    )


    input_quantity = Column(
        Float
    )


    packed_quantity = Column(
        Float
    )


    package_size = Column(
        String
    )


    status = Column(
        String,
        default="Processing"
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )




# ==================================================
# SALES DELIVERY
# ==================================================

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


    order_id = Column(
        Integer,
        ForeignKey(
            "sales_orders.id"
        )
    )


    destination = Column(
        String
    )


    driver = Column(
        String
    )


    vehicle = Column(
        String
    )


    status = Column(
        String,
        default="Pending"
    )


    delivered_date = Column(
        DateTime
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )




# ==================================================
# INVOICING
# ==================================================

class Invoice(Base):

    __tablename__ = "invoices"


    id = Column(
        Integer,
        primary_key=True
    )


    invoice_number = Column(
        String,
        unique=True
    )


    customer_id = Column(
        Integer,
        ForeignKey(
            "customers.id"
        )
    )


    order_id = Column(
        Integer,
        ForeignKey(
            "sales_orders.id"
        )
    )


    amount = Column(
        Float,
        default=0
    )


    status = Column(
        String,
        default="Unpaid"
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )




# ==================================================
# PAYMENTS
# ==================================================

class Payment(Base):

    __tablename__ = "payments"


    id = Column(
        Integer,
        primary_key=True
    )


    invoice_id = Column(
        Integer,
        ForeignKey(
            "invoices.id"
        )
    )


    amount = Column(
        Float,
        default=0
    )


    payment_method = Column(
        String
    )


    reference = Column(
        String
    )


    status = Column(
        String,
        default="Completed"
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )




# ==================================================
# FINANCE TRANSACTIONS
# ==================================================

class FinanceTransaction(Base):

    __tablename__ = "finance_transactions"


    id = Column(
        Integer,
        primary_key=True
    )


    transaction_type = Column(
        String
    )


    category = Column(
        String
    )


    description = Column(
        Text
    )


    amount = Column(
        Float
    )


    reference = Column(
        String
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )




# ==================================================
# SYSTEM SETTINGS
# ==================================================

class SystemSetting(Base):

    __tablename__ = "system_settings"


    id = Column(
        Integer,
        primary_key=True
    )


    key = Column(
        String,
        unique=True
    )


    value = Column(
        String
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )




# ==================================================
# STOCK RESERVATION 
# ==================================================


class StockReservation(Base):

    __tablename__ = "stock_reservations"


    id = Column(
        Integer,
        primary_key=True
    )


    sales_order_id = Column(
        Integer,
        ForeignKey(
            "sales_orders.id"
        )
    )


    product_id = Column(
        Integer,
        ForeignKey(
            "products.id"
        )
    )


    quantity = Column(
        Float
    )


    status = Column(
        String,
        default="Reserved"
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    sales_order = relationship("SalesOrder")
    product = relationship("Product")