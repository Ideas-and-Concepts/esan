"""
Esan ERP Warehouse Service
Nile Harvest Foods Ltd.

Warehouse and Inventory Management Services
"""

from datetime import datetime

from sqlalchemy.orm import Session

from database import SessionLocal
from models import Product, StockMovement

==================================================

PRODUCTS

==================================================

def get_all_products():
"""Return all products ordered alphabetically."""

db = SessionLocal()

try:
    return (
        db.query(Product)
        .order_by(Product.name.asc())
        .all()
    )

finally:
    db.close()

def get_product(product_id):
"""Return a single product by ID."""

db = SessionLocal()

try:
    return (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

finally:
    db.close()

def create_product(
name,
category=None,
unit="Kg",
quantity=0,
cost_price=0,
selling_price=0,
):
"""Create a new inventory product."""

db = SessionLocal()

try:
    product = Product(
        name=name.strip(),
        category=category,
        unit=unit,
        quantity=float(quantity or 0),
        cost_price=float(cost_price or 0),
        selling_price=float(selling_price or 0),
        created_at=datetime.utcnow(),
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product

except Exception:
    db.rollback()
    raise

finally:
    db.close()

def update_product(
product_id,
name=None,
category=None,
unit=None,
quantity=None,
cost_price=None,
selling_price=None,
):
"""
Update an existing product.

Only supplied values are changed.
"""

db = SessionLocal()

try:
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        return None

    if name is not None:
        product.name = name.strip()

    if category is not None:
        product.category = category

    if unit is not None:
        product.unit = unit

    if quantity is not None:
        product.quantity = float(quantity)

    if cost_price is not None:
        product.cost_price = float(cost_price)

    if selling_price is not None:
        product.selling_price = float(selling_price)

    db.commit()
    db.refresh(product)

    return product

except Exception:
    db.rollback()
    raise

finally:
    db.close()

def delete_product(product_id):
"""Delete a product."""

db = SessionLocal()

try:
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        return False

    db.delete(product)
    db.commit()

    return True

except Exception:
    db.rollback()
    raise

finally:
    db.close()

==================================================

STOCK MANAGEMENT

==================================================

def adjust_stock(
product_id,
quantity,
movement_type,
reference=None,
):
"""
Add or remove stock.

Positive quantity increases stock.
Negative quantity decreases stock.

movement_type examples:
- Purchase
- Sale
- Production
- Adjustment
- Transfer
"""

db = SessionLocal()

try:
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        return None

    quantity = float(quantity)

    new_quantity = float(product.quantity or 0) + quantity

    if new_quantity < 0:
        raise ValueError(
            "Stock quantity cannot be negative."
        )

    product.quantity = new_quantity

    movement = StockMovement(
        product_id=product.id,
        movement_type=movement_type,
        quantity=quantity,
        reference=reference,
        created_at=datetime.utcnow(),
    )

    db.add(movement)

    db.commit()
    db.refresh(product)

    return product

except Exception:
    db.rollback()
    raise

finally:
    db.close()

def add_stock(
product_id,
quantity,
reference=None,
):
"""Add stock to inventory."""

return adjust_stock(
    product_id=product_id,
    quantity=quantity,
    movement_type="Stock In",
    reference=reference,
)

def remove_stock(
product_id,
quantity,
reference=None,
):
"""Remove stock from inventory."""

quantity = float(quantity)

if quantity < 0:
    raise ValueError(
        "Quantity must be positive when removing stock."
    )

return adjust_stock(
    product_id=product_id,
    quantity=-quantity,
    movement_type="Stock Out",
    reference=reference,
)

==================================================

STOCK MOVEMENTS

==================================================

def get_stock_movements(product_id=None):
"""Return stock movements, optionally filtered by product."""

db = SessionLocal()

try:
    query = db.query(StockMovement)

    if product_id is not None:
        query = query.filter(
            StockMovement.product_id == product_id
        )

    return (
        query
        .order_by(StockMovement.created_at.desc())
        .all()
    )

finally:
    db.close()

==================================================

INVENTORY SUMMARY

==================================================

def get_inventory_summary():
"""Return basic inventory statistics."""

db = SessionLocal()

try:
    products = db.query(Product).all()

    total_products = len(products)

    total_stock = sum(
        float(product.quantity or 0)
        for product in products
    )

    total_stock_value = sum(
        float(product.quantity or 0)
        * float(product.cost_price or 0)
        for product in products
    )

    return {
        "total_products": total_products,
        "total_stock": total_stock,
        "total_stock_value": total_stock_value,
    }

finally:
    db.close()