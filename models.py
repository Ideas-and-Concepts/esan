"""
Esan ERP Models
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
        String
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


class Inventory(Base):

    __tablename__ = "inventory"

    id = Column(
        Integer,
        primary_key=True
    )

    product = Column(
        String
    )

    quantity = Column(
        Float,
        default=0
    )

    unit = Column(
        String
    )

    location = Column(
        String
    )


class ProductionBatch(Base):

    __tablename__ = "production_batches"

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

    status = Column(
        String,
        default="Planned"
    )


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

    product = Column(
        String
    )

    quantity = Column(
        Float
    )

    package_size = Column(
        String
    )

    status = Column(
        String,
        default="Planned"
    )

# =====================================
# SALES & DISTRIBUTION MODELS
# =====================================

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey
)

from datetime import datetime


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
        String,
        default="Uganda"
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )



class SalesOrder(Base):

    __tablename__ = "sales_orders"


    id = Column(
        Integer,
        primary_key=True
    )


    customer_id = Column(
        Integer,
        ForeignKey(
            "customers.id"
        )
    )


    product = Column(
        String,
        nullable=False
    )


    quantity = Column(
        Float
    )


    unit_price = Column(
        Float
    )


    total_amount = Column(
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



class Delivery(Base):

    __tablename__ = "deliveries"


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


    truck_number = Column(
        String
    )


    driver = Column(
        String
    )


    destination = Column(
        String
    )


    status = Column(
        String,
        default="Loading"
    )


    delivery_date = Column(
        DateTime,
        default=datetime.utcnow
    )



class Payment(Base):

    __tablename__ = "payments"


    id = Column(
        Integer,
        primary_key=True
    )


    customer_id = Column(
        Integer,
        ForeignKey(
            "customers.id"
        )
    )


    amount = Column(
        Float
    )


    payment_status = Column(
        String,
        default="Unpaid"
    )


    payment_date = Column(
        DateTime,
        default=datetime.utcnow
    )
