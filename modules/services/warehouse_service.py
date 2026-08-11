"""
Esan ERP Warehouse Service
Nile Harvest Foods Ltd.

Enterprise Milling & Packaging Management System

Functions:
- Product management
- Warehouse management
- Inventory management
- Stock in
- Stock out
- Stock adjustments
- Stock movement history
- Low stock reporting
"""

from datetime import datetime

from sqlalchemy.orm import Session

from database import SessionLocal
from models import Product, Warehouse, StockMovement


# ============================================================
# PRODUCT MANAGEMENT
# ============================================================

def get_all_products():
    """Return all products ordered by name."""

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
    """Get a single product by ID."""

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

    if not name or not name.strip():
        raise ValueError("Product name is required.")

    if quantity < 0:
        raise ValueError("Opening quantity cannot be negative.")

    if cost_price < 0:
        raise ValueError("Cost price cannot be negative.")

    if selling_price < 0:
        raise ValueError("Selling price cannot be negative.")

    db = SessionLocal()

    try:
        existing = (
            db.query(Product)
            .filter(Product.name == name.strip())
            .first()
        )

        if existing:
            raise ValueError(
                f"Product '{name.strip()}' already exists."
            )

        product = Product(
            name=name.strip(),
            category=category,
            unit=unit or "Kg",
            quantity=float(quantity),
            cost_price=float(cost_price),
            selling_price=float(selling_price),
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
    cost_price=None,
    selling_price=None,
):
    """Update product information without directly changing stock."""

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
            if not name.strip():
                raise ValueError("Product name cannot be empty.")

            duplicate = (
                db.query(Product)
                .filter(
                    Product.name == name.strip(),
                    Product.id != product_id,
                )
                .first()
            )

            if duplicate:
                raise ValueError(
                    f"Product '{name.strip()}' already exists."
                )

            product.name = name.strip()

        if category is not None:
            product.category = category

        if unit is not None:
            product.unit = unit

        if cost_price is not None:
            if cost_price < 0:
                raise ValueError(
                    "Cost price cannot be negative."
                )

            product.cost_price = float(cost_price)

        if selling_price is not None:
            if selling_price < 0:
                raise ValueError(
                    "Selling price cannot be negative."
                )

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
    """
    Delete a product.

    Products with stock movements are protected from deletion
    to preserve inventory history.
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

        movement_count = (
            db.query(StockMovement)
            .filter(
                StockMovement.product_id == product_id
            )
            .count()
        )

        if movement_count > 0:
            raise ValueError(
                "This product has stock movement history "
                "and cannot be deleted. "
                "Use it as an inactive/archive record instead."
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
# PRODUCT SEARCH
# ============================================================

def search_products(search_term):
    """Search products by name or category."""

    db = SessionLocal()

    try:
        query = db.query(Product)

        if search_term:
            search = f"%{search_term.strip()}%"

            query = query.filter(
                (Product.name.ilike(search))
                | (Product.category.ilike(search))
            )

        return query.order_by(Product.name.asc()).all()

    finally:
        db.close()


# ============================================================
# WAREHOUSE MANAGEMENT
# ============================================================

def get_all_warehouses():
    """Return all warehouses."""

    db = SessionLocal()

    try:
        return (
            db.query(Warehouse)
            .order_by(Warehouse.name.asc())
            .all()
        )

    finally:
        db.close()


def get_warehouse(warehouse_id):
    """Get a warehouse by ID."""

    db = SessionLocal()

    try:
        return (
            db.query(Warehouse)
            .filter(Warehouse.id == warehouse_id)
            .first()
        )

    finally:
        db.close()


def create_warehouse(
    name,
    location=None,
    capacity=0,
):
    """Create a new warehouse."""

    if not name or not name.strip():
        raise ValueError("Warehouse name is required.")

    if capacity is not None and capacity < 0:
        raise ValueError(
            "Warehouse capacity cannot be negative."
        )

    db = SessionLocal()

    try:
        existing = (
            db.query(Warehouse)
            .filter(Warehouse.name == name.strip())
            .first()
        )

        if existing:
            raise ValueError(
                f"Warehouse '{name.strip()}' already exists."
            )

        warehouse = Warehouse(
            name=name.strip(),
            location=location,
            capacity=float(capacity or 0),
            created_at=datetime.utcnow(),
        )

        db.add(warehouse)
        db.commit()
        db.refresh(warehouse)

        return warehouse

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_warehouse(
    warehouse_id,
    name=None,
    location=None,
    capacity=None,
):
    """Update warehouse information."""

    db = SessionLocal()

    try:
        warehouse = (
            db.query(Warehouse)
            .filter(Warehouse.id == warehouse_id)
            .first()
        )

        if not warehouse:
            return None

        if name is not None:
            if not name.strip():
                raise ValueError(
                    "Warehouse name cannot be empty."
                )

            duplicate = (
                db.query(Warehouse)
                .filter(
                    Warehouse.name == name.strip(),
                    Warehouse.id != warehouse_id,
                )
                .first()
            )

            if duplicate:
                raise ValueError(
                    f"Warehouse '{name.strip()}' already exists."
                )

            warehouse.name = name.strip()

        if location is not None:
            warehouse.location = location

        if capacity is not None:
            if capacity < 0:
                raise ValueError(
                    "Warehouse capacity cannot be negative."
                )

            warehouse.capacity = float(capacity)

        db.commit()
        db.refresh(warehouse)

        return warehouse

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def delete_warehouse(warehouse_id):
    """Delete a warehouse."""

    db = SessionLocal()

    try:
        warehouse = (
            db.query(Warehouse)
            .filter(Warehouse.id == warehouse_id)
            .first()
        )

        if not warehouse:
            return False

        db.delete(warehouse)
        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# STOCK IN
# ============================================================

def stock_in(
    product_id,
    quantity,
    reference=None,
):
    """
    Add stock to a product.

    Creates a StockMovement record and updates Product.quantity.
    """

    if quantity <= 0:
        raise ValueError(
            "Stock-in quantity must be greater than zero."
        )

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

        product.quantity = (
            float(product.quantity or 0)
            + float(quantity)
        )

        movement = StockMovement(
            product_id=product.id,
            movement_type="Stock In",
            quantity=float(quantity),
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


# ============================================================
# STOCK OUT
# ============================================================

def stock_out(
    product_id,
    quantity,
    reference=None,
):
    """
    Remove stock from a product.

    Prevents stock from becoming negative.
    """

    if quantity <= 0:
        raise ValueError(
            "Stock-out quantity must be greater than zero."
        )

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

        current_stock = float(
            product.quantity or 0
        )

        if quantity > current_stock:
            raise ValueError(
                f"Insufficient stock. "
                f"Available: {current_stock:,.2f} "
                f"{product.unit or 'units'}."
            )

        product.quantity = (
            current_stock - float(quantity)
        )

        movement = StockMovement(
            product_id=product.id,
            movement_type="Stock Out",
            quantity=float(quantity),
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


# ============================================================
# STOCK ADJUSTMENT
# ============================================================

def adjust_stock(
    product_id,
    new_quantity,
    reference=None,
):
    """
    Set the product's stock to an exact quantity.

    The difference between old and new stock is recorded
    as an Adjustment movement.
    """

    if new_quantity < 0:
        raise ValueError(
            "Adjusted stock cannot be negative."
        )

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

        old_quantity = float(
            product.quantity or 0
        )

        new_quantity = float(new_quantity)

        difference = new_quantity - old_quantity

        product.quantity = new_quantity

        movement = StockMovement(
            product_id=product.id,
            movement_type="Adjustment",
            quantity=difference,
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


# ============================================================
# STOCK MOVEMENTS
# ============================================================

def get_stock_movements(
    product_id=None,
    movement_type=None,
):
    """
    Return stock movement history.

    Optional filters:
    - product_id
    - movement_type
    """

    db = SessionLocal()

    try:
        query = db.query(StockMovement)

        if product_id is not None:
            query = query.filter(
                StockMovement.product_id == product_id
            )

        if movement_type:
            query = query.filter(
                StockMovement.movement_type
                == movement_type
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


# ============================================================
# LOW STOCK
# ============================================================

def get_low_stock_products(
    minimum_quantity=10,
):
    """Return products at or below the minimum stock level."""

    db = SessionLocal()

    try:
        return (
            db.query(Product)
            .filter(
                Product.quantity <= minimum_quantity
            )
            .order_by(Product.quantity.asc())
            .all()
        )

    finally:
        db.close()


# ============================================================
# INVENTORY SUMMARY
# ============================================================

def get_inventory_summary():
    """
    Return basic inventory KPIs.
    """

    db = SessionLocal()

    try:
        products = db.query(Product).all()

        total_products = len(products)

        total_stock = sum(
            float(product.quantity or 0)
            for product in products
        )

        total_inventory_value = sum(
            float(product.quantity or 0)
            * float(product.cost_price or 0)
            for product in products
        )

        return {
            "total_products": total_products,
            "total_stock": total_stock,
            "total_inventory_value": total_inventory_value,
        }

    finally:
        db.close()


# ============================================================
# STOCK MOVEMENT SUMMARY
# ============================================================

def get_stock_movement_summary():
    """
    Return total quantities for stock-in, stock-out,
    and adjustments.
    """

    db = SessionLocal()

    try:
        movements = (
            db.query(StockMovement)
            .all()
        )

        stock_in_total = 0.0
        stock_out_total = 0.0
        adjustment_total = 0.0

        for movement in movements:

            quantity = float(
                movement.quantity or 0
            )

            movement_type = (
                movement.movement_type or ""
            ).lower()

            if movement_type == "stock in":
                stock_in_total += quantity

            elif movement_type == "stock out":
                stock_out_total += quantity

            elif movement_type == "adjustment":
                adjustment_total += quantity

        return {
            "stock_in": stock_in_total,
            "stock_out": stock_out_total,
            "adjustments": adjustment_total,
        }

    finally:
        db.close()