"""
Esan ERP Warehouse Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Handles:
- Products
- Inventory
- Stock movements
- Stock adjustments
"""

from datetime import datetime

from database import SessionLocal
from models import (
    Product,
    StockMovement,
)


# ============================================================
# PRODUCTS
# ============================================================

def get_all_products():
    """Return all products."""

    db = SessionLocal()

    try:

        return (
            db.query(Product)
            .order_by(
                Product.name.asc()
            )
            .all()
        )

    finally:
        db.close()


def get_product(product_id):
    """Return a product by ID."""

    db = SessionLocal()

    try:

        return (
            db.query(Product)
            .filter(
                Product.id == product_id
            )
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
    """Create a new product."""

    if not name or not name.strip():
        raise ValueError(
            "Product name is required."
        )

    if quantity < 0:
        raise ValueError(
            "Opening quantity cannot be negative."
        )

    if cost_price < 0:
        raise ValueError(
            "Cost price cannot be negative."
        )

    if selling_price < 0:
        raise ValueError(
            "Selling price cannot be negative."
        )

    db = SessionLocal()

    try:

        product = Product(
            name=name.strip(),
            category=category,
            unit=unit or "Kg",
            quantity=float(quantity),
            cost_price=float(cost_price),
            selling_price=float(
                selling_price
            ),
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
    name,
    category=None,
    unit="Kg",
    cost_price=0,
    selling_price=0,
):
    """
    Update product information.

    Stock quantity is deliberately not changed here.
    Stock changes should go through adjust_stock().
    """

    if not name or not name.strip():
        raise ValueError(
            "Product name is required."
        )

    db = SessionLocal()

    try:

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id
            )
            .first()
        )

        if not product:
            return None

        product.name = name.strip()
        product.category = category
        product.unit = unit or "Kg"
        product.cost_price = float(
            cost_price
        )
        product.selling_price = float(
            selling_price
        )

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
            .filter(
                Product.id == product_id
            )
            .first()
        )

        if not product:
            return False

        # Prevent deleting a product with
        # stock remaining.
        if (
            product.quantity is not None
            and product.quantity > 0
        ):
            raise ValueError(
                "Cannot delete a product "
                "that still has stock."
            )

        db.delete(product)

        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# STOCK MANAGEMENT
# ============================================================

def adjust_stock(
    product_id,
    quantity,
    movement_type,
    reference=None,
):
    """
    Adjust product stock.

    movement_type:
        IN
        OUT
    """

    quantity = float(quantity)

    if quantity <= 0:
        raise ValueError(
            "Stock adjustment quantity "
            "must be greater than zero."
        )

    movement_type = (
        movement_type.upper().strip()
    )

    if movement_type not in [
        "IN",
        "OUT",
    ]:
        raise ValueError(
            "Movement type must be IN or OUT."
        )

    db = SessionLocal()

    try:

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id
            )
            .first()
        )

        if not product:
            raise ValueError(
                "Product not found."
            )

        current_quantity = float(
            product.quantity or 0
        )

        if movement_type == "IN":

            new_quantity = (
                current_quantity +
                quantity
            )

        else:

            new_quantity = (
                current_quantity -
                quantity
            )

            if new_quantity < 0:

                raise ValueError(
                    "Insufficient stock. "
                    f"Available: "
                    f"{current_quantity:,.2f} "
                    f"{product.unit}"
                )

        product.quantity = (
            new_quantity
        )

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


def get_stock_movements(
    product_id=None
):
    """Return stock movements."""

    db = SessionLocal()

    try:

        query = (
            db.query(StockMovement)
        )

        if product_id is not None:

            query = query.filter(
                StockMovement.product_id
                == product_id
            )

        return (
            query
            .order_by(
                StockMovement.created_at.desc()
            )
            .all()
        )

    finally:
        db.close()


def get_total_stock():
    """Return total stock quantity."""

    db = SessionLocal()

    try:

        total = (
            db.query(
                Product.quantity
            ).all()
        )

        return sum(
            float(row[0] or 0)
            for row in total
        )

    finally:
        db.close()