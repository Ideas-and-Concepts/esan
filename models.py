from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime


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


    location = Column(
        String
    )


    phone = Column(
        String
    )



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


    cost = Column(
        Float
    )


    status = Column(
        String
    )



class Inventory(Base):

    __tablename__ = "inventory"


    id = Column(
        Integer,
        primary_key=True
    )


    item = Column(
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



class ProductionBatch(Base):

    __tablename__ = "production_batches"


    id = Column(
        Integer,
        primary_key=True
    )


    product = Column(
        String
    )


    input_quantity = Column(
        Float
    )


    output_quantity = Column(
        Float
    )


    date = Column(
        DateTime,
        default=datetime.now
    )



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
        String
    )