"""
Seed Data for Esan ERP
Nile Harvest Foods Ltd.
"""

import sys
from datetime import datetime
from database import SessionLocal
from models import (
    Customer, Supplier, Product, Warehouse,
    SalesOrder, SalesOrderItem, Quotation, QuotationItem
)

def load_seed_data():
    db = SessionLocal()
    try:
        # Only seed if no customers exist (prevents duplicate seeding)
        if db.query(Customer).count() > 0:
            return

        # ------- CUSTOMERS -------
        c1 = Customer(
            name="Juba Traders Ltd",
            phone="+211 912 345 678",
            email="info@jubatraders.com",
            address="Juba Market Road",
            customer_type="Wholesale",
            location="Juba",
            country="South Sudan",
            contact_person="John Deng"
        )
        c2 = Customer(
            name="Kampala Retailers",
            phone="+256 701 234 567",
            email="sales@kampalaretail.ug",
            address="Kampala Road 45",
            customer_type="Retail",
            location="Kampala",
            country="Uganda",
            contact_person="Sarah Nambi"
        )
        db.add_all([c1, c2])

        # ------- SUPPLIERS -------
        s1 = Supplier(
            name="Abyssinia Grains Co.",
            phone="+251 911 223 344",
            email="abyssinia@grains.et",
            address="Addis Ababa",
            supplier_type="Agricultural Supplier",
            location="Addis Ababa",
            country="Ethiopia",
            contact_person="Dawit Mekonnen"
        )
        db.add(s1)

        # ------- PRODUCTS -------
        p1 = Product(name="Maize Flour 5kg", category="Flour", unit="Bag", quantity=5000, cost_price=3500, selling_price=4000)
        p2 = Product(name="Wheat Flour 2kg", category="Flour", unit="Bag", quantity=3000, cost_price=2800, selling_price=3200)
        db.add_all([p1, p2])

        # ------- WAREHOUSES -------
        w1 = Warehouse(name="Main Warehouse", location="Kampala", capacity=100000)
        db.add(w1)

        # Commit the base data first
        db.commit()

        # ------- CREATE A QUOTATION (example) -------
        quotation = Quotation(
            quotation_number="Q-2024-001",
            customer_id=c1.id,
            status="Sent",
            total_amount=4000000,
            created_at=datetime.utcnow()
        )
        db.add(quotation)
        db.flush()  # get quotation.id

        q_item = QuotationItem(
            quotation_id=quotation.id,
            product_name="Maize Flour 5kg",
            quantity=1000,
            unit_price=4000,
            total=4000000
        )
        db.add(q_item)

        # ------- CREATE A SALES ORDER (correct way: no 'product' argument) -------
        order = SalesOrder(
            order_number="SO-2024-001",
            customer_id=c1.id,
            status="Pending",
            total_amount=4000000,
            created_at=datetime.utcnow()
        )
        db.add(order)
        db.flush()

        order_item = SalesOrderItem(
            order_id=order.id,
            product_name="Maize Flour 5kg",
            quantity=1000,
            unit_price=4000,
            total=4000000
        )
        db.add(order_item)

        db.commit()
        print("✅ Seed data loaded successfully.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error loading seed data: {e}")
    finally:
        db.close()