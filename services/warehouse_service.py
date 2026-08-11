"""
Esan ERP Warehouse Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Functions:
- Products
- Inventory
- Stock movements
- Add products
- Edit products
- Delete products
- Stock adjustments
"""

from datetime import datetime

from database import SessionLocal
from models import Product, StockMovement


# ==================================================
# PRODUCTS
# ==================================================

def get_all_products():

    db = SessionLocal()

    try:

        return (
            db.query(Product)
            .order_by(Product.name)
            .all()
        )

    finally:

        db.close()


def get_product(product_id):

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

    db = SessionLocal()

    try:

        product = Product(
            name=name,
            category=category,
            unit=unit,
            quantity=quantity,
            cost_price=cost_price,
            selling_price=selling_price,
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
            product.name = name

        if category is not None:
            product.category = category

        if unit is not None:
            product.unit = unit

        if quantity is not None:
            product.quantity = quantity

        if cost_price is not None:
            product.cost_price = cost_price

        if selling_price is not None:
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

    db = SessionLocal()

    try:

        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )

        if not product:

            return False

        db.query(StockMovement).filter(
            StockMovement.product_id == product_id
        ).delete(
            synchronize_session=False
        )

        db.delete(product)

        db.commit()

        return True

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


# ==================================================
# STOCK
# ==================================================

def adjust_stock(
    product_id,
    quantity,
    movement_type,
    reference=None,
):

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

        if quantity <= 0:

            raise ValueError(
                "Quantity must be greater than zero."
            )

        movement_type = movement_type.strip().lower()

        if movement_type in (
            "in",
            "stock in",
            "receipt",
            "received",
            "purchase",
        ):

            product.quantity += quantity

            movement_label = "IN"

        elif movement_type in (
            "out",
            "stock out",
            "issue",
            "issued",
            "sale",
        ):

            if product.quantity < quantity:

                raise ValueError(
                    "Insufficient stock."
                )

            product.quantity -= quantity

            movement_label = "OUT"

        else:

            raise ValueError(
                "Movement type must be IN or OUT."
            )

        movement = StockMovement(
            product_id=product.id,
            movement_type=movement_label,
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

    db = SessionLocal()

    try:

        query = db.query(
            StockMovement
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


# ==================================================
# INVENTORY SUMMARY
# ==================================================

def get_inventory_summary():

    db = SessionLocal()

    try:

        products = (
            db.query(Product)
            .order_by(Product.name)
            .all()
        )

        total_products = len(products)

        total_stock = sum(
            product.quantity or 0
            for product in products
        )

        total_cost_value = sum(
            (product.quantity or 0)
            * (product.cost_price or 0)
            for product in products
        )

        total_sales_value = sum(
            (product.quantity or 0)
            * (product.selling_price or 0)
            for product in products
        )

        return {
            "total_products": total_products,
            "total_stock": total_stock,
            "total_cost_value": total_cost_value,
            "total_sales_value": total_sales_value,
        }

    finally:

        db.close()