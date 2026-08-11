"""
Esan ERP Warehouse Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Handles:
- Products
- Inventory
- Stock
- Stock movements
"""

from datetime import datetime

from database import SessionLocal
from models import Product, StockMovement


# ==================================================
# PRODUCTS
# ==================================================

def get_all_products():
    """
    Return all products ordered alphabetically.
    """

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
    """
    Return a single product by ID.
    """

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
    """
    Create a new product.
    """

    db = SessionLocal()

    try:

        if not name or not str(name).strip():
            raise ValueError(
                "Product name is required."
            )

        product = Product(
            name=str(name).strip(),
            category=category,
            unit=unit or "Kg",
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

    Only values supplied to the function are changed.
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

            name = str(name).strip()

            if not name:
                raise ValueError(
                    "Product name cannot be empty."
                )

            product.name = name

        if category is not None:
            product.category = category

        if unit is not None:
            product.unit = unit

        if quantity is not None:

            quantity = float(quantity)

            if quantity < 0:
                raise ValueError(
                    "Stock quantity cannot be negative."
                )

            product.quantity = quantity

        if cost_price is not None:

            cost_price = float(cost_price)

            if cost_price < 0:
                raise ValueError(
                    "Cost price cannot be negative."
                )

            product.cost_price = cost_price

        if selling_price is not None:

            selling_price = float(selling_price)

            if selling_price < 0:
                raise ValueError(
                    "Selling price cannot be negative."
                )

            product.selling_price = selling_price

        db.commit()
        db.refresh(product)

        return product

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def delete_product(product_id):
    """
    Delete a product.
    """

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


# ==================================================
# INVENTORY
# ==================================================

def get_inventory():
    """
    Return all products currently held in inventory.
    """

    return get_all_products()


def get_total_stock():
    """
    Return total stock quantity across all products.
    """

    db = SessionLocal()

    try:

        total = (
            db.query(Product.quantity)
            .all()
        )

        return sum(
            float(row[0] or 0)
            for row in total
        )

    finally:
        db.close()


# ==================================================
# STOCK ADJUSTMENT
# ==================================================

def adjust_stock(
    product_id,
    quantity,
    movement_type,
    reference=None,
):
    """
    Adjust product stock and create a stock movement.

    Positive quantity increases stock.
    Negative quantity decreases stock.
    """

    db = SessionLocal()

    try:

        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )

        if not product:
            raise ValueError(
                "Product not found."
            )

        quantity = float(quantity)

        new_quantity = (
            float(product.quantity or 0)
            + quantity
        )

        if new_quantity < 0:
            raise ValueError(
                "Insufficient stock."
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
    """
    Add stock to a product.
    """

    if float(quantity) <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    return adjust_stock(
        product_id=product_id,
        quantity=float(quantity),
        movement_type="IN",
        reference=reference,
    )


def remove_stock(
    product_id,
    quantity,
    reference=None,
):
    """
    Remove stock from a product.
    """

    if float(quantity) <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    return adjust_stock(
        product_id=product_id,
        quantity=-float(quantity),
        movement_type="OUT",
        reference=reference,
    )


# ==================================================
# STOCK MOVEMENTS
# ==================================================

def get_stock_movements(
    product_id=None,
):
    """
    Return stock movements.

    If product_id is supplied, only movements for that
    product are returned.
    """

    db = SessionLocal()

    try:

        query = (
            db.query(StockMovement)
            .order_by(
                StockMovement.created_at.desc()
            )
        )

        if product_id is not None:
            query = query.filter(
                StockMovement.product_id
                == product_id
            )

        return query.all()

    finally:
        db.close()